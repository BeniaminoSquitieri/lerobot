#!/usr/bin/env python3
"""Test ROS2 cross-machine communication between two hosts.

Run --pub on one machine, --sub on the other, or --both for loopback.
"""

import argparse
import json
import sys
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

TOPIC = "/bt_comm_test"


class PubNode(Node):
    def __init__(self):
        super().__init__("comm_test_pub")
        self.pub = self.create_publisher(String, TOPIC, 10)
        self.count = 0
        self.timer = self.create_timer(1.0, self._tick)
        self.get_logger().info(f"PUBLISHER ready on {TOPIC}")

    def _tick(self):
        self.count += 1
        payload = {
            "host": self.get_namespace(),
            "count": self.count,
            "time": time.time(),
            "msg": f"Hello from pub #{self.count}",
        }
        msg = String()
        msg.data = json.dumps(payload)
        self.pub.publish(msg)
        self.get_logger().info(f"PUB #{self.count}")


class SubNode(Node):
    def __init__(self):
        super().__init__("comm_test_sub")
        self.sub = self.create_subscription(String, TOPIC, self._on_msg, 10)
        self.get_logger().info(f"SUBSCRIBER ready on {TOPIC}")

    def _on_msg(self, msg: String):
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            data = {"raw": msg.data}
        self.get_logger().info(f"RECV: {json.dumps(data)}")


class BothNode(Node):
    def __init__(self):
        super().__init__("comm_test_both")
        self.sub = self.create_subscription(String, TOPIC, self._on_msg, 10)
        self.pub = self.create_publisher(String, TOPIC, 10)
        self.count = 0
        self.timer = self.create_timer(1.0, self._tick)
        self.get_logger().info(f"BOTH (pub+sub) ready on {TOPIC}")

    def _tick(self):
        self.count += 1
        msg = String()
        msg.data = json.dumps({"host": "self", "count": self.count})
        self.pub.publish(msg)
        self.get_logger().info(f"PUB #{self.count}")

    def _on_msg(self, msg: String):
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            data = {"raw": msg.data}
        self.get_logger().info(f"RECV: {json.dumps(data)}")


def main():
    parser = argparse.ArgumentParser(description="ROS2 cross-machine comm test")
    parser.add_argument("--pub", action="store_true")
    parser.add_argument("--sub", action="store_true")
    parser.add_argument("--both", action="store_true")
    parser.add_argument("--timeout", type=int, default=15)
    args = parser.parse_args()

    rclpy.init()

    if args.pub:
        node = PubNode()
    elif args.sub:
        node = SubNode()
    else:
        node = BothNode()

    try:
        print(f"\n  Running for {args.timeout}s... Press Ctrl+C to stop earlier.\n")
        rclpy.spin_once(node, timeout_sec=0.1)
        start = time.time()
        while rclpy.ok() and (time.time() - start) < args.timeout:
            rclpy.spin_once(node, timeout_sec=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
