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
2. Dispatch that command to a learned ACT skill or a VLM/manual gate.
3. Return the result to the BT so the tree can continue or retry.
"""

import importlib
import json
import logging
import os
import sys
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
from lerobot.processor import ProcessorStepRegistry, RobotProcessorPipeline
from lerobot.processor.converters import (
    observation_to_transition,
    robot_action_observation_to_transition,
    transition_to_observation,
    transition_to_robot_action,
)
from lerobot.utils.utils import init_logging, log_say
from lerobot.utils.visualization_utils import init_rerun as init_rerun_viz

from .config import SkillCommandServerConfig
from .executor import CommandResult, SkillCommandExecutor
from .verification import (
    VLM_FAILURE,
    VLM_NEEDS_MANUAL_HELP,
    VLM_PENDING,
    VLM_RUNNING,
    VLM_SUCCESS,
    VLM_UNKNOWN,
    VLM_WAIT_HUMAN,
    VLM_WAITING_STATUSES,
    VlmCheckRegistry,
)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "make_sandwich_executor.yaml"
"""Default draccus YAML loaded when the entry point is started without flags."""

if TYPE_CHECKING:
    from lerobot.robots.custom_manipulator.custom_manipulator import CustomManipulator

VLM_GATE_PENDING_KIND = "vlm_gate_pending"
"""Command kind that acknowledges a gate but leaves the VLM check pending."""

_NEXT_ACTION_TO_STATUS = {
    "CONTINUE": VLM_SUCCESS,
    "PROCEED": VLM_SUCCESS,
    "RETRY": VLM_FAILURE,
    "RETRY_SKILL": VLM_FAILURE,
    "WAIT": VLM_RUNNING,
    "WAIT_HUMAN": VLM_WAIT_HUMAN,
    "REQUEST_MANUAL_INTERVENTION": VLM_NEEDS_MANUAL_HELP,
    "MANUAL_INTERVENTION": VLM_NEEDS_MANUAL_HELP,
}


def _truthy_payload_value(value: Any) -> bool:
    """@brief Return true for boolean-like values coming from simple VLM topics."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def _normalize_vlm_status_token(token: str) -> str:
    """@brief Map scene-gate tokens onto the registry status vocabulary."""
    normalized = token.upper()
    if not normalized:
        return ""
    if normalized.startswith("SCENE_") and normalized.endswith("_READY"):
        return VLM_SUCCESS
    if normalized == "TASK_COMPLETE":
        return VLM_SUCCESS
    if normalized == "ANOMALY_DETECTED":
        return VLM_FAILURE
    if normalized == "HUMAN_HELP_REQUIRED":
        return VLM_NEEDS_MANUAL_HELP
    return normalized


def _vlm_status_from_payload(payload: dict[str, Any]) -> str:
    """@brief Resolve VLM status/next_action fields into the BT-facing status."""
    if _truthy_payload_value(payload.get("human_help_required", False)):
        return VLM_NEEDS_MANUAL_HELP
    if _truthy_payload_value(payload.get("anomaly_detected", False)):
        return VLM_FAILURE
    if _truthy_payload_value(payload.get("scene_ready", False)):
        return VLM_SUCCESS

    status = _normalize_vlm_status_token(str(payload.get("status", "")))
    if status:
        return status
    scene_id = _normalize_vlm_status_token(str(payload.get("scene_id", "")))
    if scene_id:
        return scene_id
    next_action = str(payload.get("next_action", "")).upper()
    if next_action in _NEXT_ACTION_TO_STATUS:
        return _NEXT_ACTION_TO_STATUS[next_action]
    return ""


def _vlm_message_from_payload(payload: dict[str, Any], *, status: str) -> str:
    """@brief Build a compact operator message from richer VLM topic fields."""
    message_parts = []
    message = str(payload.get("message", ""))
    if message:
        message_parts.append(message)
    for key in (
        "scene_id",
        "scene_ready",
        "anomaly_detected",
        "human_help_required",
        "failure_reason",
        "scene_state",
        "required_human_action",
        "next_action",
    ):
        value = payload.get(key)
        if value not in (None, ""):
            message_parts.append(f"{key}={value}")
    if not message_parts:
        message_parts.append(f"External verifier reported {status}.")
    return " | ".join(message_parts)


