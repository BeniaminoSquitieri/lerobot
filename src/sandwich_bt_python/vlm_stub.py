"""@file vlm_stub.py
@brief Lightweight topic publisher that emulates VLM verification verdicts.

Publish a small JSON string on `/sandwich_bt/vlm_sim` and this node republishes
the normalized verdict on `/sandwich_bt/verification_report`, which is the same
topic a real VLM should use.

Expected input payload (`std_msgs/String.data`):
  {"skill_name":"place_first_toast","status":"SUCCESS","confidence":0.9,"message":"ok"}
"""

from __future__ import annotations

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class VLMStubNode(Node):
    """@brief ROS2 node that turns simple JSON messages into verifier reports."""

    def __init__(
        self,
        *,
        input_topic: str = "/sandwich_bt/vlm_sim",
        report_topic: str = "/sandwich_bt/verification_report",
    ) -> None:
        """@brief Subscribe to manual input and publish normalized verifier reports."""
        super().__init__("vlm_stub")
        self._input_topic = input_topic
        self._report_topic = report_topic
        self._report_publisher = self.create_publisher(String, self._report_topic, 10)
        self.create_subscription(String, self._input_topic, self._on_msg, 10)
        self.get_logger().info(
            f"VLM stub listening on '{self._input_topic}' and publishing reports to '{self._report_topic}'."
        )

    def _on_msg(self, msg: String) -> None:
        """@brief Parse one JSON message and publish it to the verifier report topic."""
        try:
            payload = json.loads(msg.data)
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error(f"Failed to parse JSON payload: {exc}: '{msg.data}'")
            return
        if not isinstance(payload, dict):
            self.get_logger().error("Payload must be a JSON object.")
            return

        skill_name = str(payload.get("skill_name", ""))
        if not skill_name:
            self.get_logger().error("Payload missing 'skill_name'.")
            return

        status = str(payload.get("status", "")).upper()
        if status not in {"SUCCESS", "FAILURE"}:
            self.get_logger().error("'status' must be 'SUCCESS' or 'FAILURE'.")
            return

        try:
            report = {
                "skill_name": skill_name,
                "attempt_id": int(payload.get("attempt_id", 0)),
                "status": status,
                "message": str(payload.get("message", "")),
                "confidence": float(payload.get("confidence", 0.0)),
            }
        except (TypeError, ValueError) as exc:
            self.get_logger().error(f"Invalid numeric field in payload: {exc}")
            return
        out_msg = String()
        out_msg.data = json.dumps(report, sort_keys=True)
        self._report_publisher.publish(out_msg)
        self.get_logger().info(
            f"Published verification report for skill '{skill_name}' with status '{status}'."
        )


def main(argv: list[str] | None = None) -> int:
    """@brief Start the VLM stub node until interrupted."""
    rclpy.init(args=argv)
    node = VLMStubNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("VLM stub interrupted, shutting down.")
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
