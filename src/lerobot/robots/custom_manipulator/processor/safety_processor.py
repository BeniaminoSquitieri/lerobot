from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from lerobot.configs.types import PipelineFeatureType, PolicyFeature
from lerobot.processor import ProcessorStep, ProcessorStepRegistry
from lerobot.types import EnvTransition, TransitionKey

logger = logging.getLogger(__name__)

try:
    from scipy.spatial.transform import Rotation as R
except ModuleNotFoundError:
    R = None


@ProcessorStepRegistry.register("cartesian_action_safety_processor")
@dataclass
class CartesianActionSafetyProcessor(ProcessorStep):
    """Reject or clip large absolute Cartesian target jumps before sending them to hardware.

    The learned sandwich skills currently emit absolute end-effector targets. If the robot
    starts far from the training distribution, the first target can become a large Cartesian
    jump that the Panda driver will try to realize immediately through IK. This step compares
    the predicted target against the current observation and enforces conservative bounds.
    """

    max_translation_m: float = 0.015
    max_rotation_rad: float = 0.12
    mode: str = "error"

    def __post_init__(self) -> None:
        if self.max_translation_m <= 0:
            raise ValueError("max_translation_m must be > 0.")
        if self.max_rotation_rad <= 0:
            raise ValueError("max_rotation_rad must be > 0.")
        if self.mode not in {"error", "clip"}:
            raise ValueError("mode must be either 'error' or 'clip'.")

    def __call__(self, transition: EnvTransition) -> EnvTransition:
        action = transition.get(TransitionKey.ACTION)
        observation = transition.get(TransitionKey.OBSERVATION)
        if not isinstance(action, dict) or not isinstance(observation, dict):
            return transition

        required_keys = (
            "position.x",
            "position.y",
            "position.z",
            "orientation.x",
            "orientation.y",
            "orientation.z",
        )
        if not all(key in action for key in required_keys) or not all(
            key in observation for key in required_keys
        ):
            return transition

        target_pos = np.array([float(action[f"position.{axis}"]) for axis in "xyz"], dtype=float)
        current_pos = np.array([float(observation[f"position.{axis}"]) for axis in "xyz"], dtype=float)
        pos_delta = target_pos - current_pos
        pos_delta_norm = float(np.linalg.norm(pos_delta))

        if R is None:
            raise ModuleNotFoundError(
                "CartesianActionSafetyProcessor requires scipy. Install the `scipy-dep` extra before using "
                "cartesian_action_safety_processor."
            )

        target_rot = R.from_rotvec([float(action[f"orientation.{axis}"]) for axis in "xyz"])
        current_rot = R.from_rotvec([float(observation[f"orientation.{axis}"]) for axis in "xyz"])
        rot_delta = target_rot * current_rot.inv()
        rot_delta_vec = rot_delta.as_rotvec()
        rot_delta_norm = float(np.linalg.norm(rot_delta_vec))

        if pos_delta_norm <= self.max_translation_m and rot_delta_norm <= self.max_rotation_rad:
            return transition

        message = (
            "Unsafe skill action rejected: "
            f"translation jump={pos_delta_norm:.4f}m (limit {self.max_translation_m:.4f}m), "
            f"rotation jump={rot_delta_norm:.4f}rad (limit {self.max_rotation_rad:.4f}rad). "
            f"Current pose={current_pos.tolist()}, target pose={target_pos.tolist()}."
        )
        if self.mode == "error":
            raise ValueError(message)

        clipped_transition = transition.copy()
        clipped_action = action.copy()

        if pos_delta_norm > self.max_translation_m and pos_delta_norm > 0:
            pos_delta = pos_delta * (self.max_translation_m / pos_delta_norm)
            target_pos = current_pos + pos_delta

        if rot_delta_norm > self.max_rotation_rad and rot_delta_norm > 0:
            rot_delta_vec = rot_delta_vec * (self.max_rotation_rad / rot_delta_norm)
            target_rot = R.from_rotvec(rot_delta_vec) * current_rot

        for axis, value in zip("xyz", target_pos, strict=True):
            clipped_action[f"position.{axis}"] = float(value)
        for axis, value in zip("xyz", target_rot.as_rotvec(), strict=True):
            clipped_action[f"orientation.{axis}"] = float(value)

        logger.warning("%s Clipping action instead of sending the raw target.", message)
        clipped_transition[TransitionKey.ACTION] = clipped_action
        return clipped_transition

    def transform_features(
        self, features: dict[PipelineFeatureType, dict[str, PolicyFeature]]
    ) -> dict[PipelineFeatureType, dict[str, PolicyFeature]]:
        return features
