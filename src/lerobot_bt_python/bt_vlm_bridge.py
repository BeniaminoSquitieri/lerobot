#!/usr/bin/env python

"""Legacy compatibility ROS2 bridge between BT VLM checks and Panda live VLM.

The BT stack uses JSON messages with `skill_name` and `attempt_id`, while the
Panda verifier uses plain `std_msgs/String` commands and statuses. This node
keeps the latest pending BT check in memory and translates both directions.
"""

from __future__ import annotations

import json
import logging
from string import Formatter
from typing import Any

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


BT_VLM_REQUEST_TOPIC = "/lerobot_bt/vlm_request"
BT_VLM_RESULT_TOPIC = "/lerobot_bt/vlm_result"
PANDA_VLM_REQUEST_TOPIC = "/panda/vlm/request"
PANDA_VLM_STATUS_TOPIC = "/panda/vlm/status"

PANDA_TO_BT_STATUS = {
    "SUCCESS": "SUCCESS",
    "FAILED": "FAILURE",
    "FAILURE": "FAILURE",
    "STILL_RUNNING": "RUNNING",
    "RUNNING": "RUNNING",
    "PENDING": "PENDING",
}

_legacy_bridge_warned = False

DEFAULT_COMMAND_TEMPLATE = (
    "Verify whether the current robot task/check is complete.\n"
    "BT check name: {skill_name}\n"
    "Attempt id: {attempt_id}\n"
    "BT message: {message}\n"
    "Return exactly one token: SUCCESS, FAILED, or STILL_RUNNING."
)


def _safe_format(template: str, values: dict[str, Any]) -> str:
    """Format a template while replacing missing fields with an empty string."""
    fields = {field_name for _, field_name, _, _ in Formatter().parse(template) if field_name}
    safe_values = {field_name: values.get(field_name, "") for field_name in fields}
    return template.format(**safe_values)


class BtPandaVlmBridge(Node):
    """Translate BT VLM JSON requests/results to the Panda VLM string protocol."""

    def __init__(self) -> None:
        super().__init__("lerobot_bt_panda_vlm_bridge")

        self.declare_parameter("bt_vlm_request_topic", BT_VLM_REQUEST_TOPIC)
        self.declare_parameter("bt_vlm_result_topic", BT_VLM_RESULT_TOPIC)
        self.declare_parameter("panda_vlm_request_topic", PANDA_VLM_REQUEST_TOPIC)
        self.declare_parameter("panda_vlm_status_topic", PANDA_VLM_STATUS_TOPIC)
        self.declare_parameter("command_template", DEFAULT_COMMAND_TEMPLATE)
        self.declare_parameter("publish_running_updates", True)

        self.bt_vlm_request_topic = str(self.get_parameter("bt_vlm_request_topic").value)
        self.bt_vlm_result_topic = str(self.get_parameter("bt_vlm_result_topic").value)
        self.panda_vlm_request_topic = str(self.get_parameter("panda_vlm_request_topic").value)
        self.panda_vlm_status_topic = str(self.get_parameter("panda_vlm_status_topic").value)
        self.command_template = str(self.get_parameter("command_template").value)
        self.publish_running_updates = bool(self.get_parameter("publish_running_updates").value)

        self._active_request: dict[str, Any] | None = None

        self._bt_request_sub = self.create_subscription(
            String,
            self.bt_vlm_request_topic,
            self._handle_bt_request,
            10,
        )
        self._panda_status_sub = self.create_subscription(
            String,
            self.panda_vlm_status_topic,
            self._handle_panda_status,
            10,
        )
        self._panda_request_pub = self.create_publisher(String, self.panda_vlm_request_topic, 10)
        self._bt_result_pub = self.create_publisher(String, self.bt_vlm_result_topic, 10)

        self.get_logger().info(
            "BT/Panda VLM bridge ready: "
            f"{self.bt_vlm_request_topic} -> {self.panda_vlm_request_topic}, "
            f"{self.panda_vlm_status_topic} -> {self.bt_vlm_result_topic}."
        )

    def _handle_bt_request(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().error(f"Rejected BT VLM request with invalid JSON: {exc}: {msg.data!r}")
            return
        if not isinstance(payload, dict):
            self.get_logger().error("Rejected BT VLM request: payload must be a JSON object.")
            return

        skill_name = str(payload.get("skill_name", "")).strip()
        if not skill_name:
            self.get_logger().error("Rejected BT VLM request: missing non-empty 'skill_name'.")
            return

        try:
            attempt_id = int(payload.get("attempt_id", 0))
        except (TypeError, ValueError):
            self.get_logger().error(f"Rejected BT VLM request for '{skill_name}': invalid attempt_id.")
            return

        payload["skill_name"] = skill_name
        payload["attempt_id"] = attempt_id
        self._active_request = payload

        request = String()
        request.data = _safe_format(self.command_template, payload)
        self._panda_request_pub.publish(request)
        self.get_logger().info(
            f"Forwarded BT VLM request '{skill_name}' attempt {attempt_id} to Panda verifier."
        )

    def _handle_panda_status(self, msg: String) -> None:
        if self._active_request is None:
            self.get_logger().warning(
                f"Ignored Panda VLM status {msg.data!r}: no active BT VLM request is pending."
            )
            return

        panda_status = msg.data.strip().upper()
        bt_status = PANDA_TO_BT_STATUS.get(panda_status)
        if bt_status is None:
            self.get_logger().warning(
                f"Ignored unsupported Panda VLM status {msg.data!r}. "
                f"Expected one of {sorted(PANDA_TO_BT_STATUS)}."
            )
            return
        if bt_status in {"RUNNING", "PENDING"} and not self.publish_running_updates:
            return

        active_request = self._active_request
        result_payload = {
            "skill_name": active_request["skill_name"],
            "attempt_id": int(active_request.get("attempt_id", 0)),
            "status": bt_status,
            "message": f"Panda VLM reported {panda_status}.",
        }

        result = String()
        result.data = json.dumps(result_payload, sort_keys=True)
        self._bt_result_pub.publish(result)
        self.get_logger().info(
            f"Published BT VLM result for '{result_payload['skill_name']}' "
            f"attempt {result_payload['attempt_id']}: {bt_status}."
        )

        if bt_status in {"SUCCESS", "FAILURE"}:
            self._active_request = None


def main() -> None:
    """Run the BT/Panda VLM bridge node."""
    global _legacy_bridge_warned
    if not _legacy_bridge_warned:
        logging.getLogger(__name__).warning("bt_vlm_bridge is a legacy compatibility path and is deprecated.")
        _legacy_bridge_warned = True
    rclpy.init()
    node = BtPandaVlmBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
