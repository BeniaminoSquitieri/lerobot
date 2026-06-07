#!/usr/bin/env python

"""@file server.py
@brief ROS2 service server for the Python execution layer.

@details
This module is the runtime boundary between the C++ BehaviorTree.CPP process,
the Python robot execution process, and external scene verifiers. The C++ side
never imports policy or robot code directly: it sends a `RunNamedCommand`
request, waits for this server to finish the command, and then polls the
VLM check state managed here. VLM/manual verifiers use topics only.

Flow role:
1. Wait for the C++ BT to send a named command.
2. Dispatch that command to a learned policy skill or a VLM/manual gate.
3. Return the result to the BT so the tree can continue or retry.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from pprint import pformat
from typing import TYPE_CHECKING, Any

import rclpy
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from lerobot.common.control_utils import is_headless
from lerobot.configs import parser
from lerobot.processor.converters import (
    observation_to_transition,
    robot_action_observation_to_transition,
    transition_to_observation,
    transition_to_robot_action,
)
from lerobot.utils.utils import init_logging, log_say
from lerobot.utils.visualization_utils import init_rerun as init_rerun_viz

from .bt_interface_paths import load_bt_services, load_query_object_pose_service
from .config import SkillCommandServerConfig
from .executor import CommandResult, SkillRunner
from .perception.camera_publisher import start_camera_publisher
from .perception.spatial_prior_gate import ObservedPose, SpatialPriorGate, parse_object_pose_json
from .processor_factory import build_robot_processor_pipeline
from .vlm.operator_console import print_vlm_request_banner, print_vlm_result_banner
from .vlm.protocol import vlm_message_from_payload, vlm_status_from_payload
from .vlm.verification import (
    VLM_RUNNING,
    VLM_SUCCESS,
    VLM_UNKNOWN,
    VLM_WAITING_STATUSES,
    SceneVerdictStore,
)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "make_sandwich_executor.yaml"
"""Default draccus YAML loaded when the entry point is started without flags."""

if TYPE_CHECKING:
    from lerobot.processor import RobotProcessorPipeline
    from lerobot.robots.custom_manipulator.custom_manipulator import CustomManipulator

VLM_GATE_KIND = "vlm_gate_pending"
"""Command kind that acknowledges a gate but leaves the VLM check running."""

_legacy_vlm_service_warned = False


def _start_camera_publisher(
    *,
    robot: CustomManipulator,
    topic_map: dict[str, str],
    depth_topic_map: dict[str, str] | None = None,
    camera_info_topic_map: dict[str, str] | None = None,
    frame_id_map: dict[str, str] | None = None,
    static_tf_map: Mapping[str, Mapping[str, Any]] | None = None,
    fps: float,
    jpeg_quality: int,
    node: Node,
):
    """@brief Backwards-compatible wrapper around `camera_publisher.start_camera_publisher`."""
    return start_camera_publisher(
        robot=robot,
        topic_map=topic_map,
        depth_topic_map=depth_topic_map,
        camera_info_topic_map=camera_info_topic_map,
        frame_id_map=frame_id_map,
        static_tf_map=static_tf_map,
        fps=fps,
        jpeg_quality=jpeg_quality,
        node=node,
    )


class SkillCommandServer(Node):
    """@brief ROS2 node that executes BT commands and stores VLM check state.

    The node owns three services and two verifier-facing topics:
    - `RunNamedCommand`: command execution requested by BT XML leaf nodes.
    - `VLM state service`: polling endpoint used by merged `DoSkill`/`AwaitScene` leaves.
    - `legacy VLM result service`: legacy endpoint kept for compatibility.
    - `vlm_request_topic`: published when a scene verdict is needed.
    - `vlm_result_topic`: consumed from manual/VLM results.
    """

    def __init__(
        self,
        cfg: SkillCommandServerConfig,
        robot: CustomManipulator,
        skill_runner: SkillRunner,
        robot_action_processor: RobotProcessorPipeline,
        robot_observation_processor: RobotProcessorPipeline,
        scene_verdict_store: SceneVerdictStore,
    ) -> None:
        """@brief Construct the service node and register every ROS2 service.

        @param cfg Runtime configuration loaded from YAML.
        @param robot Connected robot object used by the executor backend.
        @param skill_runner Object that actually runs learned skills.
        @param robot_action_processor Pipeline that converts policy actions.
        @param robot_observation_processor Pipeline that converts observations.
        @param scene_verdict_store In-memory state machine for skill attempts.
        """
        super().__init__("lerobot_bt_skill_server")
        self.cfg = cfg
        self.robot = robot
        self.skill_runner = skill_runner
        self.robot_action_processor = robot_action_processor
        self.robot_observation_processor = robot_observation_processor
        self.scene_verdict_store = scene_verdict_store
        self._command_callback_group = MutuallyExclusiveCallbackGroup()
        self._vlm_callback_group = ReentrantCallbackGroup()
        self._auto_shutdown_success_names = set(cfg.auto_shutdown_success_names)

        # ROS2 entrypoints used by the BT runtime and verifier-facing topics.
        bt_command_service_type, vlm_state_service_type, legacy_vlm_result_service_type = load_bt_services()
        from std_msgs.msg import String  # type: ignore

        self._bt_command_server = self.create_service(
            bt_command_service_type,
            cfg.bt_command_service,
            self._handle_request,
            callback_group=self._command_callback_group,
        )
        self._vlm_state_server = self.create_service(
            vlm_state_service_type,
            cfg.vlm_state_service,
            self._handle_get_vlm_state,
            callback_group=self._vlm_callback_group,
        )
        self._legacy_vlm_result_server = self.create_service(
            legacy_vlm_result_service_type,
            cfg.legacy_vlm_result_service,
            self._handle_legacy_vlm_result,
            callback_group=self._vlm_callback_group,
        )
        self._vlm_request_publisher = self.create_publisher(
            String,
            cfg.vlm_request_topic,
            10,
        )
        self._vlm_result_subscription = self.create_subscription(
            String,
            cfg.vlm_result_topic,
            self._handle_vlm_result_topic,
            10,
            callback_group=self._vlm_callback_group,
        )
        self._shutdown_requested = False
        self._shutdown_reason = ""
        self._shutdown_lock = threading.Lock()
        self.get_logger().info(
            "Serving BT commands on "
            f"'{cfg.bt_command_service}', VLM state service on "
            f"'{cfg.vlm_state_service}', legacy VLM result service on "
            f"'{cfg.legacy_vlm_result_service}', VLM requests on "
            f"'{cfg.vlm_request_topic}', and VLM results from "
            f"'{cfg.vlm_result_topic}'."
        )

        # Deterministic spatial-prior OOD gate. Inert when mode == "off".
        self._spatial_prior_gate = SpatialPriorGate(
            cfg.spatial_prior_gate,
            package_dir=Path(__file__).resolve().parent,
            logger=self.get_logger(),
        )
        self._query_pose_client = None
        self._query_pose_service_type = None
        if self._spatial_prior_gate.enabled:
            try:
                self._query_pose_service_type = load_query_object_pose_service()
                self._query_pose_client = self.create_client(
                    self._query_pose_service_type,
                    cfg.spatial_prior_gate.query_pose_service,
                    callback_group=self._vlm_callback_group,
                )
                self.get_logger().info(
                    "spatial_prior_gate: mode="
                    f"{cfg.spatial_prior_gate.mode}, querying object poses on "
                    f"'{cfg.spatial_prior_gate.query_pose_service}'."
                )
            except Exception as exc:  # noqa: BLE001
                # A missing perception service must not crash the BT server: the
                # gate degrades to ABSTAIN (it cannot fetch poses) and logs why.
                self.get_logger().warning(
                    f"spatial_prior_gate: could not create QueryObjectPose client: {exc}. "
                    "The gate will ABSTAIN until the perception service is available."
                )

    def _query_object_pose(self, object_name: str) -> ObservedPose:
        """@brief pose_provider backed by the perception QueryObjectPose service.

        Returns an ObservedPose with `error` set whenever the perception pose
        cannot be obtained, so the gate ABSTAINS rather than blocking.
        """
        client = self._query_pose_client
        if client is None or self._query_pose_service_type is None:
            return ObservedPose(error="query_pose_client_unavailable")

        timeout_s = float(self.cfg.spatial_prior_gate.query_timeout_s)
        if not client.wait_for_service(timeout_sec=timeout_s):
            return ObservedPose(error="query_pose_service_unavailable")

        request = self._query_pose_service_type.Request()
        request.object_name = object_name
        request.require_fresh = bool(self.cfg.spatial_prior_gate.require_fresh_pose)
        request.max_age_s = float(self.cfg.spatial_prior_gate.query_max_age_s)

        future = client.call_async(request)
        deadline = time.monotonic() + timeout_s
        while not future.done() and time.monotonic() < deadline:
            time.sleep(0.01)
        if not future.done():
            return ObservedPose(error="query_pose_timeout")

        response = future.result()
        if response is None:
            return ObservedPose(error="query_pose_no_response")
        if not bool(getattr(response, "success", False)):
            reason = str(getattr(response, "error_message", "") or "perception_no_pose")
            return ObservedPose(error=reason)
        return parse_object_pose_json(str(getattr(response, "pose_json", "")))

    def _handle_request(self, request, response):
        """@brief Handle one `RunNamedCommand` service request.

        @param request ROS2 request with `kind`, `name`, and `timeout_s`.
        @param response Mutable ROS2 response filled before returning.
        @return The filled ROS2 response object.

        This method deliberately separates command execution from post-skill
        scene check. A successful skill opens a VLM check attempt; the BT can
        only advance after the merged BT leaf sees that attempt resolve.
        """
        # This is the handoff point between C++ BT orchestration and Python execution.
        log_say(f"Executing {request.kind} {request.name}", self.cfg.play_sounds)

        try:
            if request.kind == "skill":
                # Deterministic spatial-prior gate runs first. In SHADOW mode it
                # only logs; in ENFORCE mode a FAIL (object out-of-distribution)
                # blocks the skill before any motion. ABSTAIN never blocks.
                gate_verdict = self._spatial_prior_gate.evaluate(request.name, self._query_object_pose)
                if self._spatial_prior_gate.should_block(gate_verdict):
                    response.success = False
                    response.status = "FAILURE"
                    response.elapsed_s = 0.0
                    response.message = (
                        f"Spatial-prior gate blocked skill '{request.name}': object "
                        f"out-of-distribution (reason={gate_verdict.reason}, "
                        f"distance={gate_verdict.distance:.3f} > "
                        f"threshold={gate_verdict.threshold:.3f}). Skill not executed."
                    )
                    self.get_logger().warning(response.message)
                    return response
                # Open a VLM check BEFORE executing the skill so the VLM can
                # monitor the scene in real-time and return SUCCESS as soon as
                # the goal is achieved, cutting the skill execution short.
                self.scene_verdict_store.register_skill_name(request.name)
                vlm_pre_attempt = self.scene_verdict_store.begin_attempt(request.name)
                self.skill_runner.begin_live_vlm_skill(
                    request.name,
                    attempt_id=vlm_pre_attempt.attempt_id,
                )
                self._publish_vlm_request(
                    vlm_pre_attempt,
                    check_period_s=float(getattr(self.cfg, "skill_vlm_check_period_s", 0.0)),
                )
                self.get_logger().info(
                    f"Pre-skill VLM check opened for '{request.name}' attempt {vlm_pre_attempt.attempt_id}."
                )
                # Real learned primitive: delegate to the robot/policy executor.
                # The executor checks _active_vlm_result and stops early if the
                # VLM reports a terminal status during execution.
                result = self.skill_runner.execute_skill(
                    skill_name=request.name,
                    robot_action_processor=self.robot_action_processor,
                    robot_observation_processor=self.robot_observation_processor,
                    timeout_override_s=request.timeout_s,
                    live_vlm_attempt_id=vlm_pre_attempt.attempt_id,
                )
            elif request.kind == VLM_GATE_KIND:
                # Human/VLM gate: open an attempt but do not resolve it.
                result = CommandResult(
                    True,
                    "SUCCESS",
                    0.0,
                    f"VLM gate '{request.name}' opened and is awaiting a VLM result.",
                )
            else:
                result = None
        except Exception as exc:  # noqa: BLE001
            if getattr(request, "kind", "") == "skill":
                self.skill_runner.clear_live_vlm_skill(request.name)
            response.success = False
            response.status = "ERROR"
            response.elapsed_s = 0.0
            response.message = f"Server exception while executing command: {exc}"
            self.get_logger().exception(response.message)
            return response

        if result is None:
            response.success = False
            response.status = "ERROR"
            response.elapsed_s = 0.0
            response.message = (
                f"Unsupported command kind '{request.kind}'. Expected one of ('skill', '{VLM_GATE_KIND}')."
            )
            self.get_logger().error(response.message)
            return response

        if request.kind in {"skill", VLM_GATE_KIND} and result.success:
            try:
                live_vlm_status = getattr(result, "vlm_status", None)
                # For skills, the VLM check was already opened before execution
                # (see pre-skill block above). Only open a new attempt for gates.
                if request.kind == VLM_GATE_KIND:
                    # Gate names do not need to exist in the real skill config.
                    self.scene_verdict_store.register_skill_name(request.name)
                    vlm_check_attempt = self.scene_verdict_store.begin_attempt(request.name)
                    # Give the human operator time to place/adjust objects
                    # before the VLM starts checking the scene. The BT polls
                    # and sees RUNNING during this wait.
                    gate_wait_s = float(getattr(self.cfg, "vlm_gate_min_wait_s", 5.0))
                    if gate_wait_s > 0:
                        self.get_logger().info(
                            f"Gate '{request.name}': waiting {gate_wait_s:.1f}s for human operator..."
                        )
                        time.sleep(gate_wait_s)
                    self._publish_vlm_request(
                        vlm_check_attempt,
                        check_period_s=float(getattr(self.cfg, "gate_vlm_check_period_s", 0.0)),
                    )
                # For skills, the pre-skill VLM check was a warm-up. After the
                # skill finishes, open a fresh attempt so the VLM sees the
                # final scene, not stale pre-skill frames. If the live verifier
                # already stopped the rollout with a terminal verdict, reuse the
                # pre-skill attempt instead of opening a brand-new attempt that
                # would immediately start re-checking a task that is already done.
                elif request.kind == "skill" and live_vlm_status:
                    vlm_check_attempt = vlm_pre_attempt
                elif request.kind == "skill":
                    vlm_check_attempt = self.scene_verdict_store.begin_attempt(request.name)
                    self._publish_vlm_request(
                        vlm_check_attempt,
                        check_period_s=float(getattr(self.cfg, "skill_vlm_check_period_s", 0.0)),
                    )
                if live_vlm_status:
                    self.scene_verdict_store.report(
                        skill_name=request.name,
                        attempt_id=vlm_check_attempt.attempt_id,
                        status=live_vlm_status,
                        message=getattr(result, "vlm_message", "") or result.message,
                    )
                    result.message = (
                        f"{result.message} "
                        f"VLM check attempt {vlm_check_attempt.attempt_id} was resolved as "
                        f"{live_vlm_status} from the live verifier result."
                    )
                else:
                    vlm_request_topic = getattr(
                        self.cfg,
                        "vlm_request_topic",
                        self.cfg.vlm_state_service,
                    )
                    result.message = (
                        f"{result.message} "
                        f"VLM check attempt {vlm_check_attempt.attempt_id} is now running on "
                        f"'{vlm_request_topic}'."
                    )
            except Exception as exc:  # noqa: BLE001
                response.success = False
                response.status = "ERROR"
                response.elapsed_s = float(result.elapsed_s)
                response.message = f"Could not open VLM check for command '{request.name}': {exc}"
                self.get_logger().error(response.message)
                return response

        response.success = bool(result.success)
        response.status = result.status
        response.elapsed_s = float(result.elapsed_s)
        response.message = result.message
        if result.success:
            self.get_logger().info(result.message)
        else:
            self.get_logger().error(result.message)
        return response

    def _handle_get_vlm_state(self, request, response):
        """@brief Return the latest VLM check attempt for one skill.

        @param request ROS2 request containing `skill_name`.
        @param response Mutable ROS2 response with attempt metadata.
        @return The filled ROS2 response object.
        """
        try:
            snapshot = self.scene_verdict_store.get_latest(request.skill_name)
        except ValueError as exc:
            response.has_attempt = False
            response.attempt_id = 0
            response.status = VLM_UNKNOWN
            response.message = str(exc)
            self.get_logger().error(response.message)
            return response

        if snapshot is None:
            response.has_attempt = False
            response.attempt_id = 0
            response.status = VLM_UNKNOWN
            response.message = f"No completed attempt has been recorded yet for skill '{request.skill_name}'."
            self.get_logger().warning(response.message)
            return response

        response.has_attempt = True
        response.attempt_id = int(snapshot.attempt_id)
        response.status = snapshot.status
        response.message = snapshot.message
        if snapshot.status in VLM_WAITING_STATUSES:
            self.get_logger().debug(
                f"VLM check for skill '{snapshot.skill_name}' attempt {snapshot.attempt_id} "
                f"is {snapshot.status}."
            )
        elif self._should_auto_shutdown_after_vlm_success(snapshot.skill_name, snapshot.status):
            self._request_shutdown(
                "Final BT leaf succeeded "
                f"('{snapshot.skill_name}' attempt {snapshot.attempt_id}); shutting down server."
            )
        return response

    def _handle_legacy_vlm_result(self, request, response):
        """@brief Accept a verifier verdict for an active skill attempt.

        @param request ROS2 request containing skill name, attempt id, status,
            and message.
        @param response Mutable ROS2 response that reports whether the verdict
            was applied.
        @return The filled ROS2 response object.
        """
        global _legacy_vlm_service_warned
        if not _legacy_vlm_service_warned:
            self.get_logger().warning("legacy_vlm_result_service is deprecated and kept for compatibility.")
            _legacy_vlm_service_warned = True
        if self._try_report_active_skill_vlm_result(
            skill_name=request.skill_name,
            attempt_id=int(request.attempt_id),
            status=request.status,
            message=request.message,
        ):
            response.accepted = True
            response.applied_attempt_id = 0
            response.message = (
                f"Accepted VLM status {request.status} as live stop for active skill '{request.skill_name}'."
            )
            return response

        try:
            update = self.scene_verdict_store.report(
                skill_name=request.skill_name,
                attempt_id=int(request.attempt_id),
                status=request.status,
                message=request.message,
            )
        except ValueError as exc:
            response.accepted = False
            response.applied_attempt_id = 0
            response.message = str(exc)
            self.get_logger().error(response.message)
            return response

        response.accepted = bool(update.accepted)
        response.applied_attempt_id = 0 if update.snapshot is None else int(update.snapshot.attempt_id)
        response.message = update.message
        if update.accepted:
            self.get_logger().info(response.message)
        else:
            self.get_logger().warning(response.message)
        return response

    def _try_report_active_skill_vlm_result(
        self,
        *,
        skill_name: str,
        attempt_id: int,
        status: str,
        message: str,
    ) -> bool:
        """@brief Offer a verifier result to the currently running skill first."""
        report_active = getattr(self.skill_runner, "report_active_vlm_result", None)
        if report_active is None:
            return False

        accepted = bool(
            report_active(
                skill_name=skill_name,
                attempt_id=attempt_id,
                status=status,
                message=message,
            )
        )
        if accepted:
            self.get_logger().info(
                f"Accepted VLM status {status} as live stop for active skill '{skill_name}'."
            )
        return accepted

    def _publish_vlm_request(self, snapshot, *, check_period_s=None) -> None:
        """@brief Publish a topic event asking a VLM/manual verifier for a verdict.

        @param snapshot The VLM check attempt snapshot to advertise.
        @param check_period_s Optional re-check cadence hint (seconds) the VLM
            verifier should honor while the status stays non-final. Used to make
            robot-skill checks re-evaluate the scene much faster than human
            gates. ``None`` lets the verifier keep its own default cadence.
        """
        from std_msgs.msg import String  # type: ignore

        # Resolve the human-readable verification description for this request.
        # Prefer explicit VLM verification prompts from executor YAML because
        # BC skill `.task` text often describes the action ("pick the toast")
        # rather than the visual success condition ("toast is on red plate").
        # Fall back to PrimitiveSkillConfig.task only when no VLM-specific
        # override exists for this skill/gate name.
        skill_cfg = self.skill_runner.skill_configs.get(snapshot.skill_name)
        task_desc = self.cfg.vlm_gate_tasks.get(snapshot.skill_name, "").strip()
        if not task_desc and skill_cfg is not None and getattr(skill_cfg, "task", None):
            task_desc = skill_cfg.task.strip()

        payload = {
            "event": "vlm_check_requested",
            "skill_name": snapshot.skill_name,
            "attempt_id": int(snapshot.attempt_id),
            "status": VLM_RUNNING,
            "message": snapshot.message,
            "task": task_desc,
            "allowed_statuses": [
                "RUNNING",
                "SUCCESS",
                "FAILURE",
            ],
            "allowed_next_actions": [
                "CONTINUE",
                "RETRY_SKILL",
                "WAIT",
            ],
        }
        if check_period_s is not None:
            payload["check_period_s"] = float(check_period_s)
        msg = String()
        msg.data = json.dumps(payload, sort_keys=True)
        self._vlm_request_publisher.publish(msg)
        self.get_logger().info(
            f"event=vlm_request_published skill={snapshot.skill_name!r} "
            f"attempt={snapshot.attempt_id} status={VLM_RUNNING} "
            f"topic={self.cfg.vlm_request_topic!r} task={task_desc!r}"
        )
        print_vlm_request_banner(
            skill_name=snapshot.skill_name,
            attempt_id=int(snapshot.attempt_id),
            task_desc=task_desc,
        )

    def _handle_vlm_result_topic(self, msg) -> None:
        """@brief Apply one JSON verifier verdict received from a ROS2 topic."""
        try:
            payload = json.loads(msg.data)
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error(
                f"event=vlm_result_received status=invalid_json "
                f"topic={self.cfg.vlm_result_topic!r} error={exc}: '{msg.data}'"
            )
            return
        if not isinstance(payload, dict):
            self.get_logger().error(
                f"event=vlm_result_received status=invalid_payload "
                f"topic={self.cfg.vlm_result_topic!r} error=payload must be a JSON object"
            )
            return

        try:
            skill_name = str(payload.get("skill_name", ""))
            status = vlm_status_from_payload(payload)
            attempt_id = int(payload.get("attempt_id", 0))
            message = vlm_message_from_payload(payload, status=status)
            if self._try_report_active_skill_vlm_result(
                skill_name=skill_name,
                attempt_id=attempt_id,
                status=status,
                message=message,
            ):
                return
            update = self.scene_verdict_store.report(
                skill_name=skill_name,
                attempt_id=attempt_id,
                status=status,
                message=message,
            )
        except (TypeError, ValueError) as exc:
            self.get_logger().error(
                f"event=vlm_result_received status=rejected topic={self.cfg.vlm_result_topic!r} error={exc}"
            )
            return

        if update.accepted:
            self.get_logger().info(update.message)
        else:
            self.get_logger().warning(update.message)

        print_vlm_result_banner(skill_name=skill_name, status=status, message=message)

    def _should_auto_shutdown_after_vlm_success(self, skill_name: str, status: str) -> bool:
        """@brief True when the BT has reached a configured terminal leaf."""
        if status != VLM_SUCCESS:
            return False
        if self._auto_shutdown_success_names:
            return skill_name in self._auto_shutdown_success_names
        return skill_name.endswith(".task_complete")

    def _request_shutdown(self, reason: str) -> None:
        """@brief Record a shutdown request exactly once and log the trigger."""
        with self._shutdown_lock:
            if self._shutdown_requested:
                return
            self._shutdown_requested = True
            self._shutdown_reason = reason
        self.get_logger().info(reason)

    def consume_shutdown_request(self) -> str | None:
        """@brief Return the pending shutdown reason, if any."""
        with self._shutdown_lock:
            if not self._shutdown_requested:
                return None
            return self._shutdown_reason


@parser.wrap(config_path=DEFAULT_CONFIG_PATH)
def run(cfg: SkillCommandServerConfig) -> None:
    """@brief Start the real ROS2 skill command server.

    @param cfg Parsed draccus config. When invoked from the entry point this is
        loaded from `make_sandwich_executor.yaml` unless another config is passed.

    Startup order matters: the robot and processors are created before the node
    spins so the BT never reaches a half-initialized command server.
    """
    init_logging()
    logging.info(pformat(asdict(cfg)))

    depth_enabled_cameras = [
        name
        for name, camera_cfg in getattr(cfg.robot, "cameras", {}).items()
        if bool(getattr(camera_cfg, "use_depth", False))
    ]
    if depth_enabled_cameras and not cfg.camera_static_tf_map:
        logging.warning(
            "Depth-enabled cameras are configured (%s) but camera_static_tf_map is empty. "
            "Perception poses will remain in camera frame and robot-frame pose queries will be "
            "rejected as tf_unavailable until calibrated hand-eye transforms are supplied.",
            ", ".join(sorted(depth_enabled_cameras)),
        )

    logging.info("Initializing ROS2 client library.")
    if not rclpy.ok():
        rclpy.init()
    logging.info("ROS2 client library is ready.")

    if cfg.display_data and not is_headless():
        logging.info("Initializing Rerun visualization.")
        init_rerun_viz(session_name="lerobot_bt_skill_server")
        logging.info("Rerun visualization is ready.")

    logging.info("Constructing CustomManipulator.")
    from lerobot.robots.custom_manipulator.custom_manipulator import CustomManipulator

    robot = CustomManipulator(cfg.robot)
    logging.info("CustomManipulator constructed.")

    logging.info("Building robot action processor.")
    robot_action_processor = build_robot_processor_pipeline(
        cfg.robot_action_processor,
        to_transition=robot_action_observation_to_transition,
        to_output=transition_to_robot_action,
    )
    logging.info("Robot action processor ready.")

    logging.info("Building robot observation processor.")
    robot_observation_processor = build_robot_processor_pipeline(
        cfg.robot_observation_processor,
        to_transition=observation_to_transition,
        to_output=transition_to_observation,
    )
    logging.info("Robot observation processor ready.")

    logging.info("Constructing skill command executor.")
    skill_runner = SkillRunner(cfg=cfg, robot=robot)
    logging.info("Skill command executor ready.")
    scene_verdict_store = SceneVerdictStore(
        known_skill_names=set(skill_runner.skill_configs),
        vlm_timeout_s=cfg.vlm_timeout_s,
    )
    logging.info("VLM check registry ready.")

    logging.info("Creating ROS2 skill command service node.")
    server_node = SkillCommandServer(
        cfg=cfg,
        robot=robot,
        skill_runner=skill_runner,
        robot_action_processor=robot_action_processor,
        robot_observation_processor=robot_observation_processor,
        scene_verdict_store=scene_verdict_store,
    )
    logging.info("ROS2 skill command service node is ready.")

    ros_executor = MultiThreadedExecutor(num_threads=4)
    ros_executor.add_node(server_node)
    try:
        # Robot-facing startup happens before we start accepting BT commands.
        logging.info("Connecting robot.")
        robot.connect()
        logging.info("Robot connected.")
        if cfg.reset_robot_on_startup:
            logging.info("Resetting robot on startup.")
            robot.reset()
            logging.info("Robot startup reset complete.")
        logging.info("Spinning skill command server.")

        # Start background camera publisher so the VLM can subscribe to live
        # frames without opening the RealSense devices a second time.
        _camera_pub_stop = None
        if cfg.camera_publish_map and cfg.camera_publish_fps > 0:
            _camera_pub_stop = _start_camera_publisher(
                robot=robot,
                topic_map=cfg.camera_publish_map,
                depth_topic_map=cfg.camera_depth_publish_map,
                camera_info_topic_map=cfg.camera_info_publish_map,
                frame_id_map=cfg.camera_frame_id_map,
                static_tf_map=cfg.camera_static_tf_map,
                fps=cfg.camera_publish_fps,
                jpeg_quality=cfg.camera_publish_jpeg_quality,
                node=server_node,
            )
            logging.info(
                "Camera publisher started: %s at %.1f FPS.",
                sorted(cfg.camera_publish_map.values()),
                cfg.camera_publish_fps,
            )

        try:
            while rclpy.ok():
                ros_executor.spin_once(timeout_sec=0.2)
                shutdown_reason = server_node.consume_shutdown_request()
                if shutdown_reason:
                    logging.info("Stopping skill command server: %s", shutdown_reason)
                    break
        finally:
            if _camera_pub_stop is not None:
                _camera_pub_stop()
    finally:
        try:
            ros_executor.shutdown()
        except Exception:  # noqa: BLE001
            logging.exception("Best-effort ROS2 executor shutdown failed.")
        try:
            robot.disconnect()
        except Exception:  # noqa: BLE001
            logging.exception("Best-effort robot disconnect failed during server shutdown.")
        try:
            server_node.destroy_node()
        except Exception:  # noqa: BLE001
            logging.exception("Best-effort ROS2 node destruction failed during server shutdown.")
        if rclpy.ok():
            rclpy.shutdown()


def main() -> None:
    """@brief Console entry point used by `lerobot-bt-skill-server`."""
    run()


if __name__ == "__main__":
    main()
