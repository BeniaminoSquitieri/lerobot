"""@file vlm_supervisor.py
@brief Supervisor that allocates closed-set sandwich subtasks to robot or human."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from typing import Protocol

from .human_interface import HumanCommandExecutor
from .planner_schema import (
    ExecutedSupervisorStep,
    PlanStepDecision,
    StepExecutionResult,
    SupervisorConfig,
    SupervisorRunResult,
    TaskPrimitive,
)
from .scene_state import SandwichSceneEstimator, SandwichSceneObservation
from .task_allocator import SandwichTaskAllocator


class RobotStepExecutor(Protocol):
    """@brief Interface for executors that can run robot-owned primitives."""

    def execute(self, primitive: TaskPrimitive) -> StepExecutionResult:
        """@brief Execute one robot-owned primitive."""
        ...


class CollaborativeSandwichSupervisor:
    """@brief Pure domain supervisor independent from ROS2 wire formats."""

    def __init__(
        self,
        *,
        cfg: SupervisorConfig,
        observe_scene: Callable[[], SandwichSceneObservation],
        scene_estimator: SandwichSceneEstimator,
        task_allocator: SandwichTaskAllocator,
        robot_executor: RobotStepExecutor,
        human_executor: HumanCommandExecutor,
    ) -> None:
        """@brief Inject scene, planning, robot, and human dependencies."""
        self.cfg = cfg
        self._observe_scene = observe_scene
        self._scene_estimator = scene_estimator
        self._task_allocator = task_allocator
        self._robot_executor = robot_executor
        self._human_executor = human_executor

    def plan_next_step(
        self,
        *,
        goal: str | None = None,
        current_task: str | None = None,
        available_robot_skills: Sequence[str] | None = None,
        available_human_skills: Sequence[str] | None = None,
    ) -> PlanStepDecision:
        """@brief Observe the scene and allocate the next step."""
        scene_estimate = self._scene_estimator.estimate(self._observe_scene())
        return self._task_allocator.plan_next_step(
            scene_estimate,
            goal=goal,
            current_task=current_task,
            available_robot_skills=list(available_robot_skills)
            if available_robot_skills is not None
            else None,
            available_human_skills=list(available_human_skills)
            if available_human_skills is not None
            else None,
        )

    def verify_step(self, step_name: str):
        """@brief Verify a named step against the latest observed scene."""
        return self._scene_estimator.verify_step(step_name, self._observe_scene())

    def dispatch_step(self, decision: PlanStepDecision) -> StepExecutionResult:
        """@brief Execute a robot or human decision and verify robot effects."""
        primitive = self._task_allocator.primitive_for_step(decision.step_name)

        if decision.actor == "robot":
            execution = self._robot_executor.execute(primitive)
            if not execution.success:
                return execution

            verification = self.verify_step(primitive.name)
            if not verification.success:
                return StepExecutionResult(
                    step_name=primitive.name,
                    actor="robot",
                    success=False,
                    status="FAILURE",
                    elapsed_s=execution.elapsed_s,
                    message=(
                        f"Robot step '{primitive.name}' finished execution, but scene verification failed: "
                        f"{verification.failure_reason}."
                    ),
                    observed_state=verification.observed_state,
                )

            return replace(execution, observed_state=verification.observed_state)

        return self._human_executor.execute(
            primitive,
            timeout_s=self.cfg.human_confirmation_timeout_s,
        )

    def run_until_done(
        self,
        *,
        goal: str | None = None,
        current_task: str | None = None,
        available_robot_skills: Sequence[str] | None = None,
        available_human_skills: Sequence[str] | None = None,
        max_steps: int = 8,
    ) -> SupervisorRunResult:
        """@brief Run the domain loop until `done`, `abort`, or max steps."""
        steps: list[ExecutedSupervisorStep] = []

        for _ in range(max_steps):
            decision = self.plan_next_step(
                goal=goal,
                current_task=current_task,
                available_robot_skills=available_robot_skills,
                available_human_skills=available_human_skills,
            )
            if decision.actor in {"done", "abort"}:
                return SupervisorRunResult(steps=steps, final_decision=decision)

            result = self.dispatch_step(decision)
            steps.append(ExecutedSupervisorStep(decision=decision, result=result))

            if not result.success:
                return SupervisorRunResult(
                    steps=steps,
                    final_decision=PlanStepDecision(
                        step_name=decision.step_name,
                        actor="abort",
                        reason=result.message,
                        expected_state=decision.expected_state,
                        confidence=decision.confidence,
                    ),
                )

        return SupervisorRunResult(
            steps=steps,
            final_decision=PlanStepDecision(
                step_name="",
                actor="abort",
                reason=f"Supervisor exceeded max_steps={max_steps}.",
                expected_state="DONE",
                confidence=0.0,
            ),
        )
