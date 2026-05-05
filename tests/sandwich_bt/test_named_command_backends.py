from __future__ import annotations

import pytest

from sandwich_bt_supervisor.collaborative_runner import (
    CollaborativeRunnerExitCode,
    SupervisorClientProtocol,
    build_mock_collaborative_runner,
    main as collaborative_runner_main,
)
from sandwich_bt_supervisor.named_command_backends import (
    NamedCommandResult,
    NamedCommandServiceUnavailableError,
    Ros2NamedCommandBackend,
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
    ) -> PlanStepDecision:
        from types import SimpleNamespace

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

    def verify_step(self, *, step_name: str, observation) -> StepVerification:
        from types import SimpleNamespace

        return self.backend.verify_step(
            SimpleNamespace(
                step_name=step_name,
                first_toast_on_plate=observation.first_toast_on_plate,
                ingredient_on_first_toast=observation.ingredient_on_first_toast,
                second_toast_on_top=observation.second_toast_on_top,
            )
        )


class ScriptedNamedCommandBackend:
    def __init__(self, scripted_results: dict[tuple[str, str], list[NamedCommandResult]] | None = None) -> None:
        self.scripted_results = scripted_results if scripted_results is not None else {}
        self.request_log: list[tuple[str, str, float]] = []

    def run_named_command(
        self,
        *,
        kind: str,
        name: str,
        timeout_s: float,
    ) -> NamedCommandResult:
        self.request_log.append((kind, name, timeout_s))
        scripted_queue = self.scripted_results.get((kind, name))
        if scripted_queue:
            return scripted_queue.pop(0)
        return NamedCommandResult(
            success=True,
            status="SUCCESS",
            elapsed_s=0.4,
            message=f"{kind}:{name} completed.",
        )


def test_runner_custom_command_backend_success_path_reaches_done() -> None:
    backend = ScriptedNamedCommandBackend()
    stack = build_mock_collaborative_runner(
        cfg=make_demo_supervisor_config(),
        supervisor_client=BackendBackedSupervisorClient(),
        command_backend=backend,
    )

    result = stack.runner.run_until_done()

    assert result.final_actor == "done"
    assert backend.request_log == [
        ("recovery", "recover_place_first_toast", 0.0),
        ("skill", "place_first_toast", 30.0),
        ("recovery", "recover_place_second_toast", 0.0),
        ("skill", "place_second_toast", 0.0),
    ]


def test_runner_custom_command_backend_failure_path_aborts() -> None:
    backend = ScriptedNamedCommandBackend(
        scripted_results={
            ("skill", "place_first_toast"): [
                NamedCommandResult(False, "FAILURE", 0.4, "Attempt 1 failed."),
                NamedCommandResult(False, "FAILURE", 0.4, "Attempt 2 failed."),
                NamedCommandResult(False, "FAILURE", 0.4, "Attempt 3 failed."),
            ]
        }
    )
    stack = build_mock_collaborative_runner(
        cfg=make_demo_supervisor_config(),
        supervisor_client=BackendBackedSupervisorClient(),
        command_backend=backend,
    )

    result = stack.runner.run_until_done()

    assert result.final_actor == "abort"
    assert result.steps[0].decision.step_name == "place_first_toast"
    assert result.steps[0].execution.status == "FAILURE"


def test_ros2_named_command_backend_missing_service_raises() -> None:
    class FakeClient:
        def wait_for_service(self, timeout_sec: float) -> bool:
            del timeout_sec
            return False

    backend = Ros2NamedCommandBackend.__new__(Ros2NamedCommandBackend)
    backend.service_name = "/sandwich_bt/run_command"
    backend._client = FakeClient()

    with pytest.raises(NamedCommandServiceUnavailableError):
        backend.wait_for_service()


def test_collaborative_runner_main_returns_exit_2_when_ros2_named_command_service_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSupervisorClient:
        def wait_for_services(self) -> None:
            return None

        def destroy_node(self) -> None:
            return None

    monkeypatch.setattr(
        "sandwich_bt_supervisor.collaborative_runner.load_supervisor_config",
        lambda _path: make_demo_supervisor_config(),
    )
    monkeypatch.setattr("sandwich_bt_supervisor.collaborative_runner.SupervisorRos2Client", lambda _cfg: FakeSupervisorClient())
    monkeypatch.setattr("sandwich_bt_supervisor.collaborative_runner.rclpy.ok", lambda: True)
    monkeypatch.setattr("sandwich_bt_supervisor.collaborative_runner.rclpy.shutdown", lambda: None)

    def _raise_missing_backend(**_kwargs):
        raise NamedCommandServiceUnavailableError("missing /sandwich_bt/run_command")

    monkeypatch.setattr(
        "sandwich_bt_supervisor.collaborative_runner.build_named_command_backend",
        _raise_missing_backend,
    )

    assert collaborative_runner_main(["--mock-scene", "--robot-backend", "ros2"]) == int(
        CollaborativeRunnerExitCode.SERVICE_UNAVAILABLE
    )