def _instantiate_processor_step(step_spec: Any):
    """@brief Build one configured robot/policy processor step.

    @param step_spec Either a registry name, or a mapping containing
        `registry_name`/`class` and an optional `config` dictionary.
    @return A configured processor step instance.

    The server allows processor steps to be configured without importing every
    possible class at module import time. A string uses LeRobot's processor
    registry; a mapping can either name a registry entry or import a class by
    dotted Python path.
    """
    if isinstance(step_spec, str):
        # Registry form: the YAML only stores a stable processor name.
        step_class = ProcessorStepRegistry.get(step_spec)
        return step_class()

    if isinstance(step_spec, dict):
        if "registry_name" in step_spec:
            # Explicit registry mapping, useful when a config block is needed.
            step_class = ProcessorStepRegistry.get(step_spec["registry_name"])
        elif "class" in step_spec:
            # Dynamic class path for processors that are not registered globally.
            module_path, class_name = step_spec["class"].rsplit(".", 1)
            module = importlib.import_module(module_path)
            step_class = getattr(module, class_name)
        else:
            raise ValueError(
                f"Invalid processor step config {step_spec!r}. Expected a string, or a dict with "
                f"'registry_name' or 'class'."
            )
        return step_class(**step_spec.get("config", {}))

    raise TypeError(f"Unsupported processor step spec: {step_spec!r}")


def _build_robot_processor_pipeline(
    processor_cfg: dict[str, Any],
    *,
    to_transition,
    to_output,
) -> RobotProcessorPipeline:
    """@brief Convert a YAML processor list into a LeRobot pipeline.

    @param processor_cfg Mapping with a `steps` list.
    @param to_transition Converter from robot-native objects to transition data.
    @param to_output Converter from transition data back to robot-native output.
    @return A `RobotProcessorPipeline` that wraps every configured step.
    """
    steps = [_instantiate_processor_step(step_spec) for step_spec in processor_cfg.get("steps", [])]
    return RobotProcessorPipeline(
        steps=steps,
        to_transition=to_transition,
        to_output=to_output,
    )


def _prepend_generated_interface_paths() -> None:
    """@brief Put generated ROS2 interface packages before source packages.

    The repository contains `src/lerobot_bt_interfaces`, while ROS2 generation
    creates importable Python bindings under `install/.../site-packages`. When
    the editable repo has already placed `src/` on `sys.path`, Python may see the
    source package first and miss the generated `.srv` modules. This helper adds
    the generated package directories at the front of `sys.path`.
    """
    python_dir = f"python{sys.version_info.major}.{sys.version_info.minor}"
    repo_root = Path(__file__).resolve().parents[2]
    prefixes = [Path(path) for path in os.environ.get("COLCON_PREFIX_PATH", "").split(os.pathsep) if path]
    prefixes.extend(
        [
            repo_root / "install" / "lerobot_bt_interfaces",
            repo_root / "install",
        ]
    )

    for prefix in prefixes:
        site_packages = prefix / "lib" / python_dir / "site-packages"
        if (site_packages / "lerobot_bt_interfaces" / "srv").exists():
            site_packages_str = str(site_packages)
            if site_packages_str not in sys.path:
                sys.path.insert(0, site_packages_str)


def _load_bt_services():
    """@brief Import generated LeRobot BT ROS2 service classes.

    @return `(RunNamedCommand, GetSkillVerification, ReportSkillVerification)`.
    @throws ImportError if the workspace has not been built or sourced.

    The editable repo adds `src/` to `sys.path`, which makes Python see the
    source-only ROS package as a namespace package before the generated
    interface package under `install/.../site-packages`.
    """
    _prepend_generated_interface_paths()
    for module_name in list(sys.modules):
        if module_name == "lerobot_bt_interfaces" or module_name.startswith("lerobot_bt_interfaces."):
            del sys.modules[module_name]

    try:
        from lerobot_bt_interfaces.srv import GetSkillVerification, ReportSkillVerification, RunNamedCommand

        return RunNamedCommand, GetSkillVerification, ReportSkillVerification
    except ImportError as import_error:
        raise ImportError(
            "Could not import the lerobot_bt_interfaces service bindings. "
            "Source install/local_setup.bash or rebuild lerobot_bt_interfaces."
        ) from import_error


