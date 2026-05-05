from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

from .config_leap_hand import COMMAND_LINK_NAMES, DEFAULT_COMMAND_INDEX_BY_LINK_NAME

LEAP_DEXPILOT_LANDMARK_ORDER = ("wrist", "thumb", "index", "middle", "ring")
LEAP_DEXPILOT_HUMAN_INDEX_BY_LANDMARK = {
    "wrist": 0,
    "thumb": 4,
    "index": 8,
    "middle": 12,
    "ring": 16,
}
LEAP_DEXPILOT_WRIST_LINK_NAME = "base"
LEAP_DEXPILOT_FINGER_TIP_LINK_NAMES = (
    "thumb_tip_head",
    "index_tip_head",
    "middle_tip_head",
    "ring_tip_head",
)
LEAP_PALM_TO_ROBOT_FRAME = np.array([[0, 0, -1], [-1, 0, 0], [0, 1, 0]], dtype=np.float32)
LEAP_GRIPPER_ACTION_KEYS = tuple(f"gripper.{link_name}" for link_name in COMMAND_LINK_NAMES)


def _require_dex_retargeting():
    try:
        from dex_retargeting.retargeting_config import RetargetingConfig
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "LEAP DexPilot retargeting requires the optional `dex_retargeting` package."
        ) from exc

    return RetargetingConfig


