"""ROS2 client for GenerateTaskPlan service."""
from typing import Optional

def request_plan_from_ros_service(
    task_name: str,
    planner_registry_payload: dict,
    *,
    service_name: str = "/lerobot_bt/generate_plan",
    scene_facts: Optional[dict] = None,
    timeout_s: float = 30.0,
) -> str:
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.task import Future
        from lerobot_bt_interfaces.srv import GenerateTaskPlan
    except ImportError as e:
        raise RuntimeError("rclpy is required for ROS planning but is not installed.") from e

    class MinimalClient(Node):
        def __init__(self):
            super().__init__('plan_client')
            self.cli = self.create_client(GenerateTaskPlan, service_name)
            if not self.cli.wait_for_service(timeout_sec=timeout_s):
                raise RuntimeError(f"Service {service_name} not available after {timeout_s}s")
            self.req = GenerateTaskPlan.Request()
            self.req.task_name = task_name
            import json
            self.req.planner_registry_json = json.dumps(planner_registry_payload)
            self.req.scene_facts_json = json.dumps(scene_facts) if scene_facts else ""
            self.future: Optional[Future] = None

        def send(self):
            self.future = self.cli.call_async(self.req)

    rclpy.init()
    client = MinimalClient()
    client.send()
    rclpy.spin_until_future_complete(client, client.future, timeout_sec=timeout_s)
    resp = client.future.result()
    rclpy.shutdown()
    if not resp:
        raise RuntimeError("No response from ROS service.")
    if not resp.success:
        raise RuntimeError(f"ROS planning failed: {resp.error_message}")
    if not resp.plan_json:
        raise RuntimeError("ROS service returned empty plan_json.")
    return resp.plan_json
