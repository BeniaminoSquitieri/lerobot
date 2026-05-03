from __future__ import annotations

from types import SimpleNamespace

import pytest

from sandwich_bt_supervisor.server import SandwichSupervisorServer, SupervisorServiceBackend
from sandwich_bt_supervisor.simulation import make_demo_supervisor_config


def _plan_request(
    *,
    goal: str = "make_sandwich",
    current_task: str = "sandwich_collaborative",
    available_robot_skills: list[str] | None = None,
    available_human_skills: list[str] | None = None,
    first_toast_on_plate: bool = False,
    ingredient_on_first_toast: bool = False,
    second_toast_on_top: bool = False,
):
    return SimpleNamespace(
        goal=goal,
        current_task=current_task,
        available_robot_skills=available_robot_skills or ["place_first_toast", "place_second_toast"],
        available_human_skills=available_human_skills or ["pour_ingredient"],
        first_toast_on_plate=first_toast_on_plate,
        ingredient_on_first_toast=ingredient_on_first_toast,
        second_toast_on_top=second_toast_on_top,
    )


def _verify_request(
    *,
    step_name: str,
    first_toast_on_plate: bool = False,
    ingredient_on_first_toast: bool = False,
    second_toast_on_top: bool = False,
):
    return SimpleNamespace(
        step_name=step_name,
        first_toast_on_plate=first_toast_on_plate,
        ingredient_on_first_toast=ingredient_on_first_toast,
        second_toast_on_top=second_toast_on_top,
    )


def test_supervisor_server_registers_plan_and_verify_services(monkeypatch: pytest.MonkeyPatch) -> None:
    rclpy = pytest.importorskip("rclpy")
    cfg = make_demo_supervisor_config()
    created_services: list[str] = []
    monkeypatch.setenv("ROS_LOG_DIR", "/tmp/ros_logs")

    class FakePlanNextStep:
        pass

    class FakeVerifyStep:
        pass

    monkeypatch.setattr(
        "sandwich_bt_supervisor.server.load_supervisor_services",
        lambda: (FakePlanNextStep, FakeVerifyStep),
    )

    def fake_create_service(self, service_type, service_name, callback):
        del service_type, callback
        created_services.append(service_name)
        return object()

    monkeypatch.setattr(SandwichSupervisorServer, "create_service", fake_create_service, raising=False)

    if not rclpy.ok():
        rclpy.init()

    server_node = SandwichSupervisorServer(cfg=cfg)
    try:
        assert created_services == [
            cfg.service.plan_service_name,
            cfg.service.verify_service_name,
        ]
    finally:
        server_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def test_plan_next_step_backend_returns_first_robot_action_for_initial_scene() -> None:
    backend = SupervisorServiceBackend(make_demo_supervisor_config())

    decision = backend.plan_next_action(_plan_request())

    assert decision.step_name == "place_first_toast"
    assert decision.actor == "robot"


def test_verify_step_backend_rejects_missing_ingredient_after_pour() -> None:
    backend = SupervisorServiceBackend(make_demo_supervisor_config())

    verification = backend.verify_step(
        _verify_request(
            step_name="pour_ingredient",
            first_toast_on_plate=True,
            ingredient_on_first_toast=False,
            second_toast_on_top=False,
        )
    )

    assert not verification.success
    assert verification.failure_reason != ""
