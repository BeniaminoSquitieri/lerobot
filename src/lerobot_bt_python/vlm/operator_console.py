"""@file operator_console.py
@brief Terminal banners printed for the human operator running the BT server.

These helpers exist only to keep `server.py` focused on ROS2 wiring. They have
no side effects on the BT protocol: every banner is plain ``print`` output to
stdout and never replaces structured logger calls.
"""

from __future__ import annotations

_BANNER_RULE = "═" * 60

_RESULT_EMOJI = {
    "SUCCESS": "✅",
    "FAILURE": "❌",
    "RUNNING": "🔄",
}


def print_vlm_request_banner(*, skill_name: str, attempt_id: int, task_desc: str) -> None:
    """@brief Print the operator banner emitted when a VLM check is requested."""
    print(f"\n{_BANNER_RULE}")
    print(f"🔍 VLM CHECK → {skill_name} (attempt {attempt_id})")
    if task_desc:
        print(f"   Task: {task_desc}")
    print(f"{_BANNER_RULE}\n")


def print_vlm_result_banner(*, skill_name: str, status: str, message: str) -> None:
    """@brief Print the operator banner emitted when a VLM result is received."""
    emoji = _RESULT_EMOJI.get(status, "📢")
    print(f"\n{_BANNER_RULE}")
    print(f"{emoji} VLM RESULT → {skill_name}: {status}")
    print(f"   Message: {message}")
    print(f"{_BANNER_RULE}\n")
