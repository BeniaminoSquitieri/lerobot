import pytest
from lerobot_bt_python.bt_generation.ros_plan_client import request_plan_from_ros_service

def test_ros_plan_client_import_error(monkeypatch):
    monkeypatch.setitem(__import__("builtins").__dict__, "__import__", lambda name, *a, **k: (_ for _ in ()).throw(ImportError()) if name == "rclpy" else __import__(name, *a, **k))
    with pytest.raises(RuntimeError, match="rclpy is required for ROS planning"):
        request_plan_from_ros_service("make_sandwich", {"foo": "bar"})
