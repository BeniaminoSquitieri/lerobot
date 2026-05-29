"""@file camera_publisher.py
@brief Background ROS2 publisher for live robot camera frames.

The external VLM verifier subscribes to camera topics rather than opening the
RealSense devices directly (which would conflict with the BT server's own
usage). This module owns the thread that snapshots frames from the robot
camera handles and republishes them as `sensor_msgs/CompressedImage`.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Any, Callable

from rclpy.node import Node

if TYPE_CHECKING:
    from lerobot.robots.custom_manipulator.custom_manipulator import CustomManipulator


def start_camera_publisher(
    *,
    robot: "CustomManipulator",
    topic_map: dict[str, str],
    fps: float,
    jpeg_quality: int,
    node: Node,
) -> Callable[[], None]:
    """Start a background thread that publishes camera frames as ROS2 CompressedImage.

    @param robot Connected CustomManipulator with cameras already open.
    @param topic_map Mapping from BT camera name to ROS topic name.
    @param fps Publishing rate in Hz.
    @param jpeg_quality JPEG quality 0-100.
    @param node ROS2 node used to create publishers.
    @return A stop function that signals the thread to exit.
    """
    import cv2
    from sensor_msgs.msg import CompressedImage

    stop_event = threading.Event()
    publishers: dict[str, Any] = {}

    for bt_cam_name, ros_topic in topic_map.items():
        if bt_cam_name not in robot.cameras:
            logging.warning(
                "Camera publish map references '%s' but robot has no such camera. Available: %s",
                bt_cam_name,
                sorted(robot.cameras),
            )
            continue
        pub = node.create_publisher(CompressedImage, ros_topic, 10)
        publishers[bt_cam_name] = pub
        logging.info("Publishing camera '%s' → %s", bt_cam_name, ros_topic)

    if not publishers:
        logging.warning("No valid camera→topic mappings; camera publisher idle.")
        return stop_event.set

    period_s = 1.0 / max(fps, 0.1)
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)]

    def _publish_loop() -> None:
        while not stop_event.is_set():
            for bt_cam_name, pub in publishers.items():
                try:
                    camera = robot.cameras[bt_cam_name]
                    # Short timeout so the publisher never blocks the policy
                    # control loop that also reads from the same camera.
                    frame = camera.async_read(timeout_ms=50)
                    if frame is None:
                        continue
                    _, jpeg_bytes = cv2.imencode(".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), encode_params)
                    msg = CompressedImage()
                    msg.header.stamp = node.get_clock().now().to_msg()
                    msg.header.frame_id = bt_cam_name
                    msg.format = "jpeg"
                    msg.data = jpeg_bytes.tobytes()
                    pub.publish(msg)
                except Exception:
                    pass  # Silently skip if camera is busy or no frame available
            stop_event.wait(timeout=period_s)

    thread = threading.Thread(target=_publish_loop, daemon=True, name="camera-publisher")
    thread.start()
    return stop_event.set
