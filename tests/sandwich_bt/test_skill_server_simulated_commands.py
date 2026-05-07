from __future__ import annotations

import inspect
import json
from types import SimpleNamespace

from sandwich_bt_python.config import SkillCommandServerConfig
from sandwich_bt_python.verification import (
    PENDING_VERIFICATION_STATUS,
    SUCCESSFUL_VERIFICATION_STATUS,
    SkillVerificationRegistry,
)


class _FakeLogger:
    def debug(self, *_args, **_kwargs) -> None:
        return None

    def error(self, *_args, **_kwargs) -> None:
        return None

    def exception(self, *_args, **_kwargs) -> None:
        return None

    def info(self, *_args, **_kwargs) -> None:
        return None

    def warning(self, *_args, **_kwargs) -> None:
        return None


class _RecordingExecutor:
    def __init__(self) -> None:
        self.skill_calls: list[str] = []

    def execute_skill(self, *, skill_name, robot_action_processor, robot_observation_processor, timeout_override_s):
        del robot_action_processor, robot_observation_processor, timeout_override_s
        self.skill_calls.append(skill_name)
        return SimpleNamespace(success=True, status="SUCCESS", elapsed_s=0.1, message=f"Skill '{skill_name}' completed.")


def _make_server(*, known_skill_names: set[str] | None = None):
    executor = _RecordingExecutor()
    server = SimpleNamespace(
        cfg=SimpleNamespace(
            play_sounds=False,
            auto_verify_real_skills=False,
            verification_query_service_name="/sandwich_bt/get_skill_verification",
            verification_request_topic_name="/sandwich_bt/verification_request",
        ),
        executor_backend=executor,
        robot_action_processor=object(),
        robot_observation_processor=object(),
        verification_registry=SkillVerificationRegistry(known_skill_names=known_skill_names or set()),
        get_logger=lambda: _FakeLogger(),
    )
    return server, executor


def _request(kind: str, name: str):
    return SimpleNamespace(kind=kind, name=name, timeout_s=0.0)


def _response():
    return SimpleNamespace(success=False, status="", elapsed_s=0.0, message="")


def _handle_request(server, request, response):
    from sandwich_bt_python.server import SkillCommandServer

    return SkillCommandServer._handle_request(server, request, response)


def test_parser_wrap_sees_dataclass_config_annotation() -> None:
    from sandwich_bt_python.server import run

    argtype = inspect.getfullargspec(run.__wrapped__).annotations["cfg"]

    assert argtype is SkillCommandServerConfig


def test_simulated_skill_auto_resolves_verification_without_touching_executor() -> None:
    server, executor = _make_server(known_skill_names={"place_first_toast"})

    response = _handle_request(server, _request("simulated_skill", "pour"), _response())
    verification = server.verification_registry.get_latest("pour")

    assert response.success
    assert response.status == "SUCCESS"
    assert executor.skill_calls == []
    assert verification is not None
    assert verification.status == SUCCESSFUL_VERIFICATION_STATUS
    assert verification.confidence == 1.0


def test_simulated_skill_pending_waits_for_external_verifier() -> None:
    server, executor = _make_server(known_skill_names={"place_first_toast"})

    response = _handle_request(
        server,
        _request("simulated_skill_pending", "place_second_toast"),
        _response(),
    )
    verification = server.verification_registry.get_latest("place_second_toast")

    assert response.success
    assert executor.skill_calls == []
    assert verification is not None
    assert verification.status == PENDING_VERIFICATION_STATUS


def test_recovery_kind_is_rejected() -> None:
    server, executor = _make_server(known_skill_names={"recover_pour"})

    response = _handle_request(
        server,
        _request("recovery", "recover_pour"),
        _response(),
    )

    assert not response.success
    assert response.status == "ERROR"
    assert "Unsupported command kind" in response.message
    assert executor.skill_calls == []
    assert server.verification_registry.get_latest("recover_pour") is None


def test_real_skill_kind_still_delegates_to_executor_and_opens_pending_verification() -> None:
    server, executor = _make_server(known_skill_names={"place_first_toast"})

    response = _handle_request(server, _request("skill", "place_first_toast"), _response())
    verification = server.verification_registry.get_latest("place_first_toast")

    assert response.success
    assert executor.skill_calls == ["place_first_toast"]
    assert verification is not None
    assert verification.status == PENDING_VERIFICATION_STATUS


def test_verification_report_topic_resolves_pending_attempt() -> None:
    server, _executor = _make_server(known_skill_names={"place_first_toast"})
    _handle_request(server, _request("skill", "place_first_toast"), _response())

    from sandwich_bt_python.server import SkillCommandServer

    SkillCommandServer._handle_verification_report_topic(
        server,
        SimpleNamespace(
            data=json.dumps(
                {
                    "skill_name": "place_first_toast",
                    "status": "SUCCESS",
                    "message": "scene ok",
                    "confidence": 0.93,
                }
            )
        ),
    )
    verification = server.verification_registry.get_latest("place_first_toast")

    assert verification is not None
    assert verification.status == SUCCESSFUL_VERIFICATION_STATUS
    assert verification.message == "scene ok"
    assert verification.confidence == 0.93
