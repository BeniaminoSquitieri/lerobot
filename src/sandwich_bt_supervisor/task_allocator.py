"""Closed-set task allocation for the collaborative sandwich supervisor."""

from __future__ import annotations

from .planner_schema import PlanStepDecision, SceneEstimate, SupervisorConfig, TaskPrimitive


class SandwichTaskAllocator:
    def __init__(self, cfg: SupervisorConfig) -> None:
        self.cfg = cfg
        self._primitives_by_name = {primitive.name: primitive for primitive in cfg.task_primitives}
        self._primitives_by_state = {primitive.required_state: primitive for primitive in cfg.task_primitives}

    def primitive_for_step(self, step_name: str) -> TaskPrimitive:
        return self._primitives_by_name[step_name]

    def plan_next_step(
        self,
        scene_estimate: SceneEstimate,
        *,
        goal: str | None = None,
        current_task: str | None = None,
        available_robot_skills: list[str] | None = None,
        available_human_skills: list[str] | None = None,
    ) -> PlanStepDecision:
        goal_name = goal or self.cfg.goal
        task_name = current_task or self.cfg.current_task
        robot_skills = set(
            self.cfg.available_robot_skills if available_robot_skills is None else available_robot_skills
        )
        human_skills = set(
            self.cfg.available_human_skills if available_human_skills is None else available_human_skills
        )

        if scene_estimate.phase == "DONE":
            return PlanStepDecision(
                step_name="",
                actor="done",
                reason=f"Goal '{goal_name}' is already satisfied.",
                expected_state="DONE",
                confidence=scene_estimate.confidence,
            )

        primitive = self._primitives_by_state[scene_estimate.phase]

        if primitive.actor == "robot":
            assert primitive.robot_skill is not None
            if primitive.robot_skill not in robot_skills:
                return PlanStepDecision(
                    step_name=primitive.name,
                    actor="abort",
                    reason=(
                        f"Task '{task_name}' needs robot skill '{primitive.robot_skill}', "
                        "but that skill is not available."
                    ),
                    expected_state=scene_estimate.phase,
                    confidence=scene_estimate.confidence,
                )
            reason = (
                f"{scene_estimate.observed_state}. Assign '{primitive.name}' to the robot "
                f"to move toward '{primitive.expected_state}'."
            )
        else:
            if primitive.name not in human_skills:
                return PlanStepDecision(
                    step_name=primitive.name,
                    actor="abort",
                    reason=(
                        f"Task '{task_name}' needs human step '{primitive.name}', "
                        "but no human executor is available."
                    ),
                    expected_state=scene_estimate.phase,
                    confidence=scene_estimate.confidence,
                )
            reason = (
                f"{scene_estimate.observed_state}. Assign '{primitive.name}' to the human "
                f"to move toward '{primitive.expected_state}'."
            )

        return PlanStepDecision(
            step_name=primitive.name,
            actor=primitive.actor,
            reason=reason,
            expected_state=primitive.expected_state,
            confidence=scene_estimate.confidence,
        )
