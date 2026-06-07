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
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from rclpy.node import Node

if TYPE_CHECKING:
    from lerobot.robots.custom_manipulator.custom_manipulator import CustomManipulator


_INTRINSICS_WARNING_EMITTED = False


@dataclass(frozen=True)
class _CameraPublishers:
    image: Any
    depth: Any | None
    camera_info: Any | None
    image_topic: str
    depth_topic: str | None
    camera_info_topic: str | None
    frame_id: str


def _topic_or_default(topic_map: Mapping[str, str], camera_name: str, default_topic: str) -> str:
    return topic_map.get(camera_name) or default_topic


def _read_latest_depth(camera: Any, max_age_ms: int) -> Any | None:
    if not hasattr(camera, "read_latest_depth"):
        return None
    try:
        return camera.read_latest_depth(max_age_ms=max_age_ms)
    except Exception:
        return None


def _read_rgbd(camera: Any, timeout_ms: int, max_age_ms: int) -> tuple[Any | None, Any | None]:
    try:
        frame = camera.async_read(timeout_ms=timeout_ms)
    except Exception:
        return None, None
    if hasattr(camera, "read_latest_rgbd"):
        try:
            color_frame, depth_frame = camera.read_latest_rgbd(max_age_ms=max_age_ms)
            return color_frame, depth_frame
        except Exception:
            return frame, None
    return frame, _read_latest_depth(camera, max_age_ms=max_age_ms)


def _camera_intrinsics(camera: Any) -> dict[str, Any] | None:
    if not hasattr(camera, "get_color_intrinsics"):
        return None
    try:
        intrinsics = camera.get_color_intrinsics()
    except Exception as exc:
        global _INTRINSICS_WARNING_EMITTED
        if not _INTRINSICS_WARNING_EMITTED:
            logging.warning(
                "Camera intrinsics unavailable; CameraInfo will not be published: %s: %s",
                type(exc).__name__,
                exc,
            )
            _INTRINSICS_WARNING_EMITTED = True
        return None
    return intrinsics if isinstance(intrinsics, dict) else None


def _build_camera_info_msg(camera: Any, stamp: Any, frame_id: str) -> Any | None:
    from sensor_msgs.msg import CameraInfo

    intrinsics = _camera_intrinsics(camera)
    if intrinsics is None:
        return None

    fx = float(intrinsics["fx"])
    fy = float(intrinsics["fy"])
    ppx = float(intrinsics["ppx"])
    ppy = float(intrinsics["ppy"])
    width = int(intrinsics["width"])
    height = int(intrinsics["height"])

    msg = CameraInfo()
    msg.header.stamp = stamp
    msg.header.frame_id = frame_id
    msg.width = width
    msg.height = height
    msg.distortion_model = str(intrinsics.get("distortion_model", "plumb_bob"))
    msg.d = [float(value) for value in intrinsics.get("distortion_coefficients", [])]
    msg.k = [fx, 0.0, ppx, 0.0, fy, ppy, 0.0, 0.0, 1.0]
    msg.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    msg.p = [fx, 0.0, ppx, 0.0, 0.0, fy, ppy, 0.0, 0.0, 0.0, 1.0, 0.0]
    return msg


def _build_depth_msg(depth: Any, stamp: Any, frame_id: str) -> Any | None:
    import numpy as np
    from sensor_msgs.msg import Image

    if depth is None or not hasattr(depth, "shape"):
        return None
    if len(depth.shape) != 2:
        return None

    depth_array = np.ascontiguousarray(depth)
    if depth_array.dtype == np.uint16:
        encoding = "16UC1"
    elif depth_array.dtype == np.float32:
        encoding = "32FC1"
    else:
        depth_array = depth_array.astype(np.uint16, copy=False)
        encoding = "16UC1"

    msg = Image()
    msg.header.stamp = stamp
    msg.header.frame_id = frame_id
    msg.height = int(depth_array.shape[0])
    msg.width = int(depth_array.shape[1])
    msg.encoding = encoding
    msg.is_bigendian = False
    msg.step = int(depth_array.strides[0])
    msg.data = depth_array.tobytes()
    return msg


