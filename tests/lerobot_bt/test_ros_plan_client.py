import builtins

import pytest

from lerobot_bt_python.bt_generation.ros_plan_client import request_plan_from_ros_service


def test_ros_plan_client_import_error(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "rclpy" or name.startswith("rclpy."):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError, match="rclpy is required for ROS planning"):
        request_plan_from_ros_service("make_sandwich", {"foo": "bar"})
