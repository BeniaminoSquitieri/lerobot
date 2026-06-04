"""ROS2 bridge from lerobot generation to the external planner service.

This module is used only when the real runtime generation path selects
ros-service planner mode. It sends task and constrained planner-registry JSON
to /lerobot_bt/generate_plan and returns the service's Linear IR response text
for robot-side parsing and validation. Do not let this client bypass local
canonicalization or strict validation of the returned plan.
"""

from __future__ import annotations

import json
import sys


def request_plan_from_ros_service(
    task_name: str,
    planner_registry_payload: dict,
    *,
    service_name: str = "/lerobot_bt/generate_plan",
    scene_facts: dict | None = None,
    timeout_s: float = 0.0,
) -> str:
    try:
        import rclpy
        from rclpy.node import Node
    except ImportError as exc:
        raise RuntimeError("rclpy is required for ROS planning but could not be imported.") from exc

    try:
        from lerobot_bt_interfaces.srv import GenerateTaskPlan
    except ImportError as exc:
        raise RuntimeError(
            "ROS planning service interface lerobot_bt_interfaces/srv/GenerateTaskPlan "
            "could not be imported. Rebuild/source lerobot_bt_interfaces."
        ) from exc

    effective_timeout_s = timeout_s if timeout_s > 0 else None

    class MinimalClient(Node):
        def __init__(self) -> None:
            super().__init__("plan_client")
            self.cli = self.create_client(GenerateTaskPlan, service_name)
            if not self.cli.wait_for_service(timeout_sec=effective_timeout_s):
                raise RuntimeError(
                    f"Service {service_name} not available after {effective_timeout_s}s"
                )
            self.req = GenerateTaskPlan.Request()
            self.req.task_name = task_name
            self.req.planner_registry_json = json.dumps(planner_registry_payload)
            self.req.scene_facts_json = json.dumps(scene_facts) if scene_facts else ""
            self.future = None

        def send(self) -> None:
            self.future = self.cli.call_async(self.req)

    timeout_desc = "indefinitely" if effective_timeout_s is None else f"{effective_timeout_s}s"
    print(
        f"[ros_plan_client] Waiting for ROS service {service_name!r} ({timeout_desc})...",
        file=sys.stderr,
        flush=True,
    )
    client: MinimalClient | None = None
    rclpy.init()
    try:
        client = MinimalClient()
        print(
            f"[ros_plan_client] Service found. Sending plan request for task {task_name!r}...",
            file=sys.stderr,
            flush=True,
        )
        client.send()
        print(
            "[ros_plan_client] Waiting for VLM plan response (this may take a while)...",
            file=sys.stderr,
            flush=True,
        )
        rclpy.spin_until_future_complete(client, client.future, timeout_sec=effective_timeout_s)
        resp = client.future.result() if client.future is not None else None
    finally:
        if client is not None:
            client.destroy_node()
        rclpy.shutdown()

    if client is not None and client.future is not None and client.future.exception() is not None:
        raise RuntimeError(f"ROS service call failed: {client.future.exception()}")
    if not resp:
        if effective_timeout_s is None:
            raise RuntimeError(
                f"ROS service {service_name} returned without a response."
            )
        raise RuntimeError(
            f"No response from ROS service {service_name} within {effective_timeout_s}s."
        )
    if not resp.success:
        raise RuntimeError(f"ROS planning failed: {resp.error_message}")
    if not resp.plan_json:
        raise RuntimeError("ROS service returned empty plan_json.")
    return resp.plan_json
