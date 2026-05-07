from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

pytest.importorskip("rclpy")
pytest.importorskip("std_msgs")

from sandwich_bt_python.vlm_stub import VLMStubNode


class _FakePublisher:
    def __init__(self) -> None:
        self.messages = []

    def publish(self, msg) -> None:
        self.messages.append(msg)


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

    def __init__(self, *, publisher: _FakePublisher, logger: _FakeLogger) -> None:
        self._report_publisher = publisher
        self._logger = logger

    def get_logger(self) -> _FakeLogger:
        return self._logger


def test_vlm_stub_republishes_manual_verdict_to_report_topic() -> None:
    logger = _FakeLogger()
    publisher = _FakePublisher()
    node = _FakeVLMStub(publisher=publisher, logger=logger)
    msg = SimpleNamespace(
        data=json.dumps(
            {
                "skill_name": "place_first_toast",
                "attempt_id": 7,
                "status": "SUCCESS",
                "confidence": 0.95,
                "message": "first toast ok",
            }
        )
    )

    VLMStubNode._on_msg(node, msg)

    assert len(publisher.messages) == 1
    payload = json.loads(publisher.messages[0].data)
    assert payload == {
        "skill_name": "place_first_toast",
        "attempt_id": 7,
        "status": "SUCCESS",
        "message": "first toast ok",
        "confidence": 0.95,
    }
    assert logger.error_messages == []
