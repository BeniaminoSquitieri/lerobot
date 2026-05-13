import numpy as np

from lerobot.teleoperators.metareader import MetaReaderConfig, MetaReaderTeleoperator
from lerobot.teleoperators.metareader.metareader import METAREADER_TRANSFORM
from lerobot.utils.rotation import Rotation as R
from metareader.receiver import HandState, JointState, Pose, TelemetryFrame


def _make_joint(position: tuple[float, float, float], *, tracked: bool = True) -> JointState:
    pose = Pose(position=position, orientation=(0.0, 0.0, 0.0, 1.0), valid=tracked)
    return JointState(tracked=tracked, pose=pose)


def _make_frame(*, include_ring: bool = True, include_little: bool = False) -> TelemetryFrame:
    palm_orientation = tuple(R.from_matrix(METAREADER_TRANSFORM.T).as_quat())
    right_hand = HandState(
        tracked=True,
        wrist=JointState(
            tracked=True,
            pose=Pose(position=(0.0, 0.0, -0.1), orientation=(0.0, 0.0, 0.0, 1.0), valid=True),
        ),
        palm=JointState(
            tracked=True,
            pose=Pose(position=(0.0, 0.0, 0.0), orientation=palm_orientation, valid=True),
        ),
        fingertips={
            "thumb_tip": _make_joint((0.03, 0.01, 0.02)),
            "index_tip": _make_joint((0.05, -0.02, 0.07)),
            "middle_tip": _make_joint((0.03, 0.0, 0.09)),
            "ring_tip": _make_joint((0.0, -0.01, 0.08), tracked=include_ring),
            "little_tip": _make_joint((-0.02, -0.01, 0.07), tracked=include_little),
        },
    )
    return TelemetryFrame(
        sequence=1,
        transport="mock",
        tracking_valid=True,
        display_time_ns=0,
        head_pose=Pose(),
        left_hand=HandState(),
        right_hand=right_hand,
        status=None,
        raw={},
    )


def test_frame_to_action_adds_wrist_and_tracking_valid():
    teleop = MetaReaderTeleoperator(MetaReaderConfig())
    action = teleop._frame_to_action(_make_frame(include_ring=True, include_little=False))

    wrist_expected = METAREADER_TRANSFORM @ np.array([0.0, 0.0, -0.1], dtype=float)
    thumb_expected = METAREADER_TRANSFORM @ np.array([0.03, 0.01, 0.02], dtype=float)

    assert action["hand_tracking_valid"] == 1.0
    assert np.allclose(
        [action[f"wrist.position.{axis}"] for axis in "xyz"],
        wrist_expected,
    )
    assert np.allclose(
        [action[f"thumb.position.{axis}"] for axis in "xyz"],
        thumb_expected,
    )


def test_frame_to_action_ignores_little_for_tracking_validity():
    teleop = MetaReaderTeleoperator(MetaReaderConfig())

    valid_without_little = teleop._frame_to_action(_make_frame(include_ring=True, include_little=False))
    invalid_without_ring = teleop._frame_to_action(_make_frame(include_ring=False, include_little=True))

    assert valid_without_little["hand_tracking_valid"] == 1.0
    assert invalid_without_ring["hand_tracking_valid"] == 0.0
