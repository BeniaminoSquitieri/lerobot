from __future__ import annotations

import pytest

from sandwich_bt_python.simulation import (
    MockRunNamedCommandRequest,
    build_demo_stack,
    default_command_sequence,
    parse_command_spec,
)


def test_mock_service_runs_full_demo_sequence() -> None:
    service = build_demo_stack()
    requests = default_command_sequence()

    responses = [service.handle_request(request) for request in requests]

    assert all(response.success for response in responses)
    assert [response.status for response in responses] == ["SUCCESS"] * len(requests)

    robot = service.executor.robot
    observation = robot.get_observation()

    assert robot.reset_count == 1
    assert len(robot.sent_actions) > 0
    assert observation["gripper"] == pytest.approx(0.0)
    assert observation["position.z"] > 0.0


def test_unknown_command_kind_returns_error() -> None:
    service = build_demo_stack()

    response = service.handle_request(MockRunNamedCommandRequest(kind="bogus", name="noop"))

    assert not response.success
    assert response.status == "ERROR"
    assert "Unsupported command kind" in response.message


def test_recovery_kind_is_not_supported() -> None:
    service = build_demo_stack(use_delta_actions=True)

    response = service.handle_request(MockRunNamedCommandRequest(kind="recovery", name="recover_place_first_toast"))

    assert not response.success
    assert response.status == "ERROR"
    assert "Unsupported command kind" in response.message


def test_parse_command_spec_with_timeout_override() -> None:
    request = parse_command_spec("skill:place_first_toast:1.25")

    assert request.kind == "skill"
    assert request.name == "place_first_toast"
    assert request.timeout_s == pytest.approx(1.25)
