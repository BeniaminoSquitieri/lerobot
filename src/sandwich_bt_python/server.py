#!/usr/bin/env python

"""ROS2 service server for the Python execution layer.

Flow role:
1. Wait for the C++ BT to send a named command.
2. Dispatch that command to either:
   - a learned ACT skill, or
   - a scripted recovery.
3. Return the result to the BT so the tree can continue or retry.
"""

import logging
from dataclasses import asdict
from pathlib import Path
from pprint import pformat

import rclpy
from rclpy.node import Node

from lerobot.configs import parser
from lerobot.processor import RobotProcessorPipeline
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

        from sandwich_bt_interfaces.srv import RunNamedCommand

        # Single ROS2 entrypoint used by the BT runtime.
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

    if not rclpy.ok():
        rclpy.init()

    if cfg.display_data and not is_headless():
        init_rerun_viz(session_name="sandwich_bt_skill_server")

    robot = CustomManipulator(cfg.robot)
    robot_action_processor = RobotProcessorPipeline.from_config(
        cfg.robot_action_processor,
        to_transition=robot_action_observation_to_transition,
        to_output=transition_to_robot_action,
    )
    robot_observation_processor = RobotProcessorPipeline.from_config(
        cfg.robot_observation_processor,
        to_transition=observation_to_transition,
        to_output=transition_to_observation,
    )
    executor_backend = SkillCommandExecutor(cfg=cfg, robot=robot)
    server_node = SkillCommandServer(
        cfg=cfg,
        robot=robot,
        executor_backend=executor_backend,
        robot_action_processor=robot_action_processor,
        robot_observation_processor=robot_observation_processor,
    )

    try:
        # Robot-facing startup happens before we start accepting BT commands.
        robot.connect()
        if cfg.reset_robot_on_startup:
            robot.reset()
        rclpy.spin(server_node)
    finally:
        server_node.destroy_node()
        robot.disconnect()
        if rclpy.ok():
            rclpy.shutdown()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
