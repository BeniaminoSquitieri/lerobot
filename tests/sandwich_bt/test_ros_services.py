from __future__ import annotations

from sandwich_bt_supervisor.ros_services import (
    GeneratedInterfaceError,
    validate_run_named_command_service,
    validate_supervisor_services,
)


class _FakeMessageType:
    def __init_subclass__(cls, *, fields: set[str]) -> None:
        cls._fields = fields

    @classmethod
    def get_fields_and_field_types(cls):
        return dict.fromkeys(cls._fields, "mock")


class _PlanRequestOk(_FakeMessageType, fields={
    "goal",
    "current_task",
    "available_robot_skills",
    "available_human_skills",
    "first_toast_on_plate",
    "ingredient_on_first_toast",
    "second_toast_on_top",
}):
    pass


class _PlanResponseOk(_FakeMessageType, fields={"step_name", "actor", "reason", "expected_state", "confidence"}):
    pass


class _VerifyRequestOk(_FakeMessageType, fields={
    "step_name",
    "first_toast_on_plate",
    "ingredient_on_first_toast",
    "second_toast_on_top",
}):
    pass


class _VerifyResponseOk(_FakeMessageType, fields={"success", "observed_state", "failure_reason", "confidence"}):
    pass


class _PlanRequestStale(_FakeMessageType, fields={"goal", "current_task"}):
    pass


class _FakePlanServiceOk:
    Request = _PlanRequestOk
    Response = _PlanResponseOk


class _FakeVerifyServiceOk:
    Request = _VerifyRequestOk
    Response = _VerifyResponseOk


class _FakePlanServiceStale:
    Request = _PlanRequestStale
    Response = _PlanResponseOk


class _RunRequestOk(_FakeMessageType, fields={"kind", "name", "timeout_s"}):
    pass


class _RunResponseOk(_FakeMessageType, fields={"success", "status", "elapsed_s", "message"}):
    pass


class _RunRequestStale(_FakeMessageType, fields={"kind"}):
    pass


class _FakeRunNamedCommandOk:
    Request = _RunRequestOk
    Response = _RunResponseOk


class _FakeRunNamedCommandStale:
    Request = _RunRequestStale
    Response = _RunResponseOk


def test_validate_supervisor_services_accepts_expected_schema() -> None:
    validate_supervisor_services(_FakePlanServiceOk, _FakeVerifyServiceOk)


def test_validate_supervisor_services_rejects_stale_schema() -> None:
    try:
        validate_supervisor_services(_FakePlanServiceStale, _FakeVerifyServiceOk)
    except GeneratedInterfaceError as exc:
        assert "sandwich_bt_interfaces are not built or are stale" in str(exc)
        assert "available_robot_skills" in str(exc)
    else:  # pragma: no cover - explicit guard for readability
        raise AssertionError("Expected validate_supervisor_services to reject a stale request schema.")


def test_validate_run_named_command_service_accepts_expected_schema() -> None:
    validate_run_named_command_service(_FakeRunNamedCommandOk)


def test_validate_run_named_command_service_rejects_stale_schema() -> None:
    try:
        validate_run_named_command_service(_FakeRunNamedCommandStale)
    except GeneratedInterfaceError as exc:
        assert "sandwich_bt_interfaces are not built or are stale" in str(exc)
        assert "timeout_s" in str(exc)
    else:  # pragma: no cover - explicit guard for readability
        raise AssertionError("Expected validate_run_named_command_service to reject a stale request schema.")