def _build_static_transform_msg(
    node: Node, camera_name: str, frame_id: str, config: Mapping[str, Any]
) -> Any:
    from geometry_msgs.msg import TransformStamped

    parent_frame_id = str(config.get("parent_frame_id") or "base_link")
    child_frame_id = str(config.get("child_frame_id") or frame_id or camera_name)
    translation = list(config.get("translation") or [0.0, 0.0, 0.0])
    rotation = list(config.get("rotation_xyzw") or [0.0, 0.0, 0.0, 1.0])
    if len(translation) != 3:
        raise ValueError(f"camera_static_tf_map[{camera_name!r}].translation must have 3 values.")
    if len(rotation) != 4:
        raise ValueError(f"camera_static_tf_map[{camera_name!r}].rotation_xyzw must have 4 values.")

    msg = TransformStamped()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.header.frame_id = parent_frame_id
    msg.child_frame_id = child_frame_id
    msg.transform.translation.x = float(translation[0])
    msg.transform.translation.y = float(translation[1])
    msg.transform.translation.z = float(translation[2])
    msg.transform.rotation.x = float(rotation[0])
    msg.transform.rotation.y = float(rotation[1])
    msg.transform.rotation.z = float(rotation[2])
    msg.transform.rotation.w = float(rotation[3])
    return msg


def _publish_static_transforms(
    *,
    node: Node,
    frame_id_map: Mapping[str, str],
    static_tf_map: Mapping[str, Mapping[str, Any]],
) -> Any | None:
    if not static_tf_map:
        return None
    try:
        from tf2_ros import StaticTransformBroadcaster
    except Exception as exc:
        logging.warning("camera_static_tf_map configured but tf2_ros is unavailable: %s", exc)
        return None

    transforms = []
    for camera_name, config in static_tf_map.items():
        frame_id = frame_id_map.get(camera_name) or str(config.get("child_frame_id") or camera_name)
        try:
            transforms.append(_build_static_transform_msg(node, camera_name, frame_id, config))
        except Exception as exc:
            logging.warning("Skipping static TF for camera '%s': %s", camera_name, exc)

    if not transforms:
        return None

    broadcaster = StaticTransformBroadcaster(node)
    broadcaster.sendTransform(transforms)
    logging.info("Published %d static camera TF transform(s).", len(transforms))
    return broadcaster


