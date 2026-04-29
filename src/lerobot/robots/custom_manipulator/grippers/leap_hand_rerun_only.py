#!/usr/bin/env python

import time
from dataclasses import dataclass, field

import numpy as np

from lerobot.configs import parser
from lerobot.teleoperators.metareader import MetaReaderConfig, MetaReaderTeleoperator

from .config_leap_hand import TIPS, LeapHandConfig
from .leap_hand import PALM_TO_TARGET_ROT, _require_klampt, _resolve_urdf_path
from .leap_hand_debug import LeapHandDebugTools


@dataclass
class LeapHandRerunOnlyConfig:
    gripper: LeapHandConfig = field(default_factory=LeapHandConfig)
    teleop: MetaReaderConfig = field(default_factory=MetaReaderConfig)
    fps: float = 60.0
    duration_s: float = 0.0
    entity_path: str = "leap_hand_sim"


class LeapHandRerunOnly:
    def __init__(self, config: LeapHandConfig, entity_path: str = "leap_hand_sim"):
        self.config = config
        self.urdf_path = _resolve_urdf_path(self.config.urdf_path)

        IKObjective, IKSolver, WorldModel, so3, vectorops = _require_klampt()
        self._IKObjective = IKObjective
        self._so3 = so3
        self._vectorops = vectorops
        self._palm_center_offset = np.asarray(self.config.palm_center_offset, dtype=float)

        world = WorldModel()
        if not world.loadRobot(self.urdf_path):
            raise RuntimeError(f"Failed to load LEAP hand URDF: {self.urdf_path}")
        self.model = world.robot(0)
        self.world = world

        self.joints = {self.model.driver(i).getName(): self.model.driver(i) for i in range(self.model.numDrivers())}
        self.links = [joint.getAffectedLink() for joint in self.joints.values()]
        self._command_index_by_driver_name = self._resolve_command_index_by_driver_name()

        self.palm_frame = self._resolve_link(self.config.palm_link_name, fallback="palm_lower")
        self.tips = {
            tip: self._resolve_link(self.config.tip_link_names[tip]) for tip in self.config.tip_link_names
        }

        self.solver = IKSolver(self.model)
        self.solver.setActiveDofs(self.links)
        self.solver.setMaxIters(self.config.niter)
        self.solver.setTolerance(1e-3)

        self._debug = LeapHandDebugTools(
            urdf_path=self.urdf_path,
            tip_names=TIPS,
            tip_scale_factors=self.config.tip_scale_factors,
            enable_tip_scale_tuner=self.config.enable_tip_scale_tuner,
            enable_rerun_visualization=True,
            palm_frame=self.palm_frame,
            root_frame=self.palm_frame,
            palm_center_offset=self._palm_center_offset,
            tips=self.tips,
            palm_to_target_rot=PALM_TO_TARGET_ROT,
            entity_path=entity_path,
        )

        self.log_state()

    def close(self):
        self._debug.close()

    def apply_action(self, action: dict[str, float] | None):
        if not action:
            return

        self._debug.poll()

        if self.config.use_delta_actions:
            fingertips = self._get_fingertips_from_current_model_state()
            action = action | {key: action[key] + fingertips[key] for key in fingertips if key in action}

        target_offsets = {
            tip: (
                PALM_TO_TARGET_ROT
                @ (
                    np.array([float(action.get(f"{tip}.position.{axis}", 0.0)) for axis in "xyz"], dtype=float)
                    * self.config.tip_scale_factors[tip]
                )
            )
            for tip in self.tips
        }
        targets = {tip: (self._palm_center_offset + target_offsets[tip]).tolist() for tip in self.tips}

        self.solver.clear()
        palm_index = self.palm_frame.getIndex()
        for tip in self.tips:
            objective = self._IKObjective()
            objective.setRelativePoint(self.tips[tip].getIndex(), palm_index, [0, 0, 0], targets[tip])
            self.solver.add(objective)
        self.solver.solve()

        self._debug.log_targets({tip: target_offsets[tip].tolist() for tip in target_offsets})
        self.log_state()

    def log_state(self):
        self._debug.log_state(
            self._link_name_to_model_joint_values(self._current_model_joint_values()),
            self._get_fingertips_from_current_model_state(),
        )
        self._debug.poll()

    def _resolve_command_index_by_driver_name(self) -> dict[str, int]:
        command_index_by_driver_name = {}
        for driver_name, driver in self.joints.items():
            affected_link = self.model.link(driver.getAffectedLink()).getName()
            if affected_link in self.config.command_index_by_link_name:
                command_index_by_driver_name[driver_name] = self.config.command_index_by_link_name[affected_link]

        if len(command_index_by_driver_name) == len(self.config.command_index_by_link_name):
            return command_index_by_driver_name

        for i in self.config.motor_ids:
            name = str(i)
            if name in self.joints:
                command_index_by_driver_name[name] = i

        if len(command_index_by_driver_name) != len(self.config.motor_ids):
            raise RuntimeError(
                "Failed to resolve LEAP hand driver ordering from the URDF model. "
                f"Resolved {len(command_index_by_driver_name)} / {len(self.config.motor_ids)} motors."
            )
        return command_index_by_driver_name

    def _resolve_link(self, link_name: str, fallback: str | None = None):
        link = self.model.link(link_name)
        if link.getIndex() >= 0:
            return link

        if fallback is not None:
            fallback_link = self.model.link(fallback)
            if fallback_link.getIndex() >= 0:
                print(
                    f"[leap_hand_rerun_only] Link {link_name!r} not found, using {fallback!r} instead.",
                    flush=True,
                )
                return fallback_link

        raise RuntimeError(f"Link {link_name!r} was not found in {self.urdf_path}.")

    def _current_model_joint_values(self) -> np.ndarray:
        model_joints = np.zeros(len(self.config.motor_ids), dtype=float)
        for name, idx in self._command_index_by_driver_name.items():
            model_joints[idx] = float(self.joints[name].getValue())
        return model_joints

    def _link_name_to_model_joint_values(self, model_joints: list[float] | np.ndarray) -> dict[str, float]:
        return {
            link_name: float(model_joints[idx])
            for link_name, idx in self.config.command_index_by_link_name.items()
        }

    def _get_fingertips_from_current_model_state(self) -> dict[str, float]:
        palm_r, palm_t = self.palm_frame.getTransform()
        palm_r_inv = self._so3.inv(palm_r)

        tip_positions = {
            tip: PALM_TO_TARGET_ROT.T
            @ np.array(
                self._so3.apply(
                    palm_r_inv, self._vectorops.sub(link.getTransform()[1], palm_t)
                )
                - self._palm_center_offset
            )
            / self.config.tip_scale_factors[tip]
            for tip, link in self.tips.items()
        }

        return {
            f"{tip}.position.{axis}": float(value)
            for tip, tip_position in tip_positions.items()
            for axis, value in zip("xyz", tip_position)
        }


@parser.wrap()
def main(cfg: LeapHandRerunOnlyConfig):
    simulator = LeapHandRerunOnly(cfg.gripper, entity_path=cfg.entity_path)
    teleop = MetaReaderTeleoperator(cfg.teleop)
    loop_dt = 0.0 if cfg.fps <= 0 else 1.0 / cfg.fps
    deadline = None if cfg.duration_s <= 0 else time.monotonic() + cfg.duration_s

    print("[leap_hand_rerun_only] Connecting MetaReader...", flush=True)
    teleop.connect()
    print("[leap_hand_rerun_only] Streaming simulated LEAP hand to Rerun.", flush=True)

    try:
        while deadline is None or time.monotonic() < deadline:
            start = time.monotonic()
            simulator.apply_action(teleop.get_action())
            if loop_dt > 0:
                time.sleep(max(0.0, loop_dt - (time.monotonic() - start)))
    except KeyboardInterrupt:
        print("[leap_hand_rerun_only] Stopped by user.", flush=True)
    finally:
        teleop.disconnect()
        simulator.close()


if __name__ == "__main__":
    main()
