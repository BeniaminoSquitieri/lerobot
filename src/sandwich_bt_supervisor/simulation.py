"""Hardware-free simulation harness for the collaborative supervisor."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

from sandwich_bt_python.simulation import (
    MockRunNamedCommandResponse,
    MockRunNamedCommandService,
    MockSkillCommandExecutor,
    build_demo_stack,
)

from .bt_executor import BtXmlRobotExecutor, default_subtree_path
from .human_interface import HumanCommandExecutor
from .planner_schema import SupervisorConfig, TaskPrimitive
from .scene_state import SandwichSceneEstimator, SandwichSceneObservation
from .task_allocator import SandwichTaskAllocator
from .vlm_supervisor import CollaborativeSandwichSupervisor


@dataclass
class MockSandwichScene:
    first_toast_on_plate: bool = False
    ingredient_on_first_toast: bool = False
    second_toast_on_top: bool = False
    events: list[str] = field(default_factory=list)

    def observe(self) -> SandwichSceneObservation:
        return SandwichSceneObservation(
            first_toast_on_plate=self.first_toast_on_plate,
            ingredient_on_first_toast=self.ingredient_on_first_toast,
            second_toast_on_top=self.second_toast_on_top,
        )


class MockHumanParticipant:
    def __init__(self, scene: MockSandwichScene, *, auto_confirm: bool = True) -> None:
        self.scene = scene
        self.auto_confirm = auto_confirm
        self.instructions: list[str] = []

    def send_instruction(self, instruction: str) -> None:
        self.instructions.append(instruction)
        self.scene.events.append(f"instruction:{instruction}")

    def confirm(self, primitive: TaskPrimitive, timeout_s: float) -> bool:
        del timeout_s
        if not self.auto_confirm:
            self.scene.events.append(f"human_rejected:{primitive.name}")
            return False

        self.scene.events.append(f"human_confirmed:{primitive.name}")
        if primitive.name == "pour_ingredient":
            self.scene.ingredient_on_first_toast = True
        return True


class MockRobotSceneEffects:
    def __init__(self, scene: MockSandwichScene) -> None:
        self.scene = scene

    def mark_completed(self, primitive_name: str) -> None:
        if primitive_name == "place_first_toast":
            self.scene.first_toast_on_plate = True
        elif primitive_name == "place_second_toast":
            self.scene.second_toast_on_top = True
        self.scene.events.append(f"robot_completed:{primitive_name}")


@dataclass
class MockCollaborativeSupervisorStack:
    cfg: SupervisorConfig
    scene: MockSandwichScene
    human: MockHumanParticipant
    supervisor: CollaborativeSandwichSupervisor
    robot_executor: BtXmlRobotExecutor
    service: MockRunNamedCommandService
    command_executor: MockSkillCommandExecutor


def make_demo_supervisor_config() -> SupervisorConfig:
    return SupervisorConfig(
        goal="make_sandwich",
        current_task="sandwich_collaborative",
        available_robot_skills=["place_first_toast", "place_second_toast"],
        available_human_skills=["pour_ingredient"],
        human_confirmation_timeout_s=15.0,
        task_primitives=[
            TaskPrimitive(
                name="place_first_toast",
                required_state="NEED_FIRST_TOAST",
                actor="robot",
                robot_skill="place_first_toast",
                bt_xml_path=str(default_subtree_path("place_first_toast_subtree.xml")),
                recovery="recover_place_first_toast",
                difficulty="easy",
                success_condition="first toast is on plate",
                expected_state="NEED_POURING",
            ),
            TaskPrimitive(
                name="pour_ingredient",
                required_state="NEED_POURING",
                actor="human",
                difficulty="hard",
                human_instruction="Pour the ingredient on the first toast.",
                success_condition="ingredient is visible on first toast",
                expected_state="NEED_SECOND_TOAST",
            ),
            TaskPrimitive(
                name="place_second_toast",
                required_state="NEED_SECOND_TOAST",
                actor="robot",
                robot_skill="place_second_toast",
                bt_xml_path=str(default_subtree_path("place_second_toast_subtree.xml")),
                recovery="recover_place_second_toast",
                difficulty="easy",
                success_condition="second toast is on top",
                expected_state="DONE",
            ),
        ],
    )


def build_demo_supervisor_stack(
    cfg: SupervisorConfig | None = None,
    *,
    auto_confirm_human: bool = True,
    use_delta_actions: bool = False,
    scripted_responses: dict[tuple[str, str], list[MockRunNamedCommandResponse]] | None = None,
) -> MockCollaborativeSupervisorStack:
    supervisor_cfg = cfg if cfg is not None else make_demo_supervisor_config()
    service = build_demo_stack(
        use_delta_actions=use_delta_actions,
        scripted_responses=scripted_responses,
    )
    scene = MockSandwichScene()
    human = MockHumanParticipant(scene, auto_confirm=auto_confirm_human)
    scene_estimator = SandwichSceneEstimator()
    task_allocator = SandwichTaskAllocator(supervisor_cfg)
    command_executor = service.executor
    robot_executor = BtXmlRobotExecutor(
        service=service,
        on_step_success=MockRobotSceneEffects(scene).mark_completed,
    )
    human_executor = HumanCommandExecutor(
        observe_scene=scene.observe,
        verify_step=scene_estimator.verify_step,
        send_instruction=human.send_instruction,
        wait_for_confirmation=human.confirm,
    )
    supervisor = CollaborativeSandwichSupervisor(
        cfg=supervisor_cfg,
        observe_scene=scene.observe,
        scene_estimator=scene_estimator,
        task_allocator=task_allocator,
        robot_executor=robot_executor,
        human_executor=human_executor,
    )
    return MockCollaborativeSupervisorStack(
        cfg=supervisor_cfg,
        scene=scene,
        human=human,
        supervisor=supervisor,
        robot_executor=robot_executor,
        service=service,
        command_executor=command_executor,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the collaborative sandwich supervisor demo.")
    parser.add_argument(
        "--deny-human-confirmation",
        action="store_true",
        help="Simulate a human that never confirms the requested handoff.",
    )
    parser.add_argument(
        "--use-delta-actions",
        action="store_true",
        help="Use the mock delta-action robot backend for the robot skill executor.",
    )
    args = parser.parse_args()

    stack = build_demo_supervisor_stack(
        auto_confirm_human=not args.deny_human_confirmation,
        use_delta_actions=args.use_delta_actions,
    )
    result = stack.supervisor.run_until_done()

    for step in result.steps:
        print(
            f"{step.decision.actor}:{step.decision.step_name} -> {step.result.status} {step.result.message}"
        )
    for command in stack.robot_executor.command_history:
        print(
            "bt_command="
            f"{command.attempt_index}:{command.request.kind}:{command.request.name}"
            f" -> {command.response.status}"
        )
    print(f"final -> {result.final_decision.actor} ({result.final_decision.reason})")


if __name__ == "__main__":
    main()
