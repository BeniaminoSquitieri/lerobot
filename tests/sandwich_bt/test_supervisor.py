from __future__ import annotations

from sandwich_bt_python.simulation import MockRunNamedCommandResponse
from sandwich_bt_supervisor.simulation import build_demo_supervisor_stack


def test_collaborative_supervisor_runs_robot_human_robot_sequence() -> None:
    stack = build_demo_supervisor_stack()

    result = stack.supervisor.run_until_done()

    assert [step.decision.actor for step in result.steps] == ["robot", "human", "robot"]
    assert [step.decision.step_name for step in result.steps] == [
        "place_first_toast",
        "pour_ingredient",
        "place_second_toast",
    ]
    assert all(step.result.success for step in result.steps)
    assert result.final_decision.actor == "done"
    assert stack.scene.first_toast_on_plate
    assert stack.scene.ingredient_on_first_toast
    assert stack.scene.second_toast_on_top
    assert stack.human.instructions == ["Pour the ingredient on the first toast."]
    assert [(request.kind, request.name) for request in stack.service.request_log] == [
        ("recovery", "recover_place_first_toast"),
        ("skill", "place_first_toast"),
        ("recovery", "recover_place_second_toast"),
        ("skill", "place_second_toast"),
    ]


def test_collaborative_supervisor_aborts_when_human_does_not_confirm() -> None:
    stack = build_demo_supervisor_stack(auto_confirm_human=False)

    result = stack.supervisor.run_until_done()

    assert [step.decision.step_name for step in result.steps] == [
        "place_first_toast",
        "pour_ingredient",
    ]
    assert result.steps[-1].result.status == "FAILURE"
    assert not result.steps[-1].result.success
    assert result.final_decision.actor == "abort"
    assert not stack.scene.ingredient_on_first_toast


def test_next_step_is_done_when_scene_is_already_complete() -> None:
    stack = build_demo_supervisor_stack()
    stack.scene.first_toast_on_plate = True
    stack.scene.ingredient_on_first_toast = True
    stack.scene.second_toast_on_top = True

    decision = stack.supervisor.plan_next_step()

    assert decision.actor == "done"
    assert decision.expected_state == "DONE"


def test_robot_bt_subtree_retries_after_a_scripted_skill_failure() -> None:
    stack = build_demo_supervisor_stack(
        scripted_responses={
            ("skill", "place_first_toast"): [
                MockRunNamedCommandResponse(
                    success=False,
                    status="FAILURE",
                    elapsed_s=0.4,
                    message="Scripted first-attempt failure.",
                )
            ]
        }
    )

    primitive = next(
        primitive for primitive in stack.cfg.task_primitives if primitive.name == "place_first_toast"
    )
    result = stack.robot_executor.execute(primitive)

    assert result.success
    assert stack.scene.first_toast_on_plate
    assert [(request.kind, request.name) for request in stack.service.request_log] == [
        ("recovery", "recover_place_first_toast"),
        ("skill", "place_first_toast"),
        ("recovery", "recover_place_first_toast"),
        ("skill", "place_first_toast"),
    ]


def test_robot_bt_subtree_fails_after_exhausting_all_attempts() -> None:
    stack = build_demo_supervisor_stack(
        scripted_responses={
            ("skill", "place_first_toast"): [
                MockRunNamedCommandResponse(False, "FAILURE", 0.4, "Attempt 1 failed."),
                MockRunNamedCommandResponse(False, "FAILURE", 0.4, "Attempt 2 failed."),
                MockRunNamedCommandResponse(False, "FAILURE", 0.4, "Attempt 3 failed."),
            ]
        }
    )

    primitive = next(
        primitive for primitive in stack.cfg.task_primitives if primitive.name == "place_first_toast"
    )
    result = stack.robot_executor.execute(primitive)

    assert not result.success
    assert result.status == "FAILURE"
    assert not stack.scene.first_toast_on_plate
    assert "failed after 3 attempts" in result.message
