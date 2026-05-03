"""Thin ROS2 adapter for the collaborative sandwich supervisor."""

#!/usr/bin/env python

"""ROS2 service server for the collaborative sandwich supervisor."""

from __future__ import annotations

import argparse
import logging
from dataclasses import asdict
from pathlib import Path
from pprint import pformat

import rclpy
from rclpy.node import Node

from lerobot.utils.utils import init_logging

from .config_io import load_supervisor_config
from .human_interface import HumanCommandExecutor
from .planner_schema import PlanStepDecision, StepVerification, SupervisorConfig, TaskPrimitive
from .ros_services import load_supervisor_services
from .scene_state import SandwichSceneEstimator, SandwichSceneObservation
from .task_allocator import SandwichTaskAllocator
from .vlm_supervisor import CollaborativeSandwichSupervisor

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "sandwich_bt_supervisor.yaml"


class _UnavailableRobotExecutor:
    def execute(self, primitive: TaskPrimitive):  # pragma: no cover - guard rail only
        raise RuntimeError(
            f"Robot execution for '{primitive.name}' is not available in sandwich_bt_supervisor.server. "
            "Use a separate collaborative runner to execute robot subtrees."
        )


class _UnavailableHumanExecutor(HumanCommandExecutor):
    def __init__(self) -> None:
        super().__init__(
            observe_scene=lambda: SandwichSceneObservation(),
            verify_step=lambda _step_name, _observation: StepVerification(
                success=False,
                observed_state="",
                failure_reason="human execution is unavailable in sandwich_bt_supervisor.server",
                confidence=0.0,
            ),
        )

    def execute(self, primitive: TaskPrimitive, timeout_s: float):
        del timeout_s
        raise RuntimeError(
            f"Human execution for '{primitive.name}' is not available in sandwich_bt_supervisor.server. "
            "Use a separate collaborative runner to handle robot/human execution."
        )


def _request_to_scene_observation(request) -> SandwichSceneObservation:
    return SandwichSceneObservation(
        first_toast_on_plate=bool(request.first_toast_on_plate),
        ingredient_on_first_toast=bool(request.ingredient_on_first_toast),
        second_toast_on_top=bool(request.second_toast_on_top),
    )


class SupervisorServiceBackend:
    """Thin request-to-domain adapter used by the ROS2 node and unit tests."""

    def __init__(self, cfg: SupervisorConfig) -> None:
        self.cfg = cfg
        self._current_observation = SandwichSceneObservation()
        self._supervisor = CollaborativeSandwichSupervisor(
            cfg=cfg,
            observe_scene=self._observe_scene,
            scene_estimator=SandwichSceneEstimator(),
            task_allocator=SandwichTaskAllocator(cfg),
            robot_executor=_UnavailableRobotExecutor(),
            human_executor=_UnavailableHumanExecutor(),
        )

    def plan_next_action(self, request) -> PlanStepDecision:
        self._current_observation = _request_to_scene_observation(request)
        return self._supervisor.plan_next_step(
            goal=request.goal or None,
            current_task=request.current_task or None,
            available_robot_skills=list(request.available_robot_skills),
            available_human_skills=list(request.available_human_skills),
        )

    def verify_step(self, request) -> StepVerification:
        self._current_observation = _request_to_scene_observation(request)
        return self._supervisor.verify_step(request.step_name)

    def _observe_scene(self) -> SandwichSceneObservation:
        return self._current_observation


class SandwichSupervisorServer(Node):
    def __init__(
        self,
        cfg: SupervisorConfig,
        backend: SupervisorServiceBackend | None = None,
    ) -> None:
        super().__init__(
            "sandwich_bt_supervisor_server",
            start_parameter_services=False,
            enable_logger_service=False,
        )
        self.cfg = cfg
        self.backend = backend if backend is not None else SupervisorServiceBackend(cfg)

        plan_next_step_service, verify_step_service = load_supervisor_services()
        self._plan_service = self.create_service(
            plan_next_step_service,
            cfg.service.plan_service_name,
            self._handle_next_action,
        )
        self._verify_service = self.create_service(
            verify_step_service,
            cfg.service.verify_service_name,
            self._handle_verify_step,
        )
        self.get_logger().info(
            f"Serving supervisor APIs on '{cfg.service.plan_service_name}' "
            f"and '{cfg.service.verify_service_name}'."
        )

    def _handle_next_action(self, request, response):
        try:
            decision = self.backend.plan_next_action(request)
        except Exception as exc:  # noqa: BLE001
            response.step_name = ""
            response.actor = "abort"
            response.reason = f"Supervisor exception while planning next action: {exc}"
            response.expected_state = "DONE"
            response.confidence = 0.0
            self.get_logger().exception(response.reason)
            return response

        response.step_name = decision.step_name
        response.actor = decision.actor
        response.reason = decision.reason
        response.expected_state = decision.expected_state
        response.confidence = float(decision.confidence)
        return response

    def _handle_verify_step(self, request, response):
        try:
            verification = self.backend.verify_step(request)
        except Exception as exc:  # noqa: BLE001
            response.success = False
            response.observed_state = ""
            response.failure_reason = f"Supervisor exception while verifying step: {exc}"
            response.confidence = 0.0
            self.get_logger().exception(response.failure_reason)
            return response

        response.success = bool(verification.success)
        response.observed_state = verification.observed_state
        response.failure_reason = verification.failure_reason
        response.confidence = float(verification.confidence)
        return response

def run(cfg: SupervisorConfig) -> None:
    init_logging()
    logging.info(pformat(asdict(cfg)))

    logging.info("Initializing ROS2 client library.")
    if not rclpy.ok():
        rclpy.init()
    logging.info("ROS2 client library is ready.")

    logging.info("Creating ROS2 supervisor service node.")
    server_node = SandwichSupervisorServer(cfg=cfg)
    logging.info("ROS2 supervisor service node is ready.")

    try:
        logging.info("Spinning supervisor server.")
        try:
            rclpy.spin(server_node)
        except KeyboardInterrupt:
            logging.info("Supervisor server interrupted, shutting down.")
    finally:
        try:
            server_node.destroy_node()
        except Exception:  # noqa: BLE001
            logging.exception("Best-effort ROS2 node destruction failed during supervisor shutdown.")
        if rclpy.ok():
            rclpy.shutdown()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config_path",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to the supervisor YAML config.",
    )
    args = parser.parse_args(argv)
    cfg = load_supervisor_config(args.config_path)
    run(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
