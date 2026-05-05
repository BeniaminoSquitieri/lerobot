import numpy as np

from lerobot.robots.custom_manipulator.grippers.leap_hand_debug import LeapHandDebugTools


class _FakeFrame:
    def __init__(self, name: str, rotation: np.ndarray, translation: np.ndarray):
        self._name = name
        self._rotation = np.asarray(rotation, dtype=float).reshape(3, 3)
        self._translation = np.asarray(translation, dtype=float)

    def getName(self):
        return self._name

    def getTransform(self):
        return self._rotation.T.reshape(-1).tolist(), self._translation.tolist()


def test_root_frame_pose_in_palm_center_applies_rotation_and_translation():
    palm_rotation_in_root = np.array(
        [
            [0.0, 0.0, -1.0],
            [0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0],
        ]
    )
    root_frame = _FakeFrame("base", np.eye(3), np.zeros(3))
    palm_frame = _FakeFrame("palm_lower", palm_rotation_in_root, np.array([0.0, 0.038, 0.098]))

    debug = LeapHandDebugTools(
        urdf_path="unused.urdf",
        tip_names=("thumb", "index", "middle", "ring"),
        tip_scale_factors={tip: 1.0 for tip in ("thumb", "index", "middle", "ring")},
        enable_tip_scale_tuner=False,
        enable_rerun_visualization=False,
        palm_frame=palm_frame,
        root_frame=root_frame,
        palm_center_offset=np.zeros(3),
        tips={},
        palm_to_target_rot=np.eye(3),
    )

    rotation, translation = debug._get_root_frame_pose_in_palm_center()

    np.testing.assert_allclose(rotation, palm_rotation_in_root.T)
    np.testing.assert_allclose(translation, palm_rotation_in_root.T @ (-np.array([0.0, 0.038, 0.098])))
