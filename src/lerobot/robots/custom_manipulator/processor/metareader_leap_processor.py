from __future__ import annotations

from dataclasses import dataclass

from lerobot.configs.types import PipelineFeatureType, PolicyFeature
from lerobot.processor import EnvTransition, ProcessorStep, ProcessorStepRegistry

from ..grippers.config_leap_hand import DEFAULT_COMMAND_INDEX_BY_LINK_NAME, _default_leap_urdf_path
from ..grippers.leap_hand import _resolve_urdf_path
from ..grippers.leap_hand_dexpilot import LeapHandDexPilotRetargeter


@ProcessorStepRegistry.register("metareader_leap_dexpilot")
@dataclass
class MetaReaderLeapDexpilot(ProcessorStep):
    urdf_path: str | None = None
    scaling_factor: float = 1.6
    low_pass_alpha: float = 0.2
    has_joint_limits: bool = True
    project_dist: float = 0.03
    escape_dist: float = 0.05

    def __post_init__(self) -> None:
        resolved_urdf_path = _resolve_urdf_path(self.urdf_path or _default_leap_urdf_path())
        self._retargeter = LeapHandDexPilotRetargeter(
            urdf_path=resolved_urdf_path,
            command_index_by_link_name=DEFAULT_COMMAND_INDEX_BY_LINK_NAME,
            scaling_factor=self.scaling_factor,
            low_pass_alpha=self.low_pass_alpha,
            has_joint_limits=self.has_joint_limits,
            project_dist=self.project_dist,
            escape_dist=self.escape_dist,
        )
        self._last_gripper_action: dict[str, float] | None = None

    def __call__(self, transition: EnvTransition) -> EnvTransition:
        action = transition["action"]
        if action is None:
            return transition

        filtered_action = {
            key: value
            for key, value in action.items()
            if not (
                key.startswith("wrist.position.")
                or key.startswith("thumb.position.")
                or key.startswith("index.position.")
                or key.startswith("middle.position.")
                or key.startswith("ring.position.")
                or key.startswith("little.position.")
                or key == "hand_tracking_valid"
            )
        }

        gripper_action = self._last_gripper_action
        if float(action.get("hand_tracking_valid", 0.0)):
            gripper_action = dict(self._retargeter.retarget_to_action(action))
            self._last_gripper_action = gripper_action

        if gripper_action is not None:
            filtered_action.update(gripper_action)

        transition["action"] = filtered_action
        return transition

    def reset(self) -> None:
        self._retargeter.reset()
        self._last_gripper_action = None

    def transform_features(
        self, features: dict[PipelineFeatureType, dict[str, PolicyFeature]]
    ) -> dict[PipelineFeatureType, dict[str, PolicyFeature]]:
        return features
