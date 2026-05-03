"""Closed-set schemas for collaborative sandwich supervision."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ScenePhase = Literal["NEED_FIRST_TOAST", "NEED_POURING", "NEED_SECOND_TOAST", "DONE"]
DecisionActor = Literal["robot", "human", "done", "abort"]

_ACTIVE_SCENE_PHASES = {"NEED_FIRST_TOAST", "NEED_POURING", "NEED_SECOND_TOAST"}
_VALID_SCENE_PHASES = _ACTIVE_SCENE_PHASES | {"DONE"}
_VALID_PRIMITIVE_ACTORS = {"robot", "human"}


@dataclass
class TaskPrimitive:
    name: str
    required_state: ScenePhase
    actor: Literal["robot", "human"]
    expected_state: ScenePhase
    success_condition: str
    difficulty: str = "unspecified"
    robot_skill: str | None = None
    bt_xml_path: str | None = None
    recovery: str | None = None
    human_instruction: str | None = None

    def __post_init__(self) -> None:
        if self.required_state not in _ACTIVE_SCENE_PHASES:
            raise ValueError(
                f"Primitive '{self.name}' must target one of {sorted(_ACTIVE_SCENE_PHASES)}, "
                f"got '{self.required_state}'."
            )
        if self.expected_state not in _VALID_SCENE_PHASES:
            raise ValueError(
                f"Primitive '{self.name}' expected_state must be one of {sorted(_VALID_SCENE_PHASES)}, "
                f"got '{self.expected_state}'."
            )
        if self.actor not in _VALID_PRIMITIVE_ACTORS:
            raise ValueError(
                f"Primitive '{self.name}' actor must be one of {sorted(_VALID_PRIMITIVE_ACTORS)}, "
                f"got '{self.actor}'."
            )
        if self.actor == "robot":
            self.robot_skill = self.robot_skill or self.name
        if self.actor == "human":
            self.human_instruction = self.human_instruction or self.name.replace("_", " ")
        if self.actor == "robot" and self.human_instruction is not None:
            raise ValueError(f"Robot primitive '{self.name}' must not define human_instruction.")
        if self.actor == "human" and self.robot_skill is not None:
            raise ValueError(f"Human primitive '{self.name}' must not define robot_skill.")
        if self.actor == "human" and self.bt_xml_path is not None:
            raise ValueError(f"Human primitive '{self.name}' must not define bt_xml_path.")


@dataclass
class SupervisorServiceConfig:
    plan_service_name: str = "/sandwich_supervisor/next_action"
    verify_service_name: str = "/sandwich_supervisor/verify_step"


@dataclass
class SupervisorConfig:
    goal: str = "make_sandwich"
    current_task: str = "sandwich_collaborative"
    task_primitives: list[TaskPrimitive] = field(default_factory=list)
    available_robot_skills: list[str] = field(default_factory=list)
    available_human_skills: list[str] = field(default_factory=list)
    human_confirmation_timeout_s: float = 30.0
    service: SupervisorServiceConfig = field(default_factory=SupervisorServiceConfig)

    def __post_init__(self) -> None:
        if not self.goal:
            raise ValueError("goal must not be empty.")
        if not self.current_task:
            raise ValueError("current_task must not be empty.")
        if not self.task_primitives:
            raise ValueError("At least one task primitive must be configured.")
        if self.human_confirmation_timeout_s <= 0:
            raise ValueError("human_confirmation_timeout_s must be > 0.")

        primitives_by_name = {primitive.name: primitive for primitive in self.task_primitives}
        if len(primitives_by_name) != len(self.task_primitives):
            raise ValueError("Primitive names must be unique.")

        primitives_by_state = {primitive.required_state: primitive for primitive in self.task_primitives}
        if len(primitives_by_state) != len(self.task_primitives):
            raise ValueError("Each scene state must map to exactly one closed-set primitive.")

        missing_states = _ACTIVE_SCENE_PHASES.difference(primitives_by_state)
        if missing_states:
            raise ValueError(
                f"Closed-set supervisor config is missing primitives for states: {sorted(missing_states)}."
            )


@dataclass(frozen=True)
class SceneEstimate:
    phase: ScenePhase
    observed_state: str
    confidence: float = 1.0


@dataclass(frozen=True)
class PlanStepDecision:
    step_name: str
    actor: DecisionActor
    reason: str
    expected_state: ScenePhase
    confidence: float = 1.0


@dataclass(frozen=True)
class StepVerification:
    success: bool
    observed_state: str
    failure_reason: str
    confidence: float = 1.0


@dataclass(frozen=True)
class StepExecutionResult:
    step_name: str
    actor: Literal["robot", "human"]
    success: bool
    status: str
    elapsed_s: float
    message: str
    observed_state: str = ""


@dataclass(frozen=True)
class ExecutedSupervisorStep:
    decision: PlanStepDecision
    result: StepExecutionResult


@dataclass(frozen=True)
class SupervisorRunResult:
    steps: list[ExecutedSupervisorStep]
    final_decision: PlanStepDecision
