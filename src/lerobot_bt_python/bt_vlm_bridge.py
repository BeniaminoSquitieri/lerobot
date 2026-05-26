#!/usr/bin/env python

# Comment: executes this BT logic statement.
"""ROS2 bridge between LeRobot BT VLM checks and the Panda live VLM verifier.

The BT stack uses JSON messages with `skill_name` and `attempt_id`, while the
Panda verifier uses plain `std_msgs/String` commands and statuses. This node
keeps the latest pending BT check in memory and translates both directions.
"""

# Comment: imports dependencies or symbols required by the module.
from __future__ import annotations

# Comment: imports dependencies or symbols required by the module.
import json
# Comment: imports dependencies or symbols required by the module.
from string import Formatter
# Comment: imports dependencies or symbols required by the module.
from typing import Any

# Comment: imports dependencies or symbols required by the module.
import rclpy
# Comment: imports dependencies or symbols required by the module.
from rclpy.node import Node
# Comment: imports dependencies or symbols required by the module.
from std_msgs.msg import String


# Comment: assigns or prepares a value used by later statements.
BT_VLM_REQUEST_TOPIC = "/lerobot_bt/vlm_request"
# Comment: assigns or prepares a value used by later statements.
BT_VLM_RESULT_TOPIC = "/lerobot_bt/vlm_result"
# Comment: assigns or prepares a value used by later statements.
PANDA_VLM_REQUEST_TOPIC = "/panda/vlm/request"
# Comment: assigns or prepares a value used by later statements.
PANDA_VLM_STATUS_TOPIC = "/panda/vlm/status"

# Comment: assigns or prepares a value used by later statements.
PANDA_TO_BT_STATUS = {
    # Comment: executes this BT logic statement.
    "SUCCESS": "SUCCESS",
    # Comment: executes this BT logic statement.
    "FAILED": "FAILURE",
    # Comment: executes this BT logic statement.
    "FAILURE": "FAILURE",
    # Comment: executes this BT logic statement.
    "STILL_RUNNING": "RUNNING",
    # Comment: executes this BT logic statement.
    "RUNNING": "RUNNING",
    # Comment: executes this BT logic statement.
    "PENDING": "PENDING",
# Comment: closes a call, data structure, or multiline block.
}

# Comment: assigns or prepares a value used by later statements.
DEFAULT_COMMAND_TEMPLATE = (
    # Comment: executes this BT logic statement.
    "Verify whether the current robot task/check is complete.\n"
    # Comment: executes this BT logic statement.
    "BT check name: {skill_name}\n"
    # Comment: executes this BT logic statement.
    "Attempt id: {attempt_id}\n"
    # Comment: executes this BT logic statement.
    "BT message: {message}\n"
    # Comment: executes this BT logic statement.
    "Return exactly one token: SUCCESS, FAILED, or STILL_RUNNING."
# Comment: closes a call, data structure, or multiline block.
)


# Comment: defines the function or method _safe_format.
def _safe_format(template: str, values: dict[str, Any]) -> str:
    # Comment: executes this BT logic statement.
    """Format a template while replacing missing fields with an empty string."""
    # Comment: assigns or prepares a value used by later statements.
    fields = {field_name for _, field_name, _, _ in Formatter().parse(template) if field_name}
    # Comment: assigns or prepares a value used by later statements.
    safe_values = {field_name: values.get(field_name, "") for field_name in fields}
    # Comment: returns the computed value to the caller.
    return template.format(**safe_values)