def start_camera_publisher(
    *,
    robot: CustomManipulator,
    topic_map: dict[str, str],
    depth_topic_map: dict[str, str] | None = None,
    camera_info_topic_map: dict[str, str] | None = None,
    frame_id_map: dict[str, str] | None = None,
    static_tf_map: Mapping[str, Mapping[str, Any]] | None = None,
    fps: float,
    jpeg_quality: int,
    node: Node,
) -> Callable[[], None]:
    """Start a background thread that publishes camera frames as ROS2 CompressedImage.

    @param robot Connected CustomManipulator with cameras already open.
    @param topic_map Mapping from BT camera name to ROS topic name.
    @param depth_topic_map Optional mapping from BT camera name to ROS Image depth topic.
    @param camera_info_topic_map Optional mapping from BT camera name to ROS CameraInfo topic.
    @param frame_id_map Optional mapping from BT camera name to ROS frame_id.
    @param static_tf_map Optional static TF config per BT camera name.
    @param fps Publishing rate in Hz.
    @param jpeg_quality JPEG quality 0-100.
    @param node ROS2 node used to create publishers.
    @return A stop function that signals the thread to exit.
    """
    import cv2
    from sensor_msgs.msg import CameraInfo, CompressedImage, Image

    stop_event = threading.Event()
    publishers: dict[str, _CameraPublishers] = {}
    depth_topic_map = depth_topic_map or {}
    camera_info_topic_map = camera_info_topic_map or {}
    frame_id_map = frame_id_map or {}
    static_tf_map = static_tf_map or {}

    for bt_cam_name, ros_topic in topic_map.items():
        if bt_cam_name not in robot.cameras:
            logging.warning(
                "Camera publish map references '%s' but robot has no such camera. Available: %s",
                bt_cam_name,
                sorted(robot.cameras),
            )
            continue
        depth_topic = depth_topic_map.get(bt_cam_name)
        camera_info_topic = camera_info_topic_map.get(bt_cam_name)
        frame_id = _topic_or_default(frame_id_map, bt_cam_name, bt_cam_name)
        publishers[bt_cam_name] = _CameraPublishers(
            image=node.create_publisher(CompressedImage, ros_topic, 10),
            depth=node.create_publisher(Image, depth_topic, 10) if depth_topic else None,
            camera_info=node.create_publisher(CameraInfo, camera_info_topic, 10)
            if camera_info_topic
            else None,
            image_topic=ros_topic,
            depth_topic=depth_topic,
            camera_info_topic=camera_info_topic,
            frame_id=frame_id,
        )
        logging.info("Publishing camera '%s' -> %s", bt_cam_name, ros_topic)
        if depth_topic:
            logging.info("Publishing camera '%s' depth -> %s", bt_cam_name, depth_topic)
            camera = robot.cameras[bt_cam_name]
            if not bool(getattr(camera, "use_depth", False)):
                logging.warning(
                    "Depth topic configured for camera '%s' but the camera does not expose use_depth=true.",
                    bt_cam_name,
                )
        if camera_info_topic:
            logging.info("Publishing camera '%s' CameraInfo -> %s", bt_cam_name, camera_info_topic)

    if not publishers:
        logging.warning("No valid camera→topic mappings; camera publisher idle.")
        return stop_event.set

    period_s = 1.0 / max(fps, 0.1)
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)]
    static_tf_broadcaster = _publish_static_transforms(
        node=node,
        frame_id_map={name: spec.frame_id for name, spec in publishers.items()},
        static_tf_map=static_tf_map,
    )

    def _publish_loop() -> None:
        while not stop_event.is_set():
            for bt_cam_name, spec in publishers.items():
                try:
                    camera = robot.cameras[bt_cam_name]
                    # Short timeout so the publisher never blocks the policy
                    # control loop that also reads from the same camera.
                    frame, depth = _read_rgbd(
                        camera,
                        timeout_ms=50,
                        max_age_ms=max(int(period_s * 2000), 100),
                    )
                    if frame is None:
                        continue
                    _, jpeg_bytes = cv2.imencode(
                        ".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), encode_params
                    )
                    msg = CompressedImage()
                    msg.header.stamp = node.get_clock().now().to_msg()
                    msg.header.frame_id = spec.frame_id
                    msg.format = "jpeg"
                    msg.data = jpeg_bytes.tobytes()
                    spec.image.publish(msg)

                    if spec.depth is not None:
                        depth_msg = _build_depth_msg(depth, msg.header.stamp, spec.frame_id)
                        if depth_msg is not None:
                            spec.depth.publish(depth_msg)

                    if spec.camera_info is not None:
                        camera_info_msg = _build_camera_info_msg(camera, msg.header.stamp, spec.frame_id)
                        if camera_info_msg is not None:
                            spec.camera_info.publish(camera_info_msg)
                except Exception as exc:  # noqa: BLE001
                    logging.debug("Skipping camera publish tick: %s", exc)
            stop_event.wait(timeout=period_s)

    thread = threading.Thread(target=_publish_loop, daemon=True, name="camera-publisher")
    thread.start()

    def _stop() -> None:
        _ = static_tf_broadcaster
        stop_event.set()

    return _stop
