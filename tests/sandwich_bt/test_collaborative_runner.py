from __future__ import annotations

from types import SimpleNamespace

from sandwich_bt_supervisor.collaborative_runner import (
    CollaborativeRunnerExitCode,
    SupervisorClientProtocol,
    build_mock_collaborative_runner,
    exit_code_for_result,
    main as collaborative_runner_main,
)
from sandwich_bt_supervisor.planner_schema import PlanStepDecision, StepVerification
from sandwich_bt_supervisor.server import SupervisorServiceBackend
from sandwich_bt_supervisor.simulation import make_demo_supervisor_config


class BackendBackedSupervisorClient(SupervisorClientProtocol):
    def __init__(self) -> None:
        self.backend = SupervisorServiceBackend(make_demo_supervisor_config())

    def plan_next_action(
        self,
        *,
        goal: str,
        current_task: str,
        available_robot_skills: list[str],
        available_human_skills: list[str],
        observation,
    ):
        return self.backend.plan_next_action(
            SimpleNamespace(
                goal=goal,
                current_task=current_task,
                available_robot_skills=available_robot_skills,
                available_human_skills=available_human_skills,
                first_toast_on_plate=observation.first_toast_on_plate,
                ingredient_on_first_toast=observation.ingredient_on_first_toast,
                second_toast_on_top=observation.second_toast_on_top,
            )
        )

    def verify_step(self, *, step_name: str, observation):
        return self.backend.verify_step(
            SimpleNamespace(
                step_name=step_name,
                first_toast_on_plate=observation.first_toast_on_plate,
                ingredient_on_first_toast=observation.ingredient_on_first_toast,
                second_toast_on_top=observation.second_toast_on_top,
            )
        )


class InvalidDecisionSupervisorClient(SupervisorClientProtocol):
    def plan_next_action(
        self,
        *,
        goal: str,
        current_task: str,
        available_robot_skills: list[str],
        available_human_skills: list[str],
        observation,
    ):
        del goal, current_task, available_robot_skills, available_human_skills, observation
        return PlanStepDecision(
            step_name="pour_ingredient",
            actor="vlm",  # type: ignore[arg-type]
            reason="invalid test actor",
            expected_state="DONE",
            confidence=1.0,
        )

    def verify_step(self, *, step_name: str, observation):
        del step_name, observation
        return StepVerification(
            success=True,
            observed_state="unused",
            failure_reason="",
            confidence=1.0,
        )


def test_collaborative_runner_reaches_done_with_mock_scene() -> None:
    cfg = make_demo_supervisor_config()
    stack = build_mock_collaborative_runner(
        cfg=cfg,
        supervisor_client=BackendBackedSupervisorClient(),
    )

    result = stack.runner.run_until_done()

    assert result.final_actor == "done"
    assert [step.decision.step_name for step in result.steps] == [
        "place_first_toast",
        "pour_ingredient",
        "place_second_toast",
    ]
    assert all(step.verification.success for step in result.steps)
    assert stack.skill_service is not None
    assert [(request.kind, request.name) for request in stack.skill_service.request_log] == [
        ("recovery", "recover_place_first_toast"),
        ("skill", "place_first_toast"),
        ("recovery", "recover_place_second_toast"),
        ("skill", "place_second_toast"),
    ]


def test_collaborative_runner_aborts_when_human_confirmation_is_denied() -> None:
    cfg = make_demo_supervisor_config()
    stack = build_mock_collaborative_runner(
        cfg=cfg,
        supervisor_client=BackendBackedSupervisorClient(),
        deny_human_confirmation=True,
    )

    result = stack.runner.run_until_done()

    assert result.final_actor == "abort"
    assert [step.decision.step_name for step in result.steps] == [
        "place_first_toast",
        "pour_ingredient",
    ]
    assert not result.steps[-1].verification.success
    assert "ingredient is not visible" in result.final_reason


def test_collaborative_runner_rejects_invalid_supervisor_actor() -> None:
    cfg = make_demo_supervisor_config()
    stack = build_mock_collaborative_runner(
        cfg=cfg,
        supervisor_client=InvalidDecisionSupervisorClient(),
    )

    try:
        stack.runner.run_until_done()
    except ValueError as exc:
        assert "unsupported actor" in str(exc)
    else:  # pragma: no cover - explicit guard for readability
        raise AssertionError("Expected CollaborativeRunner to reject an invalid supervisor actor.")


def test_collaborative_runner_exit_codes_follow_final_actor() -> None:
    cfg = make_demo_supervisor_config()

    done_stack = build_mock_collaborative_runner(
        cfg=cfg,
        supervisor_client=BackendBackedSupervisorClient(),
    )
    abort_stack = build_mock_collaborative_runner(
        cfg=cfg,
        supervisor_client=BackendBackedSupervisorClient(),
        deny_human_confirmation=True,
    )

    assert exit_code_for_result(done_stack.runner.run_until_done()) == int(CollaborativeRunnerExitCode.DONE)
    assert exit_code_for_result(abort_stack.runner.run_until_done()) == int(CollaborativeRunnerExitCode.ABORT)


def test_collaborative_runner_main_requires_mock_scene_flag() -> None:
    assert collaborative_runner_main([]) == int(CollaborativeRunnerExitCode.INVALID_RUNTIME)
