#!/usr/bin/env python

"""@file server.py
@brief ROS2 service server for the Python execution layer.

@details
This module is the runtime boundary between the C++ BehaviorTree.CPP process and
the Python robot execution process. The C++ side never imports policy or robot
code directly: it sends a `RunNamedCommand` request, waits for this server to
finish the command, and then polls the verification services managed here.

Flow role:
1. Wait for the C++ BT to send a named command.
2. Dispatch that command to either:
   - a learned ACT skill, or
   - a scripted recovery.
3. Return the result to the BT so the tree can continue or retry.
"""

import importlib
import logging
import os
import sys
from dataclasses import asdict
from pathlib import Path
from pprint import pformat
from typing import TYPE_CHECKING, Any

import rclpy
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
    PENDING_VERIFICATION_STATUS,
    SUCCESSFUL_VERIFICATION_STATUS,
    UNKNOWN_VERIFICATION_STATUS,
    SkillVerificationRegistry,
)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "sandwich_bt_executor.yaml"
"""Default draccus YAML loaded when the entry point is started without flags."""

if TYPE_CHECKING:
    from lerobot.robots.custom_manipulator.custom_manipulator import CustomManipulator

SIMULATED_RECOVERY_KIND = "simulated_recovery"
"""Command kind that acknowledges a recovery without touching the robot."""

SIMULATED_SKILL_KIND = "simulated_skill"
"""Command kind that acknowledges a skill and auto-resolves verification."""

SIMULATED_SKILL_PENDING_KIND = "simulated_skill_pending"
"""Command kind that acknowledges a skill but leaves verification pending."""

_KINDS_THAT_OPEN_VERIFICATION = {
    "skill",
    SIMULATED_SKILL_KIND,
    SIMULATED_SKILL_PENDING_KIND,
}
_KINDS_THAT_AUTO_VERIFY = {
    SIMULATED_SKILL_KIND,
}


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

    The repository contains `src/sandwich_bt_interfaces`, while ROS2 generation
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
            repo_root / "install" / "sandwich_bt_interfaces",
            repo_root / "install",
        ]
    )

    for prefix in prefixes:
        site_packages = prefix / "lib" / python_dir / "site-packages"
        if (site_packages / "sandwich_bt_interfaces" / "srv").exists():
            site_packages_str = str(site_packages)
            if site_packages_str not in sys.path:
                sys.path.insert(0, site_packages_str)


def _load_bt_services():
    """@brief Import generated sandwich BT ROS2 service classes.

    @return `(RunNamedCommand, GetSkillVerification, ReportSkillVerification)`.
    @throws ImportError if the workspace has not been built or sourced.

    The editable repo adds `src/` to `sys.path`, which makes Python see the
    source-only ROS package as a namespace package before the generated
    interface package under `install/.../site-packages`.
    """
    _prepend_generated_interface_paths()
    for module_name in list(sys.modules):
        if module_name == "sandwich_bt_interfaces" or module_name.startswith("sandwich_bt_interfaces."):
            del sys.modules[module_name]

    try:
        from sandwich_bt_interfaces.srv import GetSkillVerification, ReportSkillVerification, RunNamedCommand

        return RunNamedCommand, GetSkillVerification, ReportSkillVerification
    except ImportError as import_error:
        raise ImportError(
            "Could not import the sandwich_bt_interfaces service bindings. "
            "Source install/local_setup.bash or rebuild sandwich_bt_interfaces."
        ) from import_error