class LeapHandDexPilotRetargeter:
    def __init__(
        self,
        *,
        urdf_path: str,
        command_index_by_link_name: dict[str, int] | None = None,
        wrist_link_name: str = LEAP_DEXPILOT_WRIST_LINK_NAME,
        finger_tip_link_names: tuple[str, ...] = LEAP_DEXPILOT_FINGER_TIP_LINK_NAMES,
        scaling_factor: float = 1.6,
        low_pass_alpha: float = 0.2,
        has_joint_limits: bool = True,
        project_dist: float = 0.03,
        escape_dist: float = 0.05,
    ):
        self.urdf_path = str(Path(urdf_path).expanduser().resolve())
        self.command_index_by_link_name = dict(
            command_index_by_link_name or DEFAULT_COMMAND_INDEX_BY_LINK_NAME
        )
        self.command_link_names = tuple(
            link_name
            for link_name, _ in sorted(self.command_index_by_link_name.items(), key=lambda item: item[1])
        )
        self.command_action_keys = tuple(f"gripper.{link_name}" for link_name in self.command_link_names)
        self.wrist_link_name = wrist_link_name
        self.finger_tip_link_names = tuple(finger_tip_link_names)
        self._human_index_by_tip_name = {
            landmark: LEAP_DEXPILOT_HUMAN_INDEX_BY_LANDMARK[landmark]
            for landmark in LEAP_DEXPILOT_LANDMARK_ORDER[1:]
        }

        RetargetingConfig = _require_dex_retargeting()
        self.retargeting = RetargetingConfig.from_dict(
            {
                "type": "DexPilot",
                "urdf_path": self.urdf_path,
                "wrist_link_name": self.wrist_link_name,
                "finger_tip_link_names": list(self.finger_tip_link_names),
                "scaling_factor": scaling_factor,
                "low_pass_alpha": low_pass_alpha,
                "has_joint_limits": has_joint_limits,
                "project_dist": project_dist,
                "escape_dist": escape_dist,
            }
        ).build()

        self._retarget_joint_name_to_command_link_name = self._resolve_command_links()
        self._retarget_to_command_index = tuple(
            self.command_index_by_link_name[self._retarget_joint_name_to_command_link_name[joint_name]]
            for joint_name in self.retargeting.joint_names
        )
        expected = list(range(len(self.command_link_names)))
        if sorted(self._retarget_to_command_index) != expected:
            raise RuntimeError(
                "Failed to resolve a full LEAP command permutation from DexPilot retargeting joints. "
                f"Expected indices {expected}, got {sorted(self._retarget_to_command_index)}."
            )

        self._seeded = False

    @property
    def joint_names(self) -> list[str]:
        return self.retargeting.joint_names

    @property
    def target_link_human_indices(self) -> np.ndarray:
        return self.retargeting.optimizer.target_link_human_indices

    def reset(self) -> None:
        self.retargeting.reset()
        self._seeded = False

    def seed_from_qpos(self, model_qpos: np.ndarray) -> None:
        self.retargeting.set_qpos(np.asarray(model_qpos, dtype=np.float32))
        self._seeded = True

    def action_to_reference_value(self, action: dict[str, float]) -> np.ndarray:
        landmark_positions = self.action_to_robot_frame_positions(action)
        indices = self.target_link_human_indices
        unknown_indices = set(np.unique(indices).tolist()) - set(landmark_positions)
        if unknown_indices:
            raise ValueError(
                "DexPilot requested unsupported human landmark indices "
                f"{sorted(unknown_indices)}. Supported indices: {sorted(landmark_positions)}."
            )

        ref_value = np.empty((indices.shape[1], 3), dtype=np.float32)
        for column, (origin_index, task_index) in enumerate(zip(indices[0], indices[1], strict=True)):
            ref_value[column] = landmark_positions[task_index] - landmark_positions[origin_index]
        return ref_value

    def action_to_robot_frame_positions(self, action: dict[str, float]) -> dict[int, np.ndarray]:
        wrist_position = np.asarray(
            [float(action[f"wrist.position.{axis}"]) for axis in "xyz"],
            dtype=np.float32,
        )
        positions: dict[int, np.ndarray] = {
            LEAP_DEXPILOT_HUMAN_INDEX_BY_LANDMARK["wrist"]: np.zeros(3, dtype=np.float32)
        }
        for landmark in LEAP_DEXPILOT_LANDMARK_ORDER[1:]:
            tip_position = np.asarray(
                [float(action[f"{landmark}.position.{axis}"]) for axis in "xyz"],
                dtype=np.float32,
            )
            positions[LEAP_DEXPILOT_HUMAN_INDEX_BY_LANDMARK[landmark]] = (
                LEAP_PALM_TO_ROBOT_FRAME @ (tip_position - wrist_position)
            ).astype(np.float32)
        return positions

    def retarget(self, action: dict[str, float], *, seed_qpos: np.ndarray | None = None) -> np.ndarray:
        if not self._seeded and seed_qpos is not None:
            self.seed_from_qpos(seed_qpos)

        qpos = np.asarray(self.retargeting.retarget(self.action_to_reference_value(action)), dtype=np.float32)
        self._seeded = True
        return qpos

    def qpos_to_command_values(self, qpos: np.ndarray) -> np.ndarray:
        qpos = np.asarray(qpos, dtype=np.float32)
        if qpos.shape != (len(self.retargeting.joint_names),):
            raise ValueError(
                "Expected DexPilot qpos shape "
                f"{(len(self.retargeting.joint_names),)}, got {qpos.shape}."
            )

        command_values = np.empty(len(self.command_link_names), dtype=np.float32)
        for retarget_index, command_index in enumerate(self._retarget_to_command_index):
            command_values[command_index] = qpos[retarget_index]
        return command_values

    def qpos_to_action(self, qpos: np.ndarray) -> OrderedDict[str, float]:
        command_values = self.qpos_to_command_values(qpos)
        return OrderedDict(
            (f"gripper.{link_name}", float(command_values[self.command_index_by_link_name[link_name]]))
            for link_name in self.command_link_names
        )

    def retarget_to_action(
        self, action: dict[str, float], *, seed_qpos: np.ndarray | None = None
    ) -> OrderedDict[str, float]:
        return self.qpos_to_action(self.retarget(action, seed_qpos=seed_qpos))

    def _extract_landmark_positions(self, action: dict[str, float]) -> dict[int, np.ndarray]:
        positions: dict[int, np.ndarray] = {}
        for landmark in LEAP_DEXPILOT_LANDMARK_ORDER:
            prefix = f"{landmark}.position" if landmark == "wrist" else f"{landmark}.position"
            coordinates = []
            for axis in "xyz":
                key = f"{prefix}.{axis}"
                if key not in action:
                    raise KeyError(f"Missing required DexPilot action key {key!r}.")
                coordinates.append(float(action[key]))
            positions[LEAP_DEXPILOT_HUMAN_INDEX_BY_LANDMARK[landmark]] = np.asarray(
                coordinates, dtype=np.float32
            )
        return positions

    def _resolve_command_links(self) -> dict[str, str]:
        root = ET.fromstring(Path(self.urdf_path).read_text())
        joint_to_child_link = {
            joint.get("name"): joint.find("child").get("link")
            for joint in root.findall("joint")
            if joint.get("type") != "fixed" and joint.find("child") is not None
        }

        retarget_joint_name_to_command_link_name: dict[str, str] = {}
        for joint_name in self.retargeting.joint_names:
            if joint_name not in joint_to_child_link:
                raise RuntimeError(f"DexPilot joint {joint_name!r} was not found in {self.urdf_path}.")
            child_link_name = joint_to_child_link[joint_name]
            if child_link_name not in self.command_index_by_link_name:
                raise RuntimeError(
                    f"URDF child link {child_link_name!r} for joint {joint_name!r} "
                    "is not part of the LEAP command map."
                )
            retarget_joint_name_to_command_link_name[joint_name] = child_link_name
        return retarget_joint_name_to_command_link_name
