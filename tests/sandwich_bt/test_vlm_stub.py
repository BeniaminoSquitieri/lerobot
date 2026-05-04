from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

pytest.importorskip("rclpy")
pytest.importorskip("std_msgs")

from sandwich_bt_python.vlm_stub import VLMStubNode


class _FakeFuture:
    def __init__(self, response) -> None:
        self._response = response

    def result(self):
        return self._response

    def add_done_callback(self, callback) -> None:
        callback(self)


class _FakeClient:
    def __init__(self, response) -> None:
        self.response = response
        self.requests = []

    def wait_for_service(self, *, timeout_sec: float) -> bool:
        del timeout_sec
        return True

    def call_async(self, request):
        self.requests.append(request)
        return _FakeFuture(self.response)


class _FakeRequest:
    pass


class _FakeService:
    Request = _FakeRequest


class _FakeLogger:
    def __init__(self) -> None:
        self.info_messages: list[str] = []
        self.warning_messages: list[str] = []
        self.error_messages: list[str] = []

    def error(self, message: str) -> None:
        self.error_messages.append(message)

    def info(self, message: str) -> None:
        self.info_messages.append(message)

    def warning(self, message: str) -> None:
        self.warning_messages.append(message)


class _FakeVLMStub:
    _on_msg = VLMStubNode._on_msg
    _on_get_skill_verification_done = VLMStubNode._on_get_skill_verification_done
    _on_report_skill_verification_done = VLMStubNode._on_report_skill_verification_done

    def __init__(self, *, get_client: _FakeClient, report_client: _FakeClient, logger: _FakeLogger) -> None:
        self._get_service_type = _FakeService
        self._report_service_type = _FakeService
        self._get_client = get_client
        self._report_client = report_client
        self._logger = logger

    def get_logger(self) -> _FakeLogger:
        return self._logger


def test_vlm_stub_reports_verification_without_nested_spin() -> None:
    logger = _FakeLogger()
    get_client = _FakeClient(SimpleNamespace(has_attempt=True, attempt_id=7))
    report_client = _FakeClient(SimpleNamespace(accepted=True, applied_attempt_id=7, message="stored"))
    node = _FakeVLMStub(get_client=get_client, report_client=report_client, logger=logger)
    msg = SimpleNamespace(
        data=json.dumps(
            {
                "skill_name": "place_first_toast",
                "status": "SUCCESS",
                "confidence": 0.95,
                "message": "first toast ok",
            }
        )
    )

    VLMStubNode._on_msg(node, msg)

    assert get_client.requests[0].skill_name == "place_first_toast"
    assert report_client.requests[0].skill_name == "place_first_toast"
    assert report_client.requests[0].attempt_id == 7
    assert report_client.requests[0].status == "SUCCESS"
    assert report_client.requests[0].confidence == 0.95
    assert logger.error_messages == []
