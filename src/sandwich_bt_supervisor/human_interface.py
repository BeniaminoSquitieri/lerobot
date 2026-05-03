"""Human-step execution with explicit confirmation and scene verification."""

from __future__ import annotations

from collections.abc import Callable

from .planner_schema import StepExecutionResult, StepVerification, TaskPrimitive
from .scene_state import SandwichSceneObservation


class HumanCommandExecutor:
    def __init__(
        self,
        *,
        observe_scene: Callable[[], SandwichSceneObservation],
        verify_step: Callable[[str, SandwichSceneObservation], StepVerification],
        send_instruction: Callable[[str], None] | None = None,
        wait_for_confirmation: Callable[[TaskPrimitive, float], bool] | None = None,
    ) -> None:
        self._observe_scene = observe_scene
        self._verify_step = verify_step
        self._send_instruction = send_instruction or (lambda _instruction: None)
        self._wait_for_confirmation = wait_for_confirmation or (lambda _primitive, _timeout_s: True)

    def execute(self, primitive: TaskPrimitive, timeout_s: float) -> StepExecutionResult:
        assert primitive.human_instruction is not None
        self._send_instruction(primitive.human_instruction)

        confirmed = self._wait_for_confirmation(primitive, timeout_s)
        if not confirmed:
            observation = self._observe_scene()
            return StepExecutionResult(
                step_name=primitive.name,
                actor="human",
                success=False,
                status="FAILURE",
                elapsed_s=0.0,
                message=f"Human step '{primitive.name}' was not confirmed within {timeout_s:.1f}s.",
                observed_state=self._verify_step(primitive.name, observation).observed_state,
            )

        observation = self._observe_scene()
        verification = self._verify_step(primitive.name, observation)
        if not verification.success:
            return StepExecutionResult(
                step_name=primitive.name,
                actor="human",
                success=False,
                status="FAILURE",
                elapsed_s=0.0,
                message=(
                    f"Human step '{primitive.name}' was confirmed, but scene verification failed: "
                    f"{verification.failure_reason}."
                ),
                observed_state=verification.observed_state,
            )

        return StepExecutionResult(
            step_name=primitive.name,
            actor="human",
            success=True,
            status="SUCCESS",
            elapsed_s=0.0,
            message=f"Human step '{primitive.name}' completed and was verified.",
            observed_state=verification.observed_state,
        )