class SkillCommandServer(Node):
    """@brief ROS2 node that executes BT commands and stores VLM check state.

    The node owns three services and two verifier-facing topics:
    - `RunNamedCommand`: command execution requested by BT XML leaf nodes.
    - `VLM state service`: polling endpoint used by `VerifySkillOutcome`.
    - `legacy VLM result service`: legacy endpoint kept for compatibility.
    - `vlm_request_topic`: published when a scene verdict is needed.
    - `vlm_result_topic`: consumed from manual/VLM results.
    """

    def __init__(
        self,
        cfg: SkillCommandServerConfig,
        robot: "CustomManipulator",
        executor_backend: SkillCommandExecutor,
        robot_action_processor: RobotProcessorPipeline,
        robot_observation_processor: RobotProcessorPipeline,
        vlm_check_registry: VlmCheckRegistry,
    ) -> None:
        """@brief Construct the service node and register every ROS2 service.

        @param cfg Runtime configuration loaded from YAML.
        @param robot Connected robot object used by the executor backend.
        @param executor_backend Object that actually runs learned skills.
        @param robot_action_processor Pipeline that converts policy actions.
        @param robot_observation_processor Pipeline that converts observations.
        @param vlm_check_registry In-memory state machine for skill attempts.
        """
        super().__init__("lerobot_bt_skill_server")
        self.cfg = cfg
        self.robot = robot
        self.executor_backend = executor_backend
        self.robot_action_processor = robot_action_processor
        self.robot_observation_processor = robot_observation_processor
        self.vlm_check_registry = vlm_check_registry
        self._command_callback_group = MutuallyExclusiveCallbackGroup()
        self._vlm_callback_group = ReentrantCallbackGroup()

        # ROS2 entrypoints used by the BT runtime and verifier-facing topics.
        bt_command_service_type, vlm_state_service_type, legacy_vlm_result_service_type = _load_bt_services()
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
        self.get_logger().info(
            "Serving BT commands on "
            f"'{cfg.bt_command_service}', VLM state service on "
            f"'{cfg.vlm_state_service}', legacy VLM result service on "
            f"'{cfg.legacy_vlm_result_service}', VLM requests on "
            f"'{cfg.vlm_request_topic}', and VLM results from "
            f"'{cfg.vlm_result_topic}'."
        )

    def _handle_request(self, request, response):
        """@brief Handle one `RunNamedCommand` service request.

        @param request ROS2 request with `kind`, `name`, and `timeout_s`.
        @param response Mutable ROS2 response filled before returning.
        @return The filled ROS2 response object.

        This method deliberately separates command execution from post-skill
        scene check. A successful skill opens a VLM check attempt; the
        BT can only advance after `VerifySkillOutcome` sees that attempt resolve.
        """
        # This is the handoff point between C++ BT orchestration and Python execution.
        log_say(f"Executing {request.kind} {request.name}", self.cfg.play_sounds)

        try:
            if request.kind == "skill":
                # Real learned primitive: delegate to the robot/policy executor.
                result = self.executor_backend.execute_skill(
                    skill_name=request.name,
                    robot_action_processor=self.robot_action_processor,
                    robot_observation_processor=self.robot_observation_processor,
                    timeout_override_s=request.timeout_s,
                )
            elif request.kind == VLM_GATE_PENDING_KIND:
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
            response.message = f"Unsupported command kind '{request.kind}'."
            self.get_logger().error(response.message)
            return response

        if request.kind in {"skill", VLM_GATE_PENDING_KIND} and result.success:
            try:
                if request.kind == VLM_GATE_PENDING_KIND:
                    # Gate names do not need to exist in the real skill config.
                    self.vlm_check_registry.register_skill_name(request.name)
                vlm_check_attempt = self.vlm_check_registry.begin_attempt(request.name)
                live_vlm_status = getattr(result, "vlm_status", None)
                if live_vlm_status:
                    self.vlm_check_registry.report(
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
                    publish_vlm_request = getattr(self, "_publish_vlm_request", None)
                    if publish_vlm_request is not None:
                        publish_vlm_request(vlm_check_attempt)
                    vlm_request_topic = getattr(
                        self.cfg,
                        "vlm_request_topic",
                        self.cfg.vlm_state_service,
                    )
                    result.message = (
                        f"{result.message} "
                        f"VLM check attempt {vlm_check_attempt.attempt_id} is now pending on "
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
            snapshot = self.vlm_check_registry.get_latest(request.skill_name)
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
        return response

    def _handle_legacy_vlm_result(self, request, response):
        """@brief Accept a verifier verdict for a pending skill attempt.

        @param request ROS2 request containing skill name, attempt id, status,
            and message.
        @param response Mutable ROS2 response that reports whether the verdict
            was applied.
        @return The filled ROS2 response object.
        """
        if self._try_report_active_skill_vlm_result(
            skill_name=request.skill_name,
            attempt_id=int(request.attempt_id),
            status=request.status,
            message=request.message,
        ):
            response.accepted = True
            response.applied_attempt_id = 0
            response.message = (
                f"Accepted VLM status {request.status} as live stop for active skill "
                f"'{request.skill_name}'."
            )
            return response

        try:
            update = self.vlm_check_registry.report(
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
        log_fn = self.get_logger().info if update.accepted else self.get_logger().warning
        log_fn(response.message)
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
        report_active = getattr(self.executor_backend, "report_active_vlm_result", None)
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

    def _publish_vlm_request(self, snapshot) -> None:
        """@brief Publish a topic event asking a VLM/manual verifier for a verdict."""
        from std_msgs.msg import String  # type: ignore

        payload = {
            "event": "vlm_check_requested",
            "skill_name": snapshot.skill_name,
            "attempt_id": int(snapshot.attempt_id),
            "status": VLM_PENDING,
            "message": snapshot.message,
            "allowed_statuses": [
                "PENDING",
                "RUNNING",
                "WAIT_HUMAN",
                "MANUAL_INTERVENTION_REQUIRED",
                "SUCCESS",
                "FAILURE",
            ],
            "allowed_next_actions": [
                "CONTINUE",
                "RETRY_SKILL",
                "WAIT_HUMAN",
                "REQUEST_MANUAL_INTERVENTION",
            ],
        }
        msg = String()
        msg.data = json.dumps(payload, sort_keys=True)
        self._vlm_request_publisher.publish(msg)
        self.get_logger().info(
            f"Published VLM request for skill '{snapshot.skill_name}' attempt {snapshot.attempt_id}."
        )

    def _handle_vlm_result_topic(self, msg) -> None:
        """@brief Apply one JSON verifier verdict received from a ROS2 topic."""
        try:
            payload = json.loads(msg.data)
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error(f"Invalid VLM result JSON: {exc}: '{msg.data}'")
            return
        if not isinstance(payload, dict):
            self.get_logger().error("Rejected VLM result topic message: payload must be a JSON object.")
            return

        try:
            skill_name = str(payload.get("skill_name", ""))
            status = _vlm_status_from_payload(payload)
            attempt_id = int(payload.get("attempt_id", 0))
            message = _vlm_message_from_payload(payload, status=status)
            if self._try_report_active_skill_vlm_result(
                skill_name=skill_name,
                attempt_id=attempt_id,
                status=status,
                message=message,
            ):
                return
            update = self.vlm_check_registry.report(
                skill_name=skill_name,
                attempt_id=attempt_id,
                status=status,
                message=message,
            )
        except (TypeError, ValueError) as exc:
            self.get_logger().error(f"Rejected VLM result topic message: {exc}")
            return

        log_fn = self.get_logger().info if update.accepted else self.get_logger().warning
        log_fn(update.message)


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
    robot_action_processor = _build_robot_processor_pipeline(
        cfg.robot_action_processor,
        to_transition=robot_action_observation_to_transition,
        to_output=transition_to_robot_action,
    )
    logging.info("Robot action processor ready.")

    logging.info("Building robot observation processor.")
    robot_observation_processor = _build_robot_processor_pipeline(
        cfg.robot_observation_processor,
        to_transition=observation_to_transition,
        to_output=transition_to_observation,
    )
    logging.info("Robot observation processor ready.")

    logging.info("Constructing skill command executor.")
    executor_backend = SkillCommandExecutor(cfg=cfg, robot=robot)
    logging.info("Skill command executor ready.")
    vlm_check_registry = VlmCheckRegistry(
        known_skill_names=set(executor_backend.skill_configs),
        vlm_timeout_s=cfg.vlm_timeout_s,
    )
    logging.info("VLM check registry ready.")

    logging.info("Creating ROS2 skill command service node.")
    server_node = SkillCommandServer(
        cfg=cfg,
        robot=robot,
        executor_backend=executor_backend,
        robot_action_processor=robot_action_processor,
        robot_observation_processor=robot_observation_processor,
        vlm_check_registry=vlm_check_registry,
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
        ros_executor.spin()
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
