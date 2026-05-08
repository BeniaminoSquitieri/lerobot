from __future__ import annotations

import inspect
import json
from types import SimpleNamespace

from sandwich_bt_python.config import SkillCommandServerConfig
from sandwich_bt_python.verification import (
    VLM_FAILURE,
    VLM_NEEDS_MANUAL_HELP,
    VLM_PENDING,
    VLM_SUCCESS,
    VLM_WAIT_HUMAN,
    VlmCheckRegistry,
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
        self.active_vlm_calls: list[dict] = []
        self.accept_active_vlm_result = False
        self.next_result = None

    def execute_skill(
        self,
        *,
        skill_name,
        robot_action_processor,
        robot_observation_processor,
        timeout_override_s,
    ):
        del robot_action_processor, robot_observation_processor, timeout_override_s
        self.skill_calls.append(skill_name)
        if self.next_result is not None:
            return self.next_result
        return SimpleNamespace(
            success=True,
            status="SUCCESS",
            elapsed_s=0.1,
            message=f"Skill '{skill_name}' completed.",
        )

    def report_active_vlm_result(self, *, skill_name, attempt_id, status, message):
        self.active_vlm_calls.append(
            {
                "skill_name": skill_name,
                "attempt_id": attempt_id,
                "status": status,
                "message": message,
            }
        )
        return self.accept_active_vlm_result


def _make_server(*, known_skill_names: set[str] | None = None):
    executor = _RecordingExecutor()
    server = SimpleNamespace(
        cfg=SimpleNamespace(
            play_sounds=False,
            auto_pass_vlm_check_for_real_skills=False,
            vlm_state_service="/sandwich_bt/vlm_state",
            vlm_request_topic="/sandwich_bt/vlm_request",
        ),
        executor_backend=executor,
        robot_action_processor=object(),
        robot_observation_processor=object(),
        vlm_check_registry=VlmCheckRegistry(known_skill_names=known_skill_names or set()),
        get_logger=lambda: _FakeLogger(),
    )
    from sandwich_bt_python.server import SkillCommandServer

    server._try_report_active_skill_vlm_result = (
        SkillCommandServer._try_report_active_skill_vlm_result.__get__(server)
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


def test_no_motion_skill_auto_passes_vlm_check_without_touching_executor() -> None:
    server, executor = _make_server(known_skill_names={"place_first_toast"})

    response = _handle_request(server, _request("no_motion_skill", "pour"), _response())
    vlm_check = server.vlm_check_registry.get_latest("pour")

    assert response.success
    assert response.status == "SUCCESS"
    assert executor.skill_calls == []
    assert vlm_check is not None
    assert vlm_check.status == VLM_SUCCESS


def test_vlm_gate_pending_waits_for_external_verifier() -> None:
    server, executor = _make_server(known_skill_names={"place_first_toast"})

    response = _handle_request(
        server,
        _request("vlm_gate_pending", "place_second_toast"),
        _response(),
    )
    vlm_check = server.vlm_check_registry.get_latest("place_second_toast")

    assert response.success
    assert executor.skill_calls == []
    assert vlm_check is not None
    assert vlm_check.status == VLM_PENDING


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
    assert server.vlm_check_registry.get_latest("recover_pour") is None


def test_real_skill_kind_still_delegates_to_executor_and_opens_pending_vlm_check() -> None:
    server, executor = _make_server(known_skill_names={"place_first_toast"})

    response = _handle_request(server, _request("skill", "place_first_toast"), _response())
    vlm_check = server.vlm_check_registry.get_latest("place_first_toast")

    assert response.success
    assert executor.skill_calls == ["place_first_toast"]
    assert vlm_check is not None
    assert vlm_check.status == VLM_PENDING


def test_real_skill_live_vlm_result_opens_resolved_vlm_check() -> None:
    server, executor = _make_server(known_skill_names={"place_first_toast"})
    executor.next_result = SimpleNamespace(
        success=True,
        status="SUCCESS",
        elapsed_s=0.2,
        message="Skill stopped by live verifier.",
        vlm_status=VLM_SUCCESS,
        vlm_message="first toast ok",
    )

    response = _handle_request(server, _request("skill", "place_first_toast"), _response())
    vlm_check = server.vlm_check_registry.get_latest("place_first_toast")

    assert response.success
    assert executor.skill_calls == ["place_first_toast"]
    assert vlm_check is not None
    assert vlm_check.status == VLM_SUCCESS
    assert vlm_check.message == "first toast ok"


def test_vlm_result_topic_can_stop_active_skill_before_attempt_exists() -> None:
    server, executor = _make_server(known_skill_names={"place_first_toast"})
    executor.accept_active_vlm_result = True

    from sandwich_bt_python.server import SkillCommandServer

    SkillCommandServer._handle_vlm_result_topic(
        server,
        SimpleNamespace(
            data=json.dumps(
                {
                    "skill_name": "place_first_toast",
                    "status": "SUCCESS",
                    "message": "first toast ok",
                }
            )
        ),
    )

    assert executor.active_vlm_calls == [
        {
            "skill_name": "place_first_toast",
            "attempt_id": 0,
            "status": VLM_SUCCESS,
            "message": "first toast ok",
        }
    ]
    assert server.vlm_check_registry.get_latest("place_first_toast") is None


def test_vlm_result_topic_resolves_pending_attempt() -> None:
    server, _executor = _make_server(known_skill_names={"place_first_toast"})
    _handle_request(server, _request("skill", "place_first_toast"), _response())

    from sandwich_bt_python.server import SkillCommandServer

    SkillCommandServer._handle_vlm_result_topic(
        server,
        SimpleNamespace(
            data=json.dumps(
                {
                    "skill_name": "place_first_toast",
                    "status": "SUCCESS",
                    "message": "scene ok",
                }
            )
        ),
    )
    vlm_check = server.vlm_check_registry.get_latest("place_first_toast")

    assert vlm_check is not None
    assert vlm_check.status == VLM_SUCCESS
    assert vlm_check.message == "scene ok"


def test_vlm_result_topic_accepts_waiting_human_state() -> None:
    server, _executor = _make_server(known_skill_names={"pour_ingredient"})
    _handle_request(server, _request("vlm_gate_pending", "pour_ingredient"), _response())

    from sandwich_bt_python.server import SkillCommandServer

    SkillCommandServer._handle_vlm_result_topic(
        server,
        SimpleNamespace(
            data=json.dumps(
                {
                    "skill_name": "pour_ingredient",
                    "status": "WAIT_HUMAN",
                    "message": "human is pouring",
                    "scene_state": "ingredient stream visible",
                }
            )
        ),
    )
    vlm_check = server.vlm_check_registry.get_latest("pour_ingredient")

    assert vlm_check is not None
    assert vlm_check.status == VLM_WAIT_HUMAN
    assert "human is pouring" in vlm_check.message
    assert "scene_state=ingredient stream visible" in vlm_check.message


def test_vlm_result_topic_maps_next_actions_to_bt_statuses() -> None:
    server, _executor = _make_server(known_skill_names={"place_first_toast"})
    _handle_request(server, _request("skill", "place_first_toast"), _response())

    from sandwich_bt_python.server import SkillCommandServer

    SkillCommandServer._handle_vlm_result_topic(
        server,
        SimpleNamespace(
            data=json.dumps(
                {
                    "skill_name": "place_first_toast",
                    "next_action": "REQUEST_MANUAL_INTERVENTION",
                    "failure_reason": "object_missing",
                    "required_human_action": "put toast back in reachable area",
                }
            )
        ),
    )
    manual = server.vlm_check_registry.get_latest("place_first_toast")
    assert manual is not None
    assert manual.status == VLM_NEEDS_MANUAL_HELP
    assert "failure_reason=object_missing" in manual.message

    SkillCommandServer._handle_vlm_result_topic(
        server,
        SimpleNamespace(
            data=json.dumps(
                {
                    "skill_name": "place_first_toast",
                    "next_action": "RETRY_SKILL",
                    "message": "human fixed the scene but placement still failed",
                }
            )
        ),
    )
    retry = server.vlm_check_registry.get_latest("place_first_toast")
    assert retry is not None
    assert retry.status == VLM_FAILURE
