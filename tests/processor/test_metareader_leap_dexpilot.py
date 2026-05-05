import numpy as np
import pytest

pytest.importorskip("dex_retargeting", reason="dex_retargeting is required for LEAP DexPilot tests")

from lerobot.processor.converters import create_transition
from lerobot.robots.custom_manipulator.grippers.config_leap_hand import COMMAND_LINK_NAMES
from lerobot.robots.custom_manipulator.grippers.leap_hand import _resolve_urdf_path
from lerobot.robots.custom_manipulator.grippers.leap_hand_dexpilot import (
    LEAP_DEXPILOT_FINGER_TIP_LINK_NAMES,
    LEAP_DEXPILOT_WRIST_LINK_NAME,
    LeapHandDexPilotRetargeter,
)
from lerobot.robots.custom_manipulator.processor.metareader_leap_processor import MetaReaderLeapDexpilot


def _make_valid_hand_action() -> dict[str, float]:
    action = {
        "position.x": 0.1,
        "position.y": -0.2,
        "position.z": 0.3,
        "orientation.x": 0.01,
        "orientation.y": -0.02,
        "orientation.z": 0.03,
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
    return action


def test_leap_dexpilot_helper_builds_and_retargets():
    retargeter = LeapHandDexPilotRetargeter(
        urdf_path=_resolve_urdf_path("/home/panda-user/dex-urdf/robots/hands/leap_hand/leap_hand_right.urdf")
    )

    qpos = retargeter.retarget(_make_valid_hand_action())
    gripper_action = retargeter.qpos_to_action(qpos)

    assert retargeter.wrist_link_name == LEAP_DEXPILOT_WRIST_LINK_NAME == "base"
    assert retargeter.finger_tip_link_names == LEAP_DEXPILOT_FINGER_TIP_LINK_NAMES
    assert retargeter.finger_tip_link_names == (
        "thumb_tip_head",
        "index_tip_head",
        "middle_tip_head",
        "ring_tip_head",
    )
    assert qpos.shape == (16,)
    assert len(retargeter.joint_names) == 16
    assert len(gripper_action) == 16
    assert list(gripper_action) == [f"gripper.{link_name}" for link_name in COMMAND_LINK_NAMES]
    assert np.isfinite(qpos).all()


def test_metareader_leap_dexpilot_preserves_arm_keys_and_holds_last_valid_command():
    step = MetaReaderLeapDexpilot()

    first_transition = create_transition(action=_make_valid_hand_action(), observation={})
    first_result = step(first_transition)
    first_action = first_result["action"]

    assert first_action["position.x"] == pytest.approx(0.1)
    assert first_action["orientation.z"] == pytest.approx(0.03)
    assert "little.position.x" not in first_action
    assert "hand_tracking_valid" not in first_action
    assert all(f"gripper.{link_name}" in first_action for link_name in COMMAND_LINK_NAMES)

    invalid_action = {
        "position.x": -0.4,
        "position.y": 0.2,
        "position.z": 0.5,
        "orientation.x": -0.05,
        "orientation.y": 0.02,
        "orientation.z": 0.01,
        "hand_tracking_valid": 0.0,
        "little.position.x": 99.0,
        "little.position.y": 99.0,
        "little.position.z": 99.0,
    }
    second_result = step(create_transition(action=invalid_action, observation={}))
    second_action = second_result["action"]

    assert second_action["position.x"] == pytest.approx(-0.4)
    assert all(
        second_action[f"gripper.{link_name}"] == pytest.approx(first_action[f"gripper.{link_name}"])
        for link_name in COMMAND_LINK_NAMES
    )

    step.reset()
    reset_result = step(create_transition(action=invalid_action, observation={}))
    assert all(f"gripper.{link_name}" not in reset_result["action"] for link_name in COMMAND_LINK_NAMES)
