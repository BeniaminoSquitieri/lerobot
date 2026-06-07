"""@file protocol.py
@brief Parsing helpers for the VLM/operator topic protocol.

Centralizes the translation between the loosely-typed JSON payloads accepted
on the VLM result topic (and the legacy gate tokens) and the VLM status
vocabulary defined in `vlm/verification.py`. Keeping these helpers in their own
module lets them be unit-tested without importing `rclpy`.
"""

from __future__ import annotations

from typing import Any

from .verification import (
    VLM_FAILURE,
    VLM_RUNNING,
    VLM_SUCCESS,
)

NEXT_ACTION_TO_STATUS = {
    "CONTINUE": VLM_SUCCESS,
    "PROCEED": VLM_SUCCESS,
    "RETRY": VLM_FAILURE,
    "RETRY_SKILL": VLM_FAILURE,
    "WAIT": VLM_RUNNING,
}
"""Mapping from `next_action` topic tokens to the VLM status vocabulary."""


def truthy_payload_value(value: Any) -> bool:
    """@brief Return true for boolean-like values coming from simple VLM topics."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def normalize_vlm_status_token(token: str) -> str:
    """@brief Map scene-gate tokens onto the registry status vocabulary."""
    normalized = token.upper()
    if not normalized:
        return ""
    if normalized.startswith("SCENE_") and normalized.endswith("_READY"):
        return VLM_SUCCESS
    if normalized == "TASK_COMPLETE":
        return VLM_SUCCESS
    if normalized == "ANOMALY_DETECTED":
        return VLM_FAILURE
    return normalized


def vlm_status_from_payload(payload: dict[str, Any]) -> str:
    """@brief Resolve VLM status/next_action fields into the BT-facing status."""
    if truthy_payload_value(payload.get("anomaly_detected", False)):
        return VLM_FAILURE
    if truthy_payload_value(payload.get("scene_ready", False)):
        return VLM_SUCCESS

    status = normalize_vlm_status_token(str(payload.get("status", "")))
    if status:
        return status
    scene_id = normalize_vlm_status_token(str(payload.get("scene_id", "")))
    if scene_id:
        return scene_id
    next_action = str(payload.get("next_action", "")).upper()
    if next_action in NEXT_ACTION_TO_STATUS:
        return NEXT_ACTION_TO_STATUS[next_action]
    return ""


def vlm_message_from_payload(payload: dict[str, Any], *, status: str) -> str:
    """@brief Build a compact operator message from richer VLM topic fields."""
    message_parts = []
    message = str(payload.get("message", ""))
    if message:
        message_parts.append(message)
    for key in (
        "scene_id",
        "scene_ready",
        "anomaly_detected",
        "human_help_required",
        "failure_reason",
        "scene_state",
        "required_human_action",
        "next_action",
    ):
        value = payload.get(key)
        if value not in (None, ""):
            message_parts.append(f"{key}={value}")
    if not message_parts:
        message_parts.append(f"External verifier reported {status}.")
    return " | ".join(message_parts)
