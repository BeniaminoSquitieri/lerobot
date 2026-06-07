import ast
import importlib
import sys
import types
from pathlib import Path

import numpy as np


class _Header:
    def __init__(self) -> None:
        self.stamp = None
        self.frame_id = ""


class _CameraInfo:
    def __init__(self) -> None:
        self.header = _Header()
        self.width = 0
        self.height = 0
        self.distortion_model = ""
        self.d = []
        self.k = []
        self.r = []
        self.p = []


class _Image:
    def __init__(self) -> None:
        self.header = _Header()
        self.height = 0
        self.width = 0
        self.encoding = ""
        self.is_bigendian = False
        self.step = 0
        self.data = b""


class _CompressedImage:
    def __init__(self) -> None:
        self.header = _Header()
        self.format = ""
        self.data = b""


class _Node:
    pass


class _FakeCamera:
    use_depth = True

    def __init__(self) -> None:
        self.color = np.zeros((3, 4, 3), dtype=np.uint8)
        self.depth = np.array(
            [
                [1000, 1001, 1002, 1003],
                [2000, 2001, 2002, 2003],
                [3000, 3001, 3002, 3003],
            ],
            dtype=np.uint16,
        )
        self.async_timeout_ms = None
        self.rgbd_max_age_ms = None

    def async_read(self, *, timeout_ms: int) -> np.ndarray:
        self.async_timeout_ms = timeout_ms
        return self.color

    def read_latest_rgbd(self, *, max_age_ms: int) -> tuple[np.ndarray, np.ndarray]:
        self.rgbd_max_age_ms = max_age_ms
        return self.color, self.depth

    def get_color_intrinsics(self) -> dict[str, object]:
        return {
            "width": 4,
            "height": 3,
            "fx": 120.0,
            "fy": 121.0,
            "ppx": 1.5,
            "ppy": 1.0,
            "distortion_model": "plumb_bob",
            "distortion_coefficients": [0.1, 0.2, 0.3, 0.4, 0.5],
        }


def _import_camera_publisher(monkeypatch):
    rclpy_module = types.ModuleType("rclpy")
    rclpy_node_module = types.ModuleType("rclpy.node")
    rclpy_node_module.Node = _Node
    sensor_msgs_module = types.ModuleType("sensor_msgs")
    sensor_msgs_msg_module = types.ModuleType("sensor_msgs.msg")
    sensor_msgs_msg_module.CameraInfo = _CameraInfo
    sensor_msgs_msg_module.CompressedImage = _CompressedImage
    sensor_msgs_msg_module.Image = _Image

    monkeypatch.setitem(sys.modules, "rclpy", rclpy_module)
    monkeypatch.setitem(sys.modules, "rclpy.node", rclpy_node_module)
    monkeypatch.setitem(sys.modules, "sensor_msgs", sensor_msgs_module)
    monkeypatch.setitem(sys.modules, "sensor_msgs.msg", sensor_msgs_msg_module)
    sys.modules.pop("lerobot_bt_python.perception.camera_publisher", None)
    return importlib.import_module("lerobot_bt_python.perception.camera_publisher")


def test_read_rgbd_prefers_camera_rgbd_api(monkeypatch):
    module = _import_camera_publisher(monkeypatch)
    camera = _FakeCamera()

    color, depth = module._read_rgbd(camera, timeout_ms=7, max_age_ms=42)

    assert color is camera.color
    assert depth is camera.depth
    assert camera.async_timeout_ms == 7
    assert camera.rgbd_max_age_ms == 42


def test_build_camera_info_msg_uses_color_intrinsics(monkeypatch):
    module = _import_camera_publisher(monkeypatch)
    stamp = object()

    msg = module._build_camera_info_msg(_FakeCamera(), stamp, "panda_wrist_camera")

    assert msg is not None
    assert msg.header.stamp is stamp
    assert msg.header.frame_id == "panda_wrist_camera"
    assert msg.width == 4
    assert msg.height == 3
    assert msg.distortion_model == "plumb_bob"
    assert msg.d == [0.1, 0.2, 0.3, 0.4, 0.5]
    assert msg.k == [120.0, 0.0, 1.5, 0.0, 121.0, 1.0, 0.0, 0.0, 1.0]
    assert msg.p == [120.0, 0.0, 1.5, 0.0, 0.0, 121.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]


def test_build_depth_msg_publishes_lossless_uint16(monkeypatch):
    module = _import_camera_publisher(monkeypatch)
    camera = _FakeCamera()
    stamp = object()

    msg = module._build_depth_msg(camera.depth, stamp, "panda_wrist_camera")

    assert msg is not None
    assert msg.header.stamp is stamp
    assert msg.header.frame_id == "panda_wrist_camera"
    assert msg.height == 3
    assert msg.width == 4
    assert msg.encoding == "16UC1"
    assert msg.is_bigendian is False
    assert msg.step == camera.depth.strides[0]
    assert msg.data == camera.depth.tobytes()


_CORE_REALSENSE = (
    Path(__file__).resolve().parents[2] / "src" / "lerobot" / "cameras" / "realsense" / "camera_realsense.py"
)


def test_core_realsense_exposes_rgbd_accessors():
    """Regression guard: the republisher depends on these core accessors.

    They were silently dropped once before, which made the depth pipeline
    fail closed on the real robot (zero poses, no crash). Catch any future
    removal here without needing hardware or heavy deps.
    """
    source = _CORE_REALSENSE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    method_names = {
        node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for required in ("get_color_intrinsics", "read_latest_depth", "read_latest_rgbd"):
        assert required in method_names, f"core RealSenseCamera lost method: {required}"


def test_core_realsense_aligns_depth_to_color():
    """Regression guard: depth must be aligned to color so a color-frame mask
    indexes the same pixels in depth. Without rs.align the back-projection is
    wrong and poses are unusable."""
    source = _CORE_REALSENSE.read_text(encoding="utf-8")
    assert "rs.align(rs.stream.color)" in source
    assert "self.rs_align.process(frame)" in source
