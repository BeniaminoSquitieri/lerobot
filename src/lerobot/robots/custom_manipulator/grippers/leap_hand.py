# pyright: reportMissingImports=false

from __future__ import annotations

from collections.abc import Mapping, Sequence
import time

import numpy as np

from lerobot.robots.custom_manipulator.grippers.config_leap_hand import (
    COMMAND_LINK_NAMES,
    LeapHandConfig,
    TIPS,
)
from lerobot.robots.custom_manipulator.grippers.dynamixel_client import DynamixelClient
from lerobot.robots.custom_manipulator.grippers.leap_hand_utils import (
    LEAPhand_to_LEAPsim,
    LEAPsim_to_LEAPhand,
    allegro_to_LEAPhand,
    angle_safety_clip,
)
from lerobot.robots.custom_manipulator.grippers.leap_hand_visualizer import LeapHandDebugTools

AXES = "xyz"
TARGET_NAMES = ("wrist", *TIPS)

ADDR_OPERATING_MODE = 11
ADDR_CURRENT_LIMIT = 38
ADDR_POSITION_D_GAIN = 80
ADDR_POSITION_I_GAIN = 82
ADDR_POSITION_P_GAIN = 84

QUEST_PALM_FROM_LEAP_PALM = np.array([
    [0.0, -1.0, 0.0],
    [0.0, 0.0, 1.0],
    [-1.0, 0.0, 0.0],
])

DEX_FRAME_FROM_LEAP_PALM = np.array([
    [0.0, -1.0, 0.0],
    [-1.0, 0.0, 0.0],
    [0.0, 0.0, -1.0],
])


