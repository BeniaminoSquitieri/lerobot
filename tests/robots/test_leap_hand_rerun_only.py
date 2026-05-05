from unittest.mock import patch

import numpy as np
import pytest

pytest.importorskip("dex_retargeting", reason="dex_retargeting is required for LEAP DexPilot tests")
pytest.importorskip("klampt", reason="klampt is required for LEAP rerun tests")

from lerobot.robots.custom_manipulator.grippers.config_leap_hand import LeapHandConfig
from lerobot.robots.custom_manipulator.grippers.leap_hand import PALM_TO_TARGET_ROT
from lerobot.robots.custom_manipulator.grippers.leap_hand_rerun_only import LeapHandRerunOnly


class _FakeDebugTools:
    def __init__(self, *args, **kwargs):
        self.root_frame_name = kwargs["root_frame"].getName()
        self.logged_targets = []
        self.logged_states = []

    def poll(self):
        return None

    def close(self):
        return None

    def log_state(self, *args, **kwargs):
        self.logged_states.append((args, kwargs))
        return None

    def log_targets(self, *args, **kwargs):
        self.logged_targets.append((args, kwargs))
        return None


def _make_valid_hand_action() -> dict[str, float]:
    return {
        "hand_tracking_valid": 1.0,
        "wrist.position.x": 0.0,
        "wrist.position.y": 0.0,
        "wrist.position.z": -0.10,
        "thumb.position.x": 0.03,
        "thumb.position.y": -0.03,
        "thumb.position.z": 0.02,
        "index.position.x": 0.06,
        "index.position.y": 0.01,
        "index.position.z": 0.08,
        "middle.position.x": 0.03,
        "middle.position.y": 0.01,
        "middle.position.z": 0.10,
        "ring.position.x": -0.01,
        "ring.position.y": 0.0,
        "ring.position.z": 0.09,
        "little.position.x": -0.03,
        "little.position.y": -0.01,
        "little.position.z": 0.08,
    }


def test_leap_hand_rerun_only_uses_dexpilot_without_serial_hardware():
    with patch(
        "lerobot.robots.custom_manipulator.grippers.leap_hand_rerun_only.LeapHandDebugTools",
        _FakeDebugTools,
    ):
        simulator = LeapHandRerunOnly(LeapHandConfig())
        before = simulator._current_model_joint_values().copy()
        simulator.apply_action(_make_valid_hand_action())
        after = simulator._current_model_joint_values()
        debug = simulator._debug
        simulator.close()

    assert not np.allclose(before, after)
    assert np.isfinite(after).all()
    assert debug.root_frame_name == "base"
    assert debug.logged_targets


def test_leap_hand_rerun_only_reports_tip_head_positions():
    with patch(
        "lerobot.robots.custom_manipulator.grippers.leap_hand_rerun_only.LeapHandDebugTools",
        _FakeDebugTools,
    ):
        simulator = LeapHandRerunOnly(LeapHandConfig())
        tip_values = simulator._get_fingertips_from_current_model_state()
        debug = simulator._debug
        simulator.close()

    assert debug.logged_states

    palm_rotation, palm_translation = simulator.palm_frame.getTransform()
    palm_rotation_inv = simulator._so3.inv(palm_rotation)
    palm_translation = np.asarray(palm_translation, dtype=float)
    expected = {}
    for tip, link_name in simulator.config.tip_point_link_names.items():
        link = simulator.model.link(link_name)
        _, tip_translation = link.getTransform()
        tip_translation = np.asarray(tip_translation, dtype=float)
        point = np.asarray(
            simulator._so3.apply(
                palm_rotation_inv,
                simulator._vectorops.sub(tip_translation.tolist(), palm_translation.tolist()),
            )
        )
        expected[tip] = (
            PALM_TO_TARGET_ROT.T @ (point - simulator._palm_center_offset)
        ) / simulator.config.tip_scale_factors[tip]

    for tip, point in expected.items():
        for axis, value in zip("xyz", point, strict=True):
            assert tip_values[f"{tip}.position.{axis}"] == pytest.approx(float(value))
