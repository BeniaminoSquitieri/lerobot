import numpy as np

from lerobot.robots.custom_manipulator.processor.metaquest_processor import ClutchProcessor
from lerobot.types import TransitionKey


def _transition(*, action_pos=(0.0, 0.0, 0.0), action_rot=(0.0, 0.0, 0.0), obs_pos=(0.5, 0.0, 0.4), obs_rot=(0.0, 0.0, 0.0)):
    return {
        TransitionKey.ACTION: {
            "position.x": float(action_pos[0]),
            "position.y": float(action_pos[1]),
            "position.z": float(action_pos[2]),
            "orientation.x": float(action_rot[0]),
            "orientation.y": float(action_rot[1]),
            "orientation.z": float(action_rot[2]),
            "gripper": 1.0,
        },
        TransitionKey.OBSERVATION: {
            "position.x": float(obs_pos[0]),
            "position.y": float(obs_pos[1]),
            "position.z": float(obs_pos[2]),
            "orientation.x": float(obs_rot[0]),
            "orientation.y": float(obs_rot[1]),
            "orientation.z": float(obs_rot[2]),
        },
    }


def test_clutch_processor_first_engaged_frame_starts_from_robot_pose():
    processor = ClutchProcessor()

    result = processor(_transition(action_pos=(0.8, -0.2, 0.6), action_rot=(0.4, -0.3, 0.2)))

    assert np.allclose(
        [result[TransitionKey.ACTION][f"position.{axis}"] for axis in "xyz"],
        [0.5, 0.0, 0.4],
    )
    assert np.allclose(
        [result[TransitionKey.ACTION][f"orientation.{axis}"] for axis in "xyz"],
        [0.0, 0.0, 0.0],
    )


def test_clutch_processor_scales_and_clips_large_relative_motion():
    processor = ClutchProcessor(
        translation_scale=0.5,
        rotation_scale=0.5,
        max_translation_m=0.1,
        max_rotation_rad=0.2,
        translation_deadzone_m=0.0,
        rotation_deadzone_rad=0.0,
    )

    processor(_transition(action_pos=(0.0, 0.0, 0.0), action_rot=(0.0, 0.0, 0.0)))
    result = processor(_transition(action_pos=(1.0, 0.0, 0.0), action_rot=(1.0, 0.0, 0.0)))

    assert np.allclose(
        [result[TransitionKey.ACTION][f"position.{axis}"] for axis in "xyz"],
        [0.6, 0.0, 0.4],
    )

    clipped_rotvec = np.array([result[TransitionKey.ACTION][f"orientation.{axis}"] for axis in "xyz"])
    assert np.isclose(np.linalg.norm(clipped_rotvec), 0.2)


def test_clutch_processor_reset_reanchors_on_next_engage():
    processor = ClutchProcessor(translation_scale=1.0, translation_deadzone_m=0.0)

    processor(_transition(action_pos=(0.0, 0.0, 0.0)))
    processor(_transition(action_pos=(0.2, 0.0, 0.0)))
    processor.reset()
    result = processor(_transition(action_pos=(1.0, 1.0, 1.0), obs_pos=(0.3, -0.1, 0.2)))

    assert np.allclose(
        [result[TransitionKey.ACTION][f"position.{axis}"] for axis in "xyz"],
        [0.3, -0.1, 0.2],
    )