class SkillCommandServer(Node):
    """@brief ROS2 node that executes BT commands and stores verification state.

    The node owns three services:
    - `RunNamedCommand`: command execution requested by BT XML leaf nodes.
    - `GetSkillVerification`: polling endpoint used by `VerifySkillOutcome`.
    - `ReportSkillVerification`: endpoint used by a VLM/manual verifier.
    """

    def __init__(
        self,
        cfg: SkillCommandServerConfig,
        robot: "CustomManipulator",
        executor_backend: SkillCommandExecutor,
        robot_action_processor: RobotProcessorPipeline,
        robot_observation_processor: RobotProcessorPipeline,
        verification_registry: SkillVerificationRegistry,
    ) -> None:
        """@brief Construct the service node and register every ROS2 service.

        @param cfg Runtime configuration loaded from YAML.
        @param robot Connected robot object used by the executor backend.
        @param executor_backend Object that actually runs skills/recoveries.
        @param robot_action_processor Pipeline that converts policy actions.
        @param robot_observation_processor Pipeline that converts observations.
        @param verification_registry In-memory state machine for skill attempts.
        """
        super().__init__("sandwich_bt_skill_server")
        self.cfg = cfg
        self.robot = robot
        self.executor_backend = executor_backend
        self.robot_action_processor = robot_action_processor
        self.robot_observation_processor = robot_observation_processor
        self.verification_registry = verification_registry

        # ROS2 entrypoints used by the BT runtime and the external verifier.
        run_named_command, get_skill_verification, report_skill_verification = _load_bt_services()
        self._command_service = self.create_service(run_named_command, cfg.service_name, self._handle_request)
        self._verification_query_service = self.create_service(
            get_skill_verification,
            cfg.verification_query_service_name,
            self._handle_get_skill_verification,
        )
        self._verification_report_service = self.create_service(
            report_skill_verification,
            cfg.verification_report_service_name,
            self._handle_report_skill_verification,
        )
        self.get_logger().info(
            "Serving BT commands on "
            f"'{cfg.service_name}', verification queries on "
            f"'{cfg.verification_query_service_name}', and verification reports on "
            f"'{cfg.verification_report_service_name}'."
        )

    def _handle_request(self, request, response):
        """@brief Handle one `RunNamedCommand` service request.

        @param request ROS2 request with `kind`, `name`, and `timeout_s`.
        @param response Mutable ROS2 response filled before returning.
        @return The filled ROS2 response object.

        This method deliberately separates command execution from post-skill
        scene verification. A successful skill opens a verification attempt; the
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
            elif request.kind == "recovery":
                # Real scripted recovery: delegate to deterministic recovery code.
                result = self.executor_backend.execute_named_recovery(
                    recovery_name=request.name,
                    timeout_override_s=request.timeout_s,
                )
            elif request.kind == SIMULATED_SKILL_KIND:
                # Bring-up path: act as though a skill ran and verification passed.
                result = CommandResult(
                    True,
                    "SUCCESS",
                    0.0,
                    f"Simulated skill '{request.name}' completed without robot execution.",
                )
            elif request.kind == SIMULATED_SKILL_PENDING_KIND:
                # Verification-flow test path: open an attempt but do not resolve it.
                result = CommandResult(
                    True,
                    "SUCCESS",
                    0.0,
                    f"Simulated skill '{request.name}' completed and is awaiting external verification.",
                )
            elif request.kind == SIMULATED_RECOVERY_KIND:
                # Bring-up path: recovery is treated as a no-op success.
                result = CommandResult(
                    True,
                    "SUCCESS",
                    0.0,
                    f"Simulated recovery '{request.name}' completed without robot execution.",
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

        if request.kind in _KINDS_THAT_OPEN_VERIFICATION and result.success:
            try:
                if request.kind in {SIMULATED_SKILL_KIND, SIMULATED_SKILL_PENDING_KIND}:
                    # Simulated skill names may not exist in the real skill config.
                    self.verification_registry.register_skill_name(request.name)
                verification_snapshot = self.verification_registry.begin_attempt(request.name)
                should_auto_verify = request.kind in _KINDS_THAT_AUTO_VERIFY or (
                    request.kind == "skill" and self.cfg.auto_verify_real_skills
                )
                if should_auto_verify:
                    self.verification_registry.report(
                        skill_name=request.name,
                        attempt_id=verification_snapshot.attempt_id,
                        status=SUCCESSFUL_VERIFICATION_STATUS,
                        message=f"Simulated verifier accepted skill '{request.name}'.",
                        confidence=1.0,
                    )
                    result.message = (
                        f"{result.message} "
                        f"Verification attempt {verification_snapshot.attempt_id} was auto-resolved as SUCCESS."
                    )
                else:
                    result.message = (
                        f"{result.message} "
                        f"Verification attempt {verification_snapshot.attempt_id} is now pending on "
                        f"'{self.cfg.verification_query_service_name}'."
                    )
            except Exception as exc:  # noqa: BLE001
                response.success = False
                response.status = "ERROR"
                response.elapsed_s = float(result.elapsed_s)
                response.message = f"Could not open verification for command '{request.name}': {exc}"
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

    def _handle_get_skill_verification(self, request, response):
        """@brief Return the latest verification attempt for one skill.

        @param request ROS2 request containing `skill_name`.
        @param response Mutable ROS2 response with attempt metadata.
        @return The filled ROS2 response object.
        """
        try:
            snapshot = self.verification_registry.get_latest(request.skill_name)
        except ValueError as exc:
            response.has_attempt = False
            response.attempt_id = 0
            response.status = UNKNOWN_VERIFICATION_STATUS
            response.message = str(exc)
            response.confidence = 0.0
            self.get_logger().error(response.message)
            return response

        if snapshot is None:
            response.has_attempt = False
            response.attempt_id = 0
            response.status = UNKNOWN_VERIFICATION_STATUS
            response.message = f"No completed attempt has been recorded yet for skill '{request.skill_name}'."
            response.confidence = 0.0
            self.get_logger().warning(response.message)
            return response

        response.has_attempt = True
        response.attempt_id = int(snapshot.attempt_id)
        response.status = snapshot.status
        response.message = snapshot.message
        response.confidence = float(snapshot.confidence)
        if snapshot.status == PENDING_VERIFICATION_STATUS:
            self.get_logger().debug(
                f"Verification for skill '{snapshot.skill_name}' attempt {snapshot.attempt_id} is still pending."
            )
        return response

    def _handle_report_skill_verification(self, request, response):
        """@brief Accept a verifier verdict for a pending skill attempt.

        @param request ROS2 request containing skill name, attempt id, status,
            message, and confidence.
        @param response Mutable ROS2 response that reports whether the verdict
            was applied.
        @return The filled ROS2 response object.
        """
        try:
            update = self.verification_registry.report(
                skill_name=request.skill_name,
                attempt_id=int(request.attempt_id),
                status=request.status,
                message=request.message,
                confidence=float(request.confidence),
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


@parser.wrap(config_path=DEFAULT_CONFIG_PATH)
def run(cfg: SkillCommandServerConfig) -> None:
    """@brief Start the real ROS2 skill command server.

    @param cfg Parsed draccus config. When invoked from the entry point this is
        loaded from `sandwich_bt_executor.yaml` unless another config is passed.

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
        init_rerun_viz(session_name="sandwich_bt_skill_server")
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
    verification_registry = SkillVerificationRegistry(known_skill_names=set(executor_backend.skill_configs))
    logging.info("Skill verification registry ready.")

    logging.info("Creating ROS2 skill command service node.")
    server_node = SkillCommandServer(
        cfg=cfg,
        robot=robot,
        executor_backend=executor_backend,
        robot_action_processor=robot_action_processor,
        robot_observation_processor=robot_observation_processor,
        verification_registry=verification_registry,
    )
    logging.info("ROS2 skill command service node is ready.")

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
        rclpy.spin(server_node)
    finally:
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