# Comment: declares the class BtPandaVlmBridge.
class BtPandaVlmBridge(Node):
    # Comment: executes this BT logic statement.
    """Translate BT VLM JSON requests/results to the Panda VLM string protocol."""

    # Comment: defines the function or method __init__.
    def __init__(self) -> None:
        # Comment: closes a call, data structure, or multiline block.
        super().__init__("lerobot_bt_panda_vlm_bridge")

        # Comment: declares a ROS2 parameter configurable at runtime.
        self.declare_parameter("bt_vlm_request_topic", BT_VLM_REQUEST_TOPIC)
        # Comment: declares a ROS2 parameter configurable at runtime.
        self.declare_parameter("bt_vlm_result_topic", BT_VLM_RESULT_TOPIC)
        # Comment: declares a ROS2 parameter configurable at runtime.
        self.declare_parameter("panda_vlm_request_topic", PANDA_VLM_REQUEST_TOPIC)
        # Comment: declares a ROS2 parameter configurable at runtime.
        self.declare_parameter("panda_vlm_status_topic", PANDA_VLM_STATUS_TOPIC)
        # Comment: declares a ROS2 parameter configurable at runtime.
        self.declare_parameter("command_template", DEFAULT_COMMAND_TEMPLATE)
        # Comment: declares a ROS2 parameter configurable at runtime.
        self.declare_parameter("publish_running_updates", True)

        # Comment: reads the effective value of a ROS2 parameter.
        self.bt_vlm_request_topic = str(self.get_parameter("bt_vlm_request_topic").value)
        # Comment: reads the effective value of a ROS2 parameter.
        self.bt_vlm_result_topic = str(self.get_parameter("bt_vlm_result_topic").value)
        # Comment: reads the effective value of a ROS2 parameter.
        self.panda_vlm_request_topic = str(self.get_parameter("panda_vlm_request_topic").value)
        # Comment: reads the effective value of a ROS2 parameter.
        self.panda_vlm_status_topic = str(self.get_parameter("panda_vlm_status_topic").value)
        # Comment: reads the effective value of a ROS2 parameter.
        self.command_template = str(self.get_parameter("command_template").value)
        # Comment: reads the effective value of a ROS2 parameter.
        self.publish_running_updates = bool(self.get_parameter("publish_running_updates").value)

        # Comment: updates state or a field on the current object.
        self._active_request: dict[str, Any] | None = None

        # Comment: creates a ROS2 subscription to receive messages from a topic.
        self._bt_request_sub = self.create_subscription(
            # Comment: executes this BT logic statement.
            String,
            # Comment: executes this BT logic statement.
            self.bt_vlm_request_topic,
            # Comment: executes this BT logic statement.
            self._handle_bt_request,
            # Comment: executes this BT logic statement.
            10,
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: creates a ROS2 subscription to receive messages from a topic.
        self._panda_status_sub = self.create_subscription(
            # Comment: executes this BT logic statement.
            String,
            # Comment: executes this BT logic statement.
            self.panda_vlm_status_topic,
            # Comment: executes this BT logic statement.
            self._handle_panda_status,
            # Comment: executes this BT logic statement.
            10,
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: creates a ROS2 publisher to send messages on a topic.
        self._panda_request_pub = self.create_publisher(String, self.panda_vlm_request_topic, 10)
        # Comment: creates a ROS2 publisher to send messages on a topic.
        self._bt_result_pub = self.create_publisher(String, self.bt_vlm_result_topic, 10)

        # Comment: executes this BT logic statement.
        self.get_logger().info(
            # Comment: executes this BT logic statement.
            "BT/Panda VLM bridge ready: "
            # Comment: executes this BT logic statement.
            f"{self.bt_vlm_request_topic} -> {self.panda_vlm_request_topic}, "
            # Comment: executes this BT logic statement.
            f"{self.panda_vlm_status_topic} -> {self.bt_vlm_result_topic}."
        # Comment: closes a call, data structure, or multiline block.
        )

    # Comment: defines the function or method _handle_bt_request.
    def _handle_bt_request(self, msg: String) -> None:
        # Comment: opens a protected block to catch possible errors.
        try:
            # Comment: deserializes a JSON string into a Python object.
            payload = json.loads(msg.data)
        # Comment: handles a specific exception raised by the protected block.
        except json.JSONDecodeError as exc:
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().error(f"Rejected BT VLM request with invalid JSON: {exc}: {msg.data!r}")
            # Comment: returns the computed value to the caller.
            return
        # Comment: evaluates a condition and chooses the branch to run.
        if not isinstance(payload, dict):
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().error("Rejected BT VLM request: payload must be a JSON object.")
            # Comment: returns the computed value to the caller.
            return

        # Comment: assigns or prepares a value used by later statements.
        skill_name = str(payload.get("skill_name", "")).strip()
        # Comment: evaluates a condition and chooses the branch to run.
        if not skill_name:
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().error("Rejected BT VLM request: missing non-empty 'skill_name'.")
            # Comment: returns the computed value to the caller.
            return

        # Comment: opens a protected block to catch possible errors.
        try:
            # Comment: assigns or prepares a value used by later statements.
            attempt_id = int(payload.get("attempt_id", 0))
        # Comment: handles a specific exception raised by the protected block.
        except (TypeError, ValueError):
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().error(f"Rejected BT VLM request for '{skill_name}': invalid attempt_id.")
            # Comment: returns the computed value to the caller.
            return

        # Comment: assigns or prepares a value used by later statements.
        payload["skill_name"] = skill_name
        # Comment: assigns or prepares a value used by later statements.
        payload["attempt_id"] = attempt_id
        # Comment: updates state or a field on the current object.
        self._active_request = payload

        # Comment: assigns or prepares a value used by later statements.
        request = String()
        # Comment: updates state or a field on the current object.
        request.data = _safe_format(self.command_template, payload)
        # Comment: publishes the prepared message on the ROS2 topic.
        self._panda_request_pub.publish(request)
        # Comment: executes this BT logic statement.
        self.get_logger().info(
            # Comment: executes this BT logic statement.
            f"Forwarded BT VLM request '{skill_name}' attempt {attempt_id} to Panda verifier."
        # Comment: closes a call, data structure, or multiline block.
        )

    # Comment: defines the function or method _handle_panda_status.
    def _handle_panda_status(self, msg: String) -> None:
        # Comment: evaluates a condition and chooses the branch to run.
        if self._active_request is None:
            # Comment: executes this BT logic statement.
            self.get_logger().warning(
                # Comment: executes this BT logic statement.
                f"Ignored Panda VLM status {msg.data!r}: no active BT VLM request is pending."
            # Comment: closes a call, data structure, or multiline block.
            )
            # Comment: returns the computed value to the caller.
            return

        # Comment: assigns or prepares a value used by later statements.
        panda_status = msg.data.strip().upper()
        # Comment: assigns or prepares a value used by later statements.
        bt_status = PANDA_TO_BT_STATUS.get(panda_status)
        # Comment: evaluates a condition and chooses the branch to run.
        if bt_status is None:
            # Comment: executes this BT logic statement.
            self.get_logger().warning(
                # Comment: executes this BT logic statement.
                f"Ignored unsupported Panda VLM status {msg.data!r}. "
                # Comment: executes this BT logic statement.
                f"Expected one of {sorted(PANDA_TO_BT_STATUS)}."
            # Comment: closes a call, data structure, or multiline block.
            )
            # Comment: returns the computed value to the caller.
            return
        # Comment: evaluates a condition and chooses the branch to run.
        if bt_status in {"RUNNING", "PENDING"} and not self.publish_running_updates:
            # Comment: returns the computed value to the caller.
            return

        # Comment: assigns or prepares a value used by later statements.
        active_request = self._active_request
        # Comment: assigns or prepares a value used by later statements.
        result_payload = {
            # Comment: executes this BT logic statement.
            "skill_name": active_request["skill_name"],
            # Comment: executes this BT logic statement.
            "attempt_id": int(active_request.get("attempt_id", 0)),
            # Comment: executes this BT logic statement.
            "status": bt_status,
            # Comment: executes this BT logic statement.
            "message": f"Panda VLM reported {panda_status}.",
        # Comment: closes a call, data structure, or multiline block.
        }

        # Comment: assigns or prepares a value used by later statements.
        result = String()
        # Comment: serializes the Python payload into a JSON string.
        result.data = json.dumps(result_payload, sort_keys=True)
        # Comment: publishes the prepared message on the ROS2 topic.
        self._bt_result_pub.publish(result)
        # Comment: executes this BT logic statement.
        self.get_logger().info(
            # Comment: executes this BT logic statement.
            f"Published BT VLM result for '{result_payload['skill_name']}' "
            # Comment: executes this BT logic statement.
            f"attempt {result_payload['attempt_id']}: {bt_status}."
        # Comment: closes a call, data structure, or multiline block.
        )

        # Comment: evaluates a condition and chooses the branch to run.
        if bt_status in {"SUCCESS", "FAILURE"}:
            # Comment: updates state or a field on the current object.
            self._active_request = None


# Comment: defines the function or method main.
def main() -> None:
    # Comment: executes this BT logic statement.
    """Run the BT/Panda VLM bridge node."""
    # Comment: closes a call, data structure, or multiline block.
    rclpy.init()
    # Comment: assigns or prepares a value used by later statements.
    node = BtPandaVlmBridge()
    # Comment: opens a protected block to catch possible errors.
    try:
        # Comment: closes a call, data structure, or multiline block.
        rclpy.spin(node)
    # Comment: always runs the final cleanup for the protected block.
    finally:
        # Comment: closes a call, data structure, or multiline block.
        node.destroy_node()
        # Comment: closes a call, data structure, or multiline block.
        rclpy.shutdown()


# Comment: evaluates a condition and chooses the branch to run.
if __name__ == "__main__":
    # Comment: closes a call, data structure, or multiline block.
    main()
