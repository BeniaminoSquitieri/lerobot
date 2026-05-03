"""ROS2 command server for the sandwich BT stack.

Exposes `/sandwich_bt/run_command` and delegates named command execution.
"""

#!/usr/bin/env python

"""ROS2 service server for the Python execution layer.

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
from typing import Any

import rclpy
from rclpy.node import Node

from lerobot.configs import parser
from lerobot.processor import ProcessorStepRegistry, RobotProcessorPipeline
from lerobot.processor.converters import (
    observation_to_transition,
    robot_action_observation_to_transition,
    transition_to_observation,
    transition_to_robot_action,
)
from lerobot.robots.custom_manipulator.custom_manipulator import CustomManipulator
from lerobot.common.control_utils import is_headless
from lerobot.utils.utils import init_logging, log_say
from lerobot.utils.visualization_utils import init_rerun as init_rerun_viz

from .config import SkillCommandServerConfig
from .executor import SkillCommandExecutor


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "sandwich_bt_executor.yaml"


def _instantiate_processor_step(step_spec: Any):
    if isinstance(step_spec, str):
        step_class = ProcessorStepRegistry.get(step_spec)
        return step_class()

    if isinstance(step_spec, dict):
        if "registry_name" in step_spec:
            step_class = ProcessorStepRegistry.get(step_spec["registry_name"])
        elif "class" in step_spec:
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
    steps = [_instantiate_processor_step(step_spec) for step_spec in processor_cfg.get("steps", [])]
    return RobotProcessorPipeline(
        steps=steps,
        to_transition=to_transition,
        to_output=to_output,
    )


def _prepend_generated_interface_paths() -> None:
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
        if (site_packages / "sandwich_bt_interfaces" / "srv" / "__init__.py").exists():
            site_packages_str = str(site_packages)
            if site_packages_str not in sys.path:
                sys.path.insert(0, site_packages_str)


def _load_run_named_command_service():
    # The editable repo adds `src/` to `sys.path`, which makes Python see the
    # source-only ROS package as a namespace package before the generated
    # interface package under `install/.../site-packages`.
    _prepend_generated_interface_paths()
    for module_name in list(sys.modules):
        if module_name == "sandwich_bt_interfaces" or module_name.startswith("sandwich_bt_interfaces."):
            del sys.modules[module_name]

    try:
        from sandwich_bt_interfaces.srv import RunNamedCommand

        return RunNamedCommand
    except ImportError as import_error:
        raise ImportError(
            "Could not import sandwich_bt_interfaces.srv.RunNamedCommand. "
            "Source install/local_setup.bash or rebuild sandwich_bt_interfaces."
        ) from import_error


class SkillCommandServer(Node):
    def __init__(
        self,
        cfg: SkillCommandServerConfig,
        robot: CustomManipulator,
        executor_backend: SkillCommandExecutor,
        robot_action_processor: RobotProcessorPipeline,
        robot_observation_processor: RobotProcessorPipeline,
    ) -> None:
        super().__init__("sandwich_bt_skill_server")
        self.cfg = cfg
        self.robot = robot
        self.executor_backend = executor_backend
        self.robot_action_processor = robot_action_processor
        self.robot_observation_processor = robot_observation_processor

        # Single ROS2 entrypoint used by the BT runtime.
        RunNamedCommand = _load_run_named_command_service()
        self._service = self.create_service(RunNamedCommand, cfg.service_name, self._handle_request)
        self.get_logger().info(f"Serving BT commands on '{cfg.service_name}'.")

    def _handle_request(self, request, response):
        # This is the handoff point between C++ BT orchestration and Python execution.
        log_say(f"Executing {request.kind} {request.name}", self.cfg.play_sounds)

        try:
            if request.kind == "skill":
                result = self.executor_backend.execute_skill(
                    skill_name=request.name,
                    robot_action_processor=self.robot_action_processor,
                    robot_observation_processor=self.robot_observation_processor,
                    timeout_override_s=request.timeout_s,
                )
            elif request.kind == "recovery":
                result = self.executor_backend.execute_named_recovery(
                    recovery_name=request.name,
                    timeout_override_s=request.timeout_s,
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

        response.success = bool(result.success)
        response.status = result.status
        response.elapsed_s = float(result.elapsed_s)
        response.message = result.message
        if result.success:
            self.get_logger().info(result.message)
        else:
            self.get_logger().error(result.message)
        return response


@parser.wrap(config_path=DEFAULT_CONFIG_PATH)
def run(cfg: SkillCommandServerConfig) -> None:
    # Server startup phase:
    # load config -> build robot -> expose ROS2 service.
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

    logging.info("Creating ROS2 skill command service node.")
    server_node = SkillCommandServer(
        cfg=cfg,
        robot=robot,
        executor_backend=executor_backend,
        robot_action_processor=robot_action_processor,
        robot_observation_processor=robot_observation_processor,
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
    run()


if __name__ == "__main__":
    main()