class LeapHand:
    end_effector_transforms = {
        "panda": np.eye(4),
        "dummy": np.eye(4),
    }

    def __init__(self, config: LeapHandConfig | None = None):
        from dex_retargeting.retargeting_config import RetargetingConfig

        self.config = config or LeapHandConfig()
        self.motors = None
        self.command_index_by_link_name = dict(self.config.command_index_by_link_name)

        disabled_indices = {
            self.command_index_by_link_name[name]
            for name in self.config.disabled_joints
        }
        self.active_joint_indices = tuple(
            i
            for i in range(len(self.command_index_by_link_name))
            if i not in disabled_indices
        )

        tip_link_names = [
            self.config.tip_point_link_names[tip]
            for tip in TIPS
        ]

        self.retargeting = RetargetingConfig.from_dict(
            {
                "type": "dexpilot",
                "urdf_path": self.config.urdf_path,
                "wrist_link_name": self.config.dexpilot_wrist_link_name,
                "finger_tip_link_names": tip_link_names,
                "scaling_factor": 1.6,
                "low_pass_alpha": 0.2,
                "has_joint_limits": True,
                "project_dist": 0.03,
                "escape_dist": 0.05,
                "target_joint_names": [str(i) for i in self.active_joint_indices],
            }
        ).build()

        self.robot = self.retargeting.optimizer.robot
        self.origin_indices, self.task_indices = (
            self.retargeting.optimizer.generate_link_indices(len(tip_link_names))
        )

        self.home_qpos = (
            np.asarray(self.config.home_position, dtype=float).copy()
            if self.config.home_position is not None
            else np.zeros(len(self.command_index_by_link_name))
        )
        self.target_qpos = self.home_qpos.copy()

        self.debug = LeapHandDebugTools(
            urdf_path=self.config.urdf_path,
            enable_rerun_visualization=self.config.visualize,
            palm_link_name=self.config.palm_link_name,
            root_link_name=self.config.root_link_name,
            command_index_by_link_name=self.command_index_by_link_name,
            quest_palm_from_leap_palm=QUEST_PALM_FROM_LEAP_PALM,
        )

    def connect(self):
        if not self.config.control:
            print("[leap_hand] Control disabled; skipping hardware connection.", flush=True)
            return

        motor_ids = list(self.config.motor_ids)
        side_to_side_motor_ids = list(self.config.side_to_side_motor_ids)

        self.motors = DynamixelClient(motor_ids, self.config.port, self.config.baudrate)
        self.motors.connect()

        self.motors.sync_write(motor_ids, [self.config.control_mode] * len(motor_ids), ADDR_OPERATING_MODE, 1)
        self.motors.set_torque_enabled(motor_ids, True)

        self.motors.sync_write(motor_ids, [self.config.kp] * len(motor_ids), ADDR_POSITION_P_GAIN, 2)
        self.motors.sync_write(side_to_side_motor_ids, [self.config.kp * 0.75] * len(side_to_side_motor_ids), ADDR_POSITION_P_GAIN, 2)

        self.motors.sync_write(motor_ids, [self.config.ki] * len(motor_ids), ADDR_POSITION_I_GAIN, 2)

        self.motors.sync_write(motor_ids, [self.config.kd] * len(motor_ids), ADDR_POSITION_D_GAIN, 2)
        self.motors.sync_write(side_to_side_motor_ids, [self.config.kd * 0.75] * len(side_to_side_motor_ids), ADDR_POSITION_D_GAIN, 2)

        self.motors.sync_write(motor_ids, [self.config.curr_lim] * len(motor_ids), ADDR_CURRENT_LIMIT, 2)

        home_device_qpos = (
            allegro_to_LEAPhand(np.zeros(len(motor_ids)))
            if self.config.home_position is None
            else angle_safety_clip(LEAPsim_to_LEAPhand(self.home_qpos))
        )

        self.motors.write_desired_pos(motor_ids, np.asarray(home_device_qpos, dtype=float))

    def reset(self):
        self.target_qpos = self.home_qpos.copy()

        if self.motors is not None:
            self.motors.write_desired_pos(
                list(self.config.motor_ids),
                np.asarray(angle_safety_clip(LEAPsim_to_LEAPhand(self.target_qpos)), dtype=float),
            )

        self.retargeting.reset()

    def disconnect(self):
        if self.motors is not None:
            self.motors.disconnect()
            self.motors = None

        self.debug.close()

    close = disconnect

    def get_end_effector_transform(self, arm_type: str) -> np.ndarray:
        return self.end_effector_transforms[arm_type].copy()

    @property
    def action_features(self) -> dict:
        return {
            f"action.{name}.position.{axis}": float
            for name in TARGET_NAMES
            for axis in AXES
        }

    @property
    def features(self) -> dict:
        return {
            f"{tip}.position.{axis}": float
            for tip in TIPS
            for axis in AXES
        }

    def get_sensors(self) -> dict[str, float]:
        qpos = (
            np.asarray(LEAPhand_to_LEAPsim(self.motors.read_pos()), dtype=float)
            if self.motors is not None
            else self.target_qpos
        )

        tip_positions = self.forward_kinematics(qpos, self.config.tip_point_link_names)

        return {
            f"{tip}.position.{axis}": float(value)
            for tip, pos in tip_positions.items()
            for axis, value in zip(AXES, pos, strict=True)
        }

    def apply_commands(self, action: dict | None = None):
        if action["is_engaged"]:
            return

        points = np.array( [[action[f"{name}.position.{axis}"] for axis in AXES] for name in TARGET_NAMES], dtype=float, ) 
        # points -= points[0] # Make wrist the origin 
        points = points @ DEX_FRAME_FROM_LEAP_PALM.T # Rotate from LEAP palm frame to DEX frame
        
        # retargeting
        ref_value = points[self.task_indices] - points[self.origin_indices]
        fixed_qpos = np.zeros(len(self.retargeting.optimizer.idx_pin2fixed))

        robot_qpos = self.retargeting.retarget(ref_value, fixed_qpos=fixed_qpos)
        active_qpos = robot_qpos[self.retargeting.optimizer.idx_pin2target]

        qpos = np.zeros(len(self.command_index_by_link_name))
        for index, value in zip(self.active_joint_indices, active_qpos, strict=True):
            qpos[index] = value

        self.target_qpos = qpos.copy()

        # TODO move log_state to get_sensors when we start using the real hand
        tip_positions = self.forward_kinematics(qpos, self.config.tip_point_link_names)

        self.debug.log_targets(points, names=TARGET_NAMES, already_transformed=True)
        self.debug.log_state(qpos=qpos, tip_positions=tip_positions)

        if self.motors is not None:
            self.motors.write_desired_pos(
                list(self.config.motor_ids),
                np.asarray(angle_safety_clip(LEAPsim_to_LEAPhand(qpos)), dtype=float),
            )


    def forward_kinematics(
        self,
        qpos: np.ndarray,
        link_names: Mapping[str, str] | Sequence[str],
    ) -> dict[str, list[float]]:
        robot_qpos = np.zeros(int(self.robot.dof))
        robot_qpos[self.retargeting.optimizer.idx_pin2target] = qpos[list(self.active_joint_indices)]

        adaptor = self.retargeting.optimizer.adaptor
        if adaptor is not None:
            robot_qpos[:] = adaptor.forward_qpos(robot_qpos)[:]

        self.robot.compute_forward_kinematics(robot_qpos)

        palm_pose = self.robot.get_link_pose(self.robot.get_link_index(self.config.palm_link_name))
        palm_pose_inv = np.linalg.inv(palm_pose)

        items = (
            link_names.items()
            if isinstance(link_names, Mapping)
            else ((name, name) for name in link_names)
        )

        positions = {}
        for name, link_name in items:
            link_pose = self.robot.get_link_pose(self.robot.get_link_index(link_name))
            position = palm_pose_inv @ np.append(link_pose[:3, 3], 1.0)
            positions[str(name)] = [float(x) for x in position[:3]]

        return positions


if __name__ == "__main__":
    from lerobot.teleoperators.metareader.config_metareader import MetaReaderConfig
    from lerobot.teleoperators.metareader.metareader import MetaReaderTeleoperator

    teleop = MetaReaderTeleoperator(MetaReaderConfig())
    teleop.connect()

    hand = LeapHand(LeapHandConfig(visualize=True, control=False))
    hand.connect()
    hand.reset()

    while True:
        action = teleop.get_action()
        hand.apply_commands(action)
        time.sleep(0.1)