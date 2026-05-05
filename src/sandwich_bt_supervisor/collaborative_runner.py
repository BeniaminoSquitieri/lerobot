#!/usr/bin/env python

"""@file collaborative_runner.py
@brief Collaborative runner above the supervisor ROS2 services.

@details
The supervisor service decides which actor owns the next step. This runner owns
the live loop: observe scene, request the next action, execute the robot/human
step, verify the updated scene, and translate the outcome into a process exit
code.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Protocol

import rclpy
from rclpy.node import Node

from lerobot.robots.custom_manipulator.ros_spin import spin_until_future_complete
from sandwich_bt_python.simulation import (
    MockRunNamedCommandResponse,
    MockRunNamedCommandService,
    MockSkillCommandExecutor,
    build_demo_stack,
)

from .bt_executor import BtXmlRobotExecutor
from .config_io import load_supervisor_config
from .named_command_backends import (
    InProcessMockNamedCommandBackend,
    NamedCommandBackend,
    NamedCommandServiceUnavailableError,
    Ros2NamedCommandBackend,
)
from .planner_schema import (
    PlanStepDecision,
    StepExecutionResult,
    StepVerification,
    SupervisorConfig,
    TaskPrimitive,
)
from .ros_services import GeneratedInterfaceError, load_supervisor_services
from .scene_state import SandwichSceneObservation

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "sandwich_bt_supervisor.yaml"
DEFAULT_RUN_NAMED_COMMAND_SERVICE = "/sandwich_bt/run_command"
VALID_ROBOT_BACKENDS = {"in-process", "ros2"}
VALID_SUPERVISOR_ACTORS = {"robot", "human", "done", "abort"}


class CollaborativeRunnerExitCode(IntEnum):
    """@brief Process exit codes returned by the collaborative runner CLI."""

    DONE = 0
    """Task completed successfully."""

    ABORT = 1
    """Task aborted or verification failed."""

    SERVICE_UNAVAILABLE = 2
    """ROS2 service dependency was unavailable."""

    INVALID_RUNTIME = 3
    """Configuration, generated interfaces, or supervisor output was invalid."""


class SupervisorServiceUnavailableError(RuntimeError):
    """Raised when the live supervisor services cannot be reached."""


class SceneObservationProviderProtocol(Protocol):
    """@brief Interface for objects that provide closed-set scene observations."""

    def observe(self) -> SandwichSceneObservation:
        """@brief Return the latest closed-set scene observation."""
        ...


@dataclass
class MockClosedSetSceneProvider:
    """@brief Deterministic scene state used by hardware-free runner tests."""

    first_toast_on_plate: bool = False
    ingredient_on_first_toast: bool = False
    second_toast_on_top: bool = False
    events: list[str] = field(default_factory=list)

    def observe(self) -> SandwichSceneObservation:
        """@brief Convert internal booleans to a domain observation object."""
        return SandwichSceneObservation(
            first_toast_on_plate=self.first_toast_on_plate,
            ingredient_on_first_toast=self.ingredient_on_first_toast,
            second_toast_on_top=self.second_toast_on_top,
        )

    def mark_robot_step_completed(self, primitive_name: str) -> None:
        """@brief Apply the expected scene effect of a robot-owned primitive."""
        self._mark_step_completed(primitive_name)
        self.events.append(f"robot_completed:{primitive_name}")

    def mark_human_step_completed(self, primitive_name: str) -> None:
        """@brief Apply the expected scene effect of a human-owned primitive."""
        self._mark_step_completed(primitive_name)
        self.events.append(f"human_completed:{primitive_name}")

    def _mark_step_completed(self, primitive_name: str) -> None:
        """@brief Mutate the one boolean associated with a completed primitive."""
        if primitive_name == "place_first_toast":
            self.first_toast_on_plate = True
        elif primitive_name == "pour_ingredient":
            self.ingredient_on_first_toast = True
        elif primitive_name == "place_second_toast":
            self.second_toast_on_top = True


class SupervisorClientProtocol(Protocol):
    """@brief Interface implemented by ROS2 and test supervisor clients."""

    def plan_next_action(
        self,
        *,
        goal: str,
        current_task: str,
        available_robot_skills: list[str],
        available_human_skills: list[str],
        observation: SandwichSceneObservation,
    ) -> PlanStepDecision:
        """@brief Request a supervisor decision for the next action."""
        ...

    def verify_step(
        self,
        *,
        step_name: str,
        observation: SandwichSceneObservation,
    ) -> StepVerification:
        """@brief Request supervisor verification for a completed step."""
        ...


class SupervisorRos2Client(Node):
    """@brief ROS2 client used by the runner to call supervisor services."""

    def __init__(self, cfg: SupervisorConfig) -> None:
        """@brief Create planning and verification clients from config."""
        super().__init__(
            "sandwich_bt_collaborative_runner",
            start_parameter_services=False,
            enable_logger_service=False,
        )
        self.cfg = cfg
        self._plan_service_type, self._verify_service_type = load_supervisor_services()
        self._plan_client = self.create_client(self._plan_service_type, cfg.service.plan_service_name)
        self._verify_client = self.create_client(self._verify_service_type, cfg.service.verify_service_name)

    def wait_for_services(self, timeout_s: float = 5.0) -> None:
        """@brief Block until both supervisor services are reachable."""
        if not self._plan_client.wait_for_service(timeout_sec=timeout_s):
            raise SupervisorServiceUnavailableError(
                f"Supervisor service '{self.cfg.service.plan_service_name}' is not available."
            )
        if not self._verify_client.wait_for_service(timeout_sec=timeout_s):
            raise SupervisorServiceUnavailableError(
                f"Supervisor service '{self.cfg.service.verify_service_name}' is not available."
            )

    def plan_next_action(
        self,
        *,
        goal: str,
        current_task: str,
        available_robot_skills: list[str],
        available_human_skills: list[str],
        observation: SandwichSceneObservation,
    ) -> PlanStepDecision:
        """@brief Call `/sandwich_supervisor/next_action` and map the response."""
        request = self._plan_service_type.Request()
        request.goal = goal
        request.current_task = current_task
        request.available_robot_skills = available_robot_skills
        request.available_human_skills = available_human_skills
        request.first_toast_on_plate = observation.first_toast_on_plate
        request.ingredient_on_first_toast = observation.ingredient_on_first_toast
        request.second_toast_on_top = observation.second_toast_on_top

        future = self._plan_client.call_async(request)
        spin_until_future_complete(self, future)
        response = future.result()
        if response is None:
            raise SupervisorServiceUnavailableError("Supervisor next_action call returned no response.")

        return PlanStepDecision(
            step_name=response.step_name,
            actor=response.actor,
            reason=response.reason,
            expected_state=response.expected_state,
            confidence=float(response.confidence),
        )

    def verify_step(
        self,
        *,
        step_name: str,
        observation: SandwichSceneObservation,
    ) -> StepVerification:
        """@brief Call `/sandwich_supervisor/verify_step` and map the response."""
        request = self._verify_service_type.Request()
        request.step_name = step_name
        request.first_toast_on_plate = observation.first_toast_on_plate
        request.ingredient_on_first_toast = observation.ingredient_on_first_toast
        request.second_toast_on_top = observation.second_toast_on_top

        future = self._verify_client.call_async(request)
        spin_until_future_complete(self, future)
        response = future.result()
        if response is None:
            raise SupervisorServiceUnavailableError("Supervisor verify_step call returned no response.")

        return StepVerification(
            success=bool(response.success),
            observed_state=response.observed_state,
            failure_reason=response.failure_reason,
            confidence=float(response.confidence),
        )


class MockHumanStepExecutor:
    """@brief Deterministic human executor used by mock-scene runs."""

    def __init__(self, scene_provider: MockClosedSetSceneProvider, *, deny_confirmation: bool = False) -> None:
        """@brief Store the scene provider and optional negative-test flag."""
        self.scene_provider = scene_provider
        self.deny_confirmation = deny_confirmation
        self.instructions: list[str] = []

    def execute(self, primitive: TaskPrimitive) -> StepExecutionResult:
        """@brief Simulate presenting a human instruction and receiving confirmation."""
        instruction = primitive.human_instruction or primitive.name
        self.instructions.append(instruction)
        self.scene_provider.events.append(f"instruction:{instruction}")

        if self.deny_confirmation:
            self.scene_provider.events.append(f"human_rejected:{primitive.name}")
            return StepExecutionResult(
                step_name=primitive.name,
                actor="human",
                success=False,
                status="FAILURE",
                elapsed_s=0.0,
                message=f"Human step '{primitive.name}' was not confirmed.",
            )

        self.scene_provider.mark_human_step_completed(primitive.name)
        return StepExecutionResult(
            step_name=primitive.name,
            actor="human",
            success=True,
            status="SUCCESS",
            elapsed_s=0.0,
            message=f"Human step '{primitive.name}' was confirmed.",
        )


@dataclass(frozen=True)
class CollaborativeRunnerStep:
    """@brief One completed runner loop iteration."""

    decision: PlanStepDecision
    execution: StepExecutionResult
    verification: StepVerification


@dataclass(frozen=True)
class CollaborativeRunnerResult:
    """@brief Final outcome returned by `CollaborativeRunner.run_until_done`."""

    steps: list[CollaborativeRunnerStep]
    final_actor: str
    final_reason: str


class CollaborativeRunner:
    """@brief Orchestrates the robot/human loop above supervisor services."""

    def __init__(
        self,
        *,
        cfg: SupervisorConfig,
        supervisor_client: SupervisorClientProtocol,
        scene_provider: SceneObservationProviderProtocol,
        robot_executor: BtXmlRobotExecutor,
        human_executor: MockHumanStepExecutor,
    ) -> None:
        """@brief Wire config, clients, scene provider, and step executors."""
        self.cfg = cfg
        self.supervisor_client = supervisor_client
        self.scene_provider = scene_provider
        self.robot_executor = robot_executor
        self.human_executor = human_executor
        self._primitives = {primitive.name: primitive for primitive in cfg.task_primitives}

    def run_until_done(self, *, max_steps: int = 8) -> CollaborativeRunnerResult:
        """@brief Execute the collaborative loop until done, abort, or max steps."""
        steps: list[CollaborativeRunnerStep] = []

        for _ in range(max_steps):
            observation = self.scene_provider.observe()
            decision = self.supervisor_client.plan_next_action(
                goal=self.cfg.goal,
                current_task=self.cfg.current_task,
                available_robot_skills=self.cfg.available_robot_skills,
                available_human_skills=self.cfg.available_human_skills,
                observation=observation,
            )
            self._validate_decision(decision)

            if decision.actor == "done":
                return CollaborativeRunnerResult(steps=steps, final_actor="done", final_reason=decision.reason)
            if decision.actor == "abort":
                return CollaborativeRunnerResult(steps=steps, final_actor="abort", final_reason=decision.reason)

            primitive = self._primitives[decision.step_name]
            if decision.actor == "robot":
                execution = self.robot_executor.execute(primitive)
            elif decision.actor == "human":
                execution = self.human_executor.execute(primitive)
            else:
                raise ValueError(f"Unsupported actor '{decision.actor}'.")

            verification = self.supervisor_client.verify_step(
                step_name=decision.step_name,
                observation=self.scene_provider.observe(),
            )
            steps.append(CollaborativeRunnerStep(decision=decision, execution=execution, verification=verification))

            if not verification.success:
                return CollaborativeRunnerResult(
                    steps=steps,
                    final_actor="abort",
                    final_reason=verification.failure_reason or execution.message,
                )

        return CollaborativeRunnerResult(
            steps=steps,
            final_actor="abort",
            final_reason=f"Collaborative runner exceeded max_steps={max_steps}.",
        )

    def _validate_decision(self, decision: PlanStepDecision) -> None:
        """@brief Reject malformed supervisor decisions before execution."""
        if decision.actor not in VALID_SUPERVISOR_ACTORS:
            raise ValueError(
                f"Supervisor returned unsupported actor '{decision.actor}'. "
                f"Expected one of {sorted(VALID_SUPERVISOR_ACTORS)}."
            )
        if decision.actor in {"robot", "human"} and decision.step_name not in self._primitives:
            raise ValueError(
                f"Supervisor returned unknown step '{decision.step_name}'. "
                f"Known configured steps: {sorted(self._primitives)}."
            )


@dataclass
class MockCollaborativeRunnerStack:
    """@brief Bundle of runner objects returned by test builders."""

    runner: CollaborativeRunner
    scene_provider: MockClosedSetSceneProvider
    supervisor_client: SupervisorClientProtocol
    robot_executor: BtXmlRobotExecutor
    human_executor: MockHumanStepExecutor
    command_backend: NamedCommandBackend
    skill_service: MockRunNamedCommandService | None
    skill_executor: MockSkillCommandExecutor | None


def build_mock_collaborative_runner(
    *,
    cfg: SupervisorConfig,
    supervisor_client: SupervisorClientProtocol,
    deny_human_confirmation: bool = False,
    use_delta_actions: bool = False,
    scripted_responses: dict[tuple[str, str], list[MockRunNamedCommandResponse]] | None = None,
    command_backend: NamedCommandBackend | None = None,
    skill_service: MockRunNamedCommandService | None = None,
    skill_executor: MockSkillCommandExecutor | None = None,
) -> MockCollaborativeRunnerStack:
    """@brief Build a hardware-free collaborative runner stack for tests/CLI."""
    if command_backend is None:
        skill_service = build_demo_stack(
            use_delta_actions=use_delta_actions,
            scripted_responses=scripted_responses,
        )
        skill_executor = skill_service.executor
        command_backend = InProcessMockNamedCommandBackend(skill_service)

    scene_provider = MockClosedSetSceneProvider()
    robot_executor = BtXmlRobotExecutor(
        command_backend=command_backend,
        on_step_success=scene_provider.mark_robot_step_completed,
    )
    human_executor = MockHumanStepExecutor(
        scene_provider=scene_provider,
        deny_confirmation=deny_human_confirmation,
    )
    runner = CollaborativeRunner(
        cfg=cfg,
        supervisor_client=supervisor_client,
        scene_provider=scene_provider,
        robot_executor=robot_executor,
        human_executor=human_executor,
    )
    return MockCollaborativeRunnerStack(
        runner=runner,
        scene_provider=scene_provider,
        supervisor_client=supervisor_client,
        robot_executor=robot_executor,
        human_executor=human_executor,
        command_backend=command_backend,
        skill_service=skill_service,
        skill_executor=skill_executor,
    )


def exit_code_for_result(result: CollaborativeRunnerResult) -> int:
    """@brief Map a runner result to the documented process exit code."""
    return int(
        CollaborativeRunnerExitCode.DONE
        if result.final_actor == "done"
        else CollaborativeRunnerExitCode.ABORT
    )


def _print_runner_result(result: CollaborativeRunnerResult) -> None:
    """@brief Print a compact human-readable execution trace."""
    for step in result.steps:
        print(
            f"{step.decision.actor}:{step.decision.step_name} -> "
            f"{step.execution.status} {step.execution.message}"
        )
    print(f"final -> {result.final_actor} ({result.final_reason})")


def build_named_command_backend(
    *,
    robot_backend: str,
    run_command_service_name: str,
    use_delta_actions: bool,
) -> tuple[
    NamedCommandBackend,
    MockRunNamedCommandService | None,
    MockSkillCommandExecutor | None,
]:
    """@brief Build either an in-process or ROS2 named-command backend."""
    if robot_backend == "in-process":
        skill_service = build_demo_stack(
            use_delta_actions=use_delta_actions,
            service_name=run_command_service_name,
        )
        return (
            InProcessMockNamedCommandBackend(skill_service),
            skill_service,
            skill_service.executor,
        )
    if robot_backend == "ros2":
        return (
            Ros2NamedCommandBackend(service_name=run_command_service_name),
            None,
            None,
        )
    raise ValueError(
        f"Unsupported robot backend '{robot_backend}'. Expected one of {sorted(VALID_ROBOT_BACKENDS)}."
    )


def main(argv: list[str] | None = None) -> int:
    """@brief CLI entry point for `lerobot-bt-collaborative-runner`."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-path",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to the supervisor YAML config.",
    )
    parser.add_argument(
        "--mock-scene",
        action="store_true",
        help="Run the deterministic closed-set mock scene loop.",
    )
    parser.add_argument(
        "--deny-human-confirmation",
        action="store_true",
        help="Simulate a human that does not confirm the requested handoff.",
    )
    parser.add_argument(
        "--use-delta-actions",
        action="store_true",
        help="Use the mock delta-action robot backend for the robot subtree executor.",
    )
    parser.add_argument(
        "--robot-backend",
        default="in-process",
        choices=sorted(VALID_ROBOT_BACKENDS),
        help="Backend used by BtXmlRobotExecutor for each RunNamedCommand call.",
    )
    parser.add_argument(
        "--run-command-service-name",
        default=DEFAULT_RUN_NAMED_COMMAND_SERVICE,
        help="ROS2 service name used by the RunNamedCommand robot backend.",
    )
    args = parser.parse_args(argv)

    if not args.mock_scene:
        print("Only --mock-scene is supported in the current collaborative runner.", file=sys.stderr)
        return int(CollaborativeRunnerExitCode.INVALID_RUNTIME)

    try:
        cfg = load_supervisor_config(args.config_path)
    except Exception as exc:  # noqa: BLE001
        print(f"Invalid collaborative runner config: {exc}", file=sys.stderr)
        return int(CollaborativeRunnerExitCode.INVALID_RUNTIME)

    initialized_rclpy = False
    command_backend: NamedCommandBackend | None = None
    supervisor_client: SupervisorRos2Client | None = None
    if not rclpy.ok():
        rclpy.init()
        initialized_rclpy = True

    try:
        supervisor_client = SupervisorRos2Client(cfg)
        supervisor_client.wait_for_services()
        command_backend, skill_service, skill_executor = build_named_command_backend(
            robot_backend=args.robot_backend,
            run_command_service_name=args.run_command_service_name,
            use_delta_actions=args.use_delta_actions,
        )
        if isinstance(command_backend, Ros2NamedCommandBackend):
            command_backend.wait_for_service()
        stack = build_mock_collaborative_runner(
            cfg=cfg,
            supervisor_client=supervisor_client,
            deny_human_confirmation=args.deny_human_confirmation,
            use_delta_actions=args.use_delta_actions,
            command_backend=command_backend,
            skill_service=skill_service,
            skill_executor=skill_executor,
        )
        result = stack.runner.run_until_done()
        _print_runner_result(result)
        return exit_code_for_result(result)
    except SupervisorServiceUnavailableError as exc:
        print(f"ROS2 supervisor service error: {exc}", file=sys.stderr)
        return int(CollaborativeRunnerExitCode.SERVICE_UNAVAILABLE)
    except NamedCommandServiceUnavailableError as exc:
        print(f"ROS2 named-command service error: {exc}", file=sys.stderr)
        return int(CollaborativeRunnerExitCode.SERVICE_UNAVAILABLE)
    except (GeneratedInterfaceError, ValueError) as exc:
        print(f"Collaborative runner runtime error: {exc}", file=sys.stderr)
        return int(CollaborativeRunnerExitCode.INVALID_RUNTIME)
    finally:
        if isinstance(command_backend, Node):
            command_backend.destroy_node()
        if supervisor_client is not None:
            supervisor_client.destroy_node()
        if initialized_rclpy and rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
