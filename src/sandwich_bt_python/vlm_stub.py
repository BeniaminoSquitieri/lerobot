"""Lightweight VLM simulator: subscribe to a topic and report verification.

This node allows manual testing of the sandwich BT verification flow without
running a full VLM verifier. Publish a small JSON string on
`/sandwich_bt/vlm_sim` and this node will query the server for the latest
verification attempt for the named skill, then call
`ReportSkillVerification` with the provided status.

Expected message payload (std_msgs/String.data):
  {"skill_name":"place_first_toast","status":"SUCCESS","confidence":0.9,"message":"ok"}

Requirements: source your ROS2 workspace so `rclpy` and
`sandwich_bt_interfaces` are importable.
"""

from __future__ import annotations

import json
from typing import Any

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class VLMStubNode(Node):
    def __init__(self, *, topic: str = "/sandwich_bt/vlm_sim") -> None:
        super().__init__("vlm_stub")
        self._topic = topic
        # Service clients
        from sandwich_bt_interfaces.srv import GetSkillVerification, ReportSkillVerification  # type: ignore

        self._get_service_type = GetSkillVerification
        self._report_service_type = ReportSkillVerification
        self._get_client = self.create_client(GetSkillVerification, "/sandwich_bt/get_skill_verification")
        self._report_client = self.create_client(ReportSkillVerification, "/sandwich_bt/report_skill_verification")

        # Subscriber to receive simple JSON commands
        self.create_subscription(String, self._topic, self._on_msg, 10)
        self.get_logger().info(f"VLM stub listening on '{self._topic}' and forwarding to verification services.")

    def _on_msg(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error(f"Failed to parse JSON payload: {exc}: '{msg.data}'")
            return

        skill_name = str(payload.get("skill_name", ""))
        if not skill_name:
            self.get_logger().error("Payload missing 'skill_name'.")
            return

        status = str(payload.get("status", "")).upper()
        if status not in {"SUCCESS", "FAILURE"}:
            self.get_logger().error("'status' must be 'SUCCESS' or 'FAILURE'.")
            return

        message = str(payload.get("message", ""))
        confidence = float(payload.get("confidence", 0.0))

        get_req = self._get_service_type.Request()
        get_req.skill_name = skill_name

        if not self._get_client.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("GetSkillVerification service not available.")
            return

        get_future = self._get_client.call_async(get_req)
        get_future.add_done_callback(
            lambda future: self._on_get_skill_verification_done(
                future,
                skill_name=skill_name,
                status=status,
                message=message,
                confidence=confidence,
            )
        )

    def _on_get_skill_verification_done(
        self,
        future: Any,
        *,
        skill_name: str,
        status: str,
        message: str,
        confidence: float,
    ) -> None:
        try:
            get_res = future.result()
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error(f"Failed to call GetSkillVerification: {exc}")
            return

        if not getattr(get_res, "has_attempt", False):
            self.get_logger().warning(f"No verification attempt found for skill '{skill_name}'.")
            return

        attempt_id = int(get_res.attempt_id)

        report_req = self._report_service_type.Request()
        report_req.skill_name = skill_name
        report_req.attempt_id = attempt_id
        report_req.status = status
        report_req.message = message
        report_req.confidence = float(confidence)

        if not self._report_client.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("ReportSkillVerification service not available.")
            return

        report_future = self._report_client.call_async(report_req)
        report_future.add_done_callback(self._on_report_skill_verification_done)

    def _on_report_skill_verification_done(self, future: Any) -> None:
        try:
            report_res = future.result()
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error(f"Failed to call ReportSkillVerification: {exc}")
            return

        accepted = getattr(report_res, "accepted", False)
        applied = int(getattr(report_res, "applied_attempt_id", 0))
        self.get_logger().info(f"Report sent: accepted={accepted}, applied_attempt_id={applied}, message='{report_res.message}'.")


def main(argv: list[str] | None = None) -> int:
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
