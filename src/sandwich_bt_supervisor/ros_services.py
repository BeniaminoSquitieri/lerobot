"""Helpers for loading generated ROS2 service interfaces for the supervisor."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PLAN_REQUEST_FIELDS = {
    "goal",
    "current_task",
    "available_robot_skills",
    "available_human_skills",
    "first_toast_on_plate",
    "ingredient_on_first_toast",
    "second_toast_on_top",
}
_PLAN_RESPONSE_FIELDS = {
    "step_name",
    "actor",
    "reason",
    "expected_state",
    "confidence",
}
_VERIFY_REQUEST_FIELDS = {
    "step_name",
    "first_toast_on_plate",
    "ingredient_on_first_toast",
    "second_toast_on_top",
}
_VERIFY_RESPONSE_FIELDS = {
    "success",
    "observed_state",
    "failure_reason",
    "confidence",
}
_RUN_REQUEST_FIELDS = {
    "kind",
    "name",
    "timeout_s",
}
_RUN_RESPONSE_FIELDS = {
    "success",
    "status",
    "elapsed_s",
    "message",
}


class GeneratedInterfaceError(RuntimeError):
    """Raised when generated ROS2 interfaces are missing or stale."""


def _build_rebuild_message(details: str) -> str:
    return (
        "sandwich_bt_interfaces are not built or are stale. "
        f"{details} "
        "Run: colcon build --base-paths src --packages-select sandwich_bt_interfaces "
        "&& source install/setup.bash"
    )


def _get_message_fields(message_type) -> set[str]:
    field_getter = getattr(message_type, "get_fields_and_field_types", None)
    if field_getter is None:
        raise GeneratedInterfaceError(
            _build_rebuild_message(
                f"Generated type '{message_type.__name__}' does not expose get_fields_and_field_types()."
            )
        )
    return set(field_getter().keys())


def _validate_message_fields(
    *,
    service_name: str,
    message_name: str,
    message_type,
    required_fields: set[str],
) -> None:
    actual_fields = _get_message_fields(message_type)
    missing_fields = sorted(required_fields - actual_fields)
    if missing_fields:
        raise GeneratedInterfaceError(
            _build_rebuild_message(
                f"{service_name}.{message_name} is missing fields: {', '.join(missing_fields)}."
            )
        )


def validate_supervisor_services(plan_service, verify_service) -> None:
    _validate_message_fields(
        service_name="PlanNextStep",
        message_name="Request",
        message_type=plan_service.Request,
        required_fields=_PLAN_REQUEST_FIELDS,
    )
    _validate_message_fields(
        service_name="PlanNextStep",
        message_name="Response",
        message_type=plan_service.Response,
        required_fields=_PLAN_RESPONSE_FIELDS,
    )
    _validate_message_fields(
        service_name="VerifyStep",
        message_name="Request",
        message_type=verify_service.Request,
        required_fields=_VERIFY_REQUEST_FIELDS,
    )
    _validate_message_fields(
        service_name="VerifyStep",
        message_name="Response",
        message_type=verify_service.Response,
        required_fields=_VERIFY_RESPONSE_FIELDS,
    )


def validate_run_named_command_service(run_named_command_service) -> None:
    _validate_message_fields(
        service_name="RunNamedCommand",
        message_name="Request",
        message_type=run_named_command_service.Request,
        required_fields=_RUN_REQUEST_FIELDS,
    )
    _validate_message_fields(
        service_name="RunNamedCommand",
        message_name="Response",
        message_type=run_named_command_service.Response,
        required_fields=_RUN_RESPONSE_FIELDS,
    )


def prepend_generated_interface_paths() -> None:
    python_dir = f"python{sys.version_info.major}.{sys.version_info.minor}"
    repo_root = Path(__file__).resolve().parents[2]
    prefixes = [Path(path) for path in os.environ.get("COLCON_PREFIX_PATH", "").split(os.pathsep) if path]
    prefixes.extend(
        [
            repo_root / "install" / "sandwich_bt_interfaces",
            repo_root / "install",
        ]
    )

    for prefix in prefixes:
        site_packages = prefix / "lib" / python_dir / "site-packages"
        if (site_packages / "sandwich_bt_interfaces" / "srv" / "__init__.py").exists():
            site_packages_str = str(site_packages)
            if site_packages_str not in sys.path:
                sys.path.insert(0, site_packages_str)


def load_supervisor_services():
    prepend_generated_interface_paths()
    for module_name in list(sys.modules):
        if module_name == "sandwich_bt_interfaces" or module_name.startswith("sandwich_bt_interfaces."):
            del sys.modules[module_name]

    try:
        from sandwich_bt_interfaces.srv import PlanNextStep, VerifyStep

        validate_supervisor_services(PlanNextStep, VerifyStep)
        return PlanNextStep, VerifyStep
    except ImportError as import_error:
        raise GeneratedInterfaceError(
            _build_rebuild_message(
                "Could not import PlanNextStep/VerifyStep from sandwich_bt_interfaces."
            )
        ) from import_error


def load_run_named_command_service():
    prepend_generated_interface_paths()
    for module_name in list(sys.modules):
        if module_name == "sandwich_bt_interfaces" or module_name.startswith("sandwich_bt_interfaces."):
            del sys.modules[module_name]

    try:
        from sandwich_bt_interfaces.srv import RunNamedCommand

        validate_run_named_command_service(RunNamedCommand)
        return RunNamedCommand
    except ImportError as import_error:
        raise GeneratedInterfaceError(
            _build_rebuild_message(
                "Could not import RunNamedCommand from sandwich_bt_interfaces."
            )
        ) from import_error
