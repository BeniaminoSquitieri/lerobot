from __future__ import annotations

import numpy as np

from lerobot.robots.custom_manipulator.grippers.config_leap_hand import (
    COMMAND_LINK_NAMES,
    DEFAULT_COMMAND_INDEX_BY_LINK_NAME,
)

LEAP_DEXPILOT_WRIST_LINK_NAME = "base"
LEAP_DEXPILOT_FINGER_TIP_LINK_NAMES = (
    "thumb_tip_head",
    "index_tip_head",
    "middle_tip_head",
    "ring_tip_head",
)


class LeapHandDexPilotRetargeter:
    def __init__(
        self,
        urdf_path: str,
        *,
        wrist_link_name: str = LEAP_DEXPILOT_WRIST_LINK_NAME,
        finger_tip_link_names: tuple[str, ...] = LEAP_DEXPILOT_FINGER_TIP_LINK_NAMES,
        command_index_by_link_name: dict[str, int] | None = None,
        scaling_factor: float = 1.6,
        low_pass_alpha: float = 0.2,
        has_joint_limits: bool = True,
        project_dist: float = 0.03,
        escape_dist: float = 0.05,
        disabled_link_names: tuple[str, ...] = (),
    ):
        self.urdf_path = urdf_path
        self.wrist_link_name = wrist_link_name
        self.finger_tip_link_names = tuple(finger_tip_link_names)
        self.command_index_by_link_name = dict(command_index_by_link_name or DEFAULT_COMMAND_INDEX_BY_LINK_NAME)
        self.disabled_link_names = tuple(disabled_link_names)
        unknown_disabled = tuple(
            link_name for link_name in self.disabled_link_names if link_name not in self.command_index_by_link_name
        )
        if unknown_disabled:
            raise ValueError(
                f"Unknown LeapHand disabled joints: {unknown_disabled}. "
                f"Available joints: {tuple(self.command_index_by_link_name)}"
            )
        self.disabled_joint_indices = tuple(
            sorted(
                self.command_index_by_link_name[link_name]
                for link_name in self.disabled_link_names
            )
        )
        self.active_joint_indices = tuple(
            idx
            for idx in range(len(self.command_index_by_link_name))
            if idx not in self.disabled_joint_indices
        )

        from dex_retargeting.retargeting_config import RetargetingConfig

        cfg = RetargetingConfig.from_dict(
            {
                "type": "dexpilot",
                "urdf_path": urdf_path,
                "wrist_link_name": wrist_link_name,
                "finger_tip_link_names": list(self.finger_tip_link_names),
                "scaling_factor": scaling_factor,
                "low_pass_alpha": low_pass_alpha,
                "has_joint_limits": has_joint_limits,
                "project_dist": project_dist,
                "escape_dist": escape_dist,
                "target_joint_names": [str(i) for i in self.active_joint_indices],
            }
        )
        self.retargeting = cfg.build()
        self.joint_names = tuple(str(i) for i in self.active_joint_indices)

    def reset(self) -> None:
        self.retargeting.reset()

    def retarget(self, action: dict[str, float]) -> np.ndarray:
        wrist = np.array([action[f"wrist.position.{a}"] for a in "xyz"], dtype=float)
        tips = {
            tip: np.array([action[f"{tip}.position.{a}"] for a in "xyz"], dtype=float)
            for tip in ("thumb", "index", "middle", "ring")
        }

        points = np.stack([wrist, tips["thumb"], tips["index"], tips["middle"], tips["ring"]], axis=0)

        origin = np.array([2, 3, 4, 3, 4, 4, 0, 0, 0, 0], dtype=int)
        task = np.array([1, 1, 1, 2, 2, 3, 1, 2, 3, 4], dtype=int)
        ref_value = points[task] - points[origin]

        fixed_qpos = np.zeros(len(self.retargeting.optimizer.idx_pin2fixed), dtype=float)
        robot_qpos = self.retargeting.retarget(ref_value, fixed_qpos=fixed_qpos)
        active_qpos = robot_qpos[self.retargeting.optimizer.idx_pin2target].astype(float, copy=False)
        qpos = np.zeros(len(self.command_index_by_link_name), dtype=float)
        for idx, value in zip(self.active_joint_indices, active_qpos, strict=True):
            qpos[idx] = float(value)
        return qpos

    def qpos_to_action(self, qpos: np.ndarray) -> dict[str, float]:
        qpos = np.asarray(qpos, dtype=float)
        return {
            f"gripper.{link_name}": float(qpos[self.command_index_by_link_name[link_name]])
            for link_name in COMMAND_LINK_NAMES
        }

    def retarget_to_action(self, action: dict[str, float]) -> dict[str, float]:
        return self.qpos_to_action(self.retarget(action))
