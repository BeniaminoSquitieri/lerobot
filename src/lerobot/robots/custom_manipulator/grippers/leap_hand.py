# pyright: reportMissingImports=false

from __future__ import annotations

import numpy as np

from lerobot.robots.custom_manipulator.grippers.config_leap_hand import LeapHandConfig, TIPS
from lerobot.robots.custom_manipulator.grippers.leap_hand_dexpilot import (
    LeapHandDexPilotRetargeter,
)
from lerobot.robots.custom_manipulator.grippers.leap_hand_utils import (
    LeapHandDebugTools,
    transform_leap_target_positions,
)


class LeapHand:
    end_effector_transforms = {"panda": np.eye(4, dtype=float), "dummy": np.eye(4, dtype=float)}

    def __init__(self, config: LeapHandConfig | None = None):
        self.config = config or LeapHandConfig()

        from klampt import WorldModel
        from klampt.math import so3, vectorops

        self._so3 = so3
        self._vectorops = vectorops

        urdf_path = self.config.urdf_path

        world = WorldModel()
        ok = world.loadRobot(urdf_path)
        if not ok:
            raise RuntimeError(f"Failed to load LEAP hand URDF: {urdf_path}")
        self.world = world
        self.model = world.robot(0)

        self.drivers = {self.model.driver(i).getName(): self.model.driver(i) for i in range(self.model.numDrivers())}

        self.root_frame = self.model.link(self.config.root_link_name)
        self.palm_frame = self.model.link(self.config.palm_link_name)
        self.tip_point_frames = {
            tip: self.model.link(self.config.tip_point_link_names[tip]) for tip in self.config.tip_point_link_names
        }

        rotation_y = self._so3.rotation([0.0, 1.0, 0.0], np.pi / 2.0)
        rotation_x = self._so3.rotation([1.0, 0.0, 0.0], -np.pi / 2.0)
        base_rotation = self._so3.mul(rotation_y, rotation_x)
        base_rotation_mat = self._so3.matrix(base_rotation)
        self.root_frame.setParentTransform(base_rotation, [0.0, 0.0, 0.0])
        self.model.setConfig(self.model.getConfig())

        self.retargeter = LeapHandDexPilotRetargeter(
            urdf_path=urdf_path,
            command_index_by_link_name=self.config.command_index_by_link_name,
        )

        palm_r, palm_t = self.palm_frame.getTransform()
        root_r, root_t = self.root_frame.getTransform()
        palm_to_root_offset = self._so3.apply(self._so3.inv(palm_r), self._vectorops.sub(root_t, palm_t))

        self.debug = LeapHandDebugTools(
            urdf_path=urdf_path,
            enable_rerun_visualization=self.config.visualize,
            palm_link_name=self.config.palm_link_name,
            root_link_name=self.config.root_link_name,
            palm_to_root_offset=palm_to_root_offset,
            base_rotation=base_rotation_mat,
        )

        self.qpos = np.zeros(16, dtype=float)
        if self.config.home_position is not None:
            self.qpos[:] = np.asarray(self.config.home_position, dtype=float)
        self._apply_qpos_to_model(self.qpos)

    def get_end_effector_transform(self, arm_type: str) -> np.ndarray:
        return self.end_effector_transforms[arm_type].copy()

    def connect(self):
        return None

    def reset(self):
        self.qpos[:] = 0.0
        if self.config.home_position is not None:
            self.qpos[:] = np.asarray(self.config.home_position, dtype=float)
        self._apply_qpos_to_model(self.qpos)

    def disconnect(self):
        self.debug.close()

    close = disconnect

    @property
    def action_features(self) -> dict:
        tip_features = {f"action.{tip}.position.{axis}": float for tip in TIPS for axis in "xyz"}
        wrist_features = {f"action.wrist.position.{axis}": float for axis in "xyz"}
        return {"action.hand_tracking_valid": float, **wrist_features, **tip_features}

    @property
    def features(self) -> dict:
        return {f"{tip}.position.{axis}": float for tip in TIPS for axis in "xyz"}

    def get_sensors(self) -> dict[str, float]:
        return dict(self._get_fingertips_from_current_model_state())

    def apply_commands(self, action: dict | None = None, **kwargs):
        del kwargs
        if not action:
            return

        if not float(action.get("hand_tracking_valid", 0.0)):
            return

        transformed_targets = transform_leap_target_positions(
            self._action_to_targets(action),
            base_rotation=self.debug._base_rotation,
        )
        self.debug.log_targets(transformed_targets, already_transformed=True)

        self.qpos[:] = self.retargeter.retarget(self._action_with_targets(action, transformed_targets))
        self._apply_qpos_to_model(self.qpos)

        tip_values, tip_positions = self._get_fingertips_from_current_model_state(return_positions=True)
        joints = {
            link_name: float(self.drivers[link_name].getValue())
            for link_name in self.config.command_index_by_link_name
            if link_name in self.drivers
        }
        self.debug.log_state(joints=joints, tip_positions=tip_positions)
        return tip_values

    def _apply_qpos_to_model(self, qpos: np.ndarray) -> None:
        for link_name, idx in self.config.command_index_by_link_name.items():
            if link_name in self.drivers:
                self.drivers[link_name].setValue(float(qpos[idx]))
        self.model.setConfig(self.model.getConfig())

    def _action_to_targets(self, action: dict[str, float]) -> dict[str, list[float]]:
        targets = {
            "wrist": [float(action[f"wrist.position.{a}"]) for a in "xyz"],
        }
        for tip in ("thumb", "index", "middle", "ring"):
            if all(f"{tip}.position.{a}" in action for a in "xyz"):
                targets[tip] = [float(action[f"{tip}.position.{a}"]) for a in "xyz"]
        return targets

    def _action_with_targets(
        self,
        action: dict[str, float],
        target_positions: dict[str, list[float]],
    ) -> dict[str, float]:
        transformed_action = dict(action)
        for tip_name, pos in target_positions.items():
            for axis, value in zip("xyz", pos, strict=True):
                transformed_action[f"{tip_name}.position.{axis}"] = float(value)
        return transformed_action

    def _get_fingertips_from_current_model_state(self, return_positions: bool = False):
        palm_r, palm_t = self.palm_frame.getTransform()
        palm_r_inv = self._so3.inv(palm_r)

        tip_positions = {}
        for tip, link in self.tip_point_frames.items():
            _, tip_t = link.getTransform()
            rel = self._so3.apply(palm_r_inv, self._vectorops.sub(tip_t, palm_t))
            tip_positions[tip] = [float(v) for v in rel]

        tip_values = {
            f"{tip}.position.{axis}": float(value)
            for tip, pos in tip_positions.items()
            for axis, value in zip("xyz", pos, strict=True)
        }

        if return_positions:
            return tip_values, tip_positions
        return tip_values


if __name__ == "__main__":
    import time

    from lerobot.teleoperators.metareader.config_metareader import MetaReaderConfig
    from lerobot.teleoperators.metareader.metareader import MetaReaderTeleoperator

    teleop = MetaReaderTeleoperator(MetaReaderConfig())
    teleop.connect()

    hand = LeapHand(LeapHandConfig(visualize=True))

    while True:
        action = teleop.get_action()
        hand.apply_commands(action)
        time.sleep(0.01)
