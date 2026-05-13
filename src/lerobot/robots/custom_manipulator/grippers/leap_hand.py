# pyright: reportMissingImports=false

from __future__ import annotations

import threading
import time

import numpy as np

from lerobot.robots.custom_manipulator.grippers.config_leap_hand import LeapHandConfig, TIPS
from lerobot.robots.custom_manipulator.grippers.dynamixel_client import (
    ADDR_CURRENT_LIMIT,
    ADDR_OPERATING_MODE,
    ADDR_POSITION_D_GAIN,
    ADDR_POSITION_I_GAIN,
    ADDR_POSITION_P_GAIN,
    DynamixelClient,
)
from lerobot.robots.custom_manipulator.grippers.leap_hand_dexpilot import LeapHandDexPilotRetargeter
from lerobot.robots.custom_manipulator.grippers.leap_hand_utils import (
    LEAPhand_to_LEAPsim,
    LEAPsim_to_LEAPhand,
    allegro_to_LEAPhand,
    angle_safety_clip,
)
from lerobot.robots.custom_manipulator.grippers.leap_hand_visualizer import (
    LeapHandDebugTools,
    transform_leap_target_positions,
)
from lerobot.robots.custom_manipulator.grippers.leap_hand_visualizer import LeapHandDebugTools

LEAP_BASE_ROTATION = np.array([[0.0, -1.0, 0.0], [0.0, 0.0, 1.0], [-1.0, 0.0, 0.0]], dtype=float)


class LeapHand:
    end_effector_transforms = {
        "panda": np.eye(4),
        "dummy": np.eye(4),
    }

    def __init__(self, config: LeapHandConfig | None = None):
        from dex_retargeting.retargeting_config import RetargetingConfig

        self.config = config or LeapHandConfig()
        self.dxl_client = None

        self.retargeter = LeapHandDexPilotRetargeter(
            urdf_path=self.config.urdf_path,
            wrist_link_name=self.config.dexpilot_wrist_link_name,
            finger_tip_link_names=tuple(self.config.tip_point_link_names[tip] for tip in TIPS),
            command_index_by_link_name=self.config.command_index_by_link_name,
            disabled_link_names=self.config.disabled_joints,
        )

        self.qpos = self._home_qpos()
        self.command_lock = threading.Lock()
        self.command_thread = None
        self.command_stop = threading.Event()
        self.command_rate_hz = float(self.config.command_rate_hz)
        self.interp_duration_s = float(self.config.command_interp_duration_s)
        self.last_sent_qpos = self.qpos.copy()
        self.interp_start_qpos = self.qpos.copy()
        self.target_qpos = self.qpos.copy()
        self.interp_start_time = time.perf_counter()
        self.base_rotation = LEAP_BASE_ROTATION.tolist()

        palm_to_root_offset = self.retargeter.palm_to_root_offset(
            self.qpos,
            palm_link_name=self.config.palm_link_name,
            root_link_name=self.config.root_link_name,
        )
        self.debug = LeapHandDebugTools(
            urdf_path=self.config.urdf_path,
            enable_rerun_visualization=self.config.visualize,
            palm_link_name=self.config.palm_link_name,
            root_link_name=self.config.root_link_name,
            palm_to_root_offset=palm_to_root_offset.tolist(),
            base_rotation=self.base_rotation,
        )

    def get_end_effector_transform(self, arm_type: str) -> np.ndarray:
        return self.end_effector_transforms[arm_type].copy()

    def connect(self):
        if not self.config.control:
            print("[leap_hand] Control disabled; skipping hardware connection.", flush=True)
            return

        self.dxl_client = DynamixelClient(
            list(self.config.motor_ids), self.config.port, self.config.baudrate
        )
        self.dxl_client.connect()
        self._configure_controller()
        self._start_command_thread()

    def reset(self):
        self.qpos[:] = self._home_qpos()
        if self.dxl_client is not None:
            self._set_target_qpos(self.qpos, immediate=True)

    def disconnect(self):
        self._stop_command_thread()
        if self.dxl_client is not None:
            self.dxl_client.disconnect()
        self.dxl_client = None
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
        if self.dxl_client is not None:
            self.qpos[:] = self._read_qpos_from_hardware()
        return self._tip_positions_to_values(self._fingertip_positions(self.qpos))

    def apply_commands(self, action: dict | None = None, **kwargs):
        del kwargs
        if not action:
            return

        if not float(action.get("hand_tracking_valid", 0.0)):
            return

        transformed_targets = transform_leap_target_positions(
            self._action_to_targets(action),
            base_rotation=self.base_rotation,
        )
        self.debug.log_targets(transformed_targets, already_transformed=True)

        transformed_action = dict(action)
        for name, pos in transformed_targets.items():
            for axis, value in zip("xyz", pos, strict=True):
                transformed_action[f"{name}.position.{axis}"] = float(value)

        self.qpos[:] = self.retargeter.retarget(transformed_action)
        if self.dxl_client is not None:
            self._set_target_qpos(self.qpos)

        tip_positions = self._fingertip_positions(self.qpos)
        joints = {link: float(self.qpos[i]) for link, i in self.config.command_index_by_link_name.items()}
        self.debug.log_state(joints=joints, tip_positions=tip_positions)
        return self._tip_positions_to_values(tip_positions)

    def _configure_controller(self) -> None:
        if self.dxl_client is None:
            raise RuntimeError("LEAP hand is not connected.")

        motor_ids = list(self.config.motor_ids)
        side_to_side_motor_ids = list(self.config.side_to_side_motor_ids)

        self.dxl_client.sync_write_constant(motor_ids, self.config.control_mode, ADDR_OPERATING_MODE, 1)
        remaining_ids = self.dxl_client.set_torque_enabled(motor_ids, True)
        if remaining_ids:
            raise RuntimeError(
                "LEAP hand did not respond to torque enable for motor IDs "
                f"{remaining_ids}. Common causes: wrong `baudrate`, wrong `port`, "
                "insufficient power, or wrong Dynamixel protocol/wiring."
            )
        self.dxl_client.sync_write_constant(motor_ids, self.config.kp, ADDR_POSITION_P_GAIN, 2)
        self.dxl_client.sync_write_constant(
            side_to_side_motor_ids,
            self.config.kp * 0.75,
            ADDR_POSITION_P_GAIN,
            2,
        )
        self.dxl_client.sync_write_constant(motor_ids, self.config.ki, ADDR_POSITION_I_GAIN, 2)
        self.dxl_client.sync_write_constant(motor_ids, self.config.kd, ADDR_POSITION_D_GAIN, 2)
        self.dxl_client.sync_write_constant(
            side_to_side_motor_ids,
            self.config.kd * 0.75,
            ADDR_POSITION_D_GAIN,
            2,
        )
        self.dxl_client.sync_write_constant(motor_ids, self.config.curr_lim, ADDR_CURRENT_LIMIT, 2)
        self.dxl_client.write_desired_pos(motor_ids, self._home_device_joints())

    def _read_qpos_from_hardware(self) -> np.ndarray:
        if self.dxl_client is None:
            raise RuntimeError("LEAP hand is not connected.")

        device_qpos = np.asarray(self.dxl_client.read_pos(), dtype=float)
        if device_qpos.shape[0] != len(self.config.motor_ids):
            raise RuntimeError(
                "Unexpected LEAP hand observation size: "
                f"expected {len(self.config.motor_ids)}, got {device_qpos.shape[0]}."
            )
        return self._device_to_model_joint_values(device_qpos)

    def _write_qpos_to_hardware(self, qpos: np.ndarray) -> None:
        if self.dxl_client is None:
            raise RuntimeError("LEAP hand is not connected.")
        self.dxl_client.write_desired_pos(
            list(self.config.motor_ids), self._model_to_device_joint_values(qpos)
        )

    def _set_target_qpos(self, qpos: np.ndarray, immediate: bool = False) -> None:
        with self.command_lock:
            if immediate:
                self.last_sent_qpos[:] = qpos
                self.interp_start_qpos[:] = qpos
                self.target_qpos[:] = qpos
                self.interp_start_time = time.perf_counter()
                self._write_qpos_to_hardware(qpos)
                return

            self.interp_start_qpos[:] = self.last_sent_qpos
            self.target_qpos[:] = qpos
            self.interp_start_time = time.perf_counter()

    def _start_command_thread(self) -> None:
        if self.command_thread is not None and self.command_thread.is_alive():
            return
        self.command_stop.clear()
        self.command_thread = threading.Thread(
            target=self._command_loop, name="leap-hand-command", daemon=True
        )
        self.command_thread.start()

    def _stop_command_thread(self) -> None:
        self.command_stop.set()
        if self.command_thread is not None:
            self.command_thread.join(timeout=1.0)
        self.command_thread = None

    def _command_loop(self) -> None:
        period_s = 1.0 / self.command_rate_hz
        while not self.command_stop.is_set():
            start_time = time.perf_counter()
            with self.command_lock:
                elapsed = time.perf_counter() - self.interp_start_time
                alpha = 1.0 if self.interp_duration_s <= 0.0 else min(1.0, elapsed / self.interp_duration_s)
                qpos = (1.0 - alpha) * self.interp_start_qpos + alpha * self.target_qpos
                self.last_sent_qpos[:] = qpos
            self._write_qpos_to_hardware(qpos)
            elapsed = time.perf_counter() - start_time
            time.sleep(period_s - elapsed if elapsed < period_s else 0.0)

    def _home_qpos(self) -> np.ndarray:
        if self.config.home_position is not None:
            home_qpos = np.asarray(self.config.home_position, dtype=float).copy()
            if home_qpos.shape != (len(self.config.command_index_by_link_name),):
                raise ValueError(
                    "LEAP hand home_position length must match command_index_by_link_name length: "
                    f"expected {len(self.config.command_index_by_link_name)}, got {home_qpos.shape[0]}."
                )
            return home_qpos
        return np.zeros(len(self.config.command_index_by_link_name), dtype=float)

    def _home_device_joints(self) -> np.ndarray:
        if self.config.home_position is not None:
            return self._model_to_device_joint_values(self.config.home_position)
        return np.asarray(
            allegro_to_LEAPhand(np.zeros(len(self.config.motor_ids), dtype=float)),
            dtype=float,
        )

    def _model_to_device_joint_values(self, model_joints: list[float] | np.ndarray) -> np.ndarray:
        return np.asarray(
            angle_safety_clip(LEAPsim_to_LEAPhand(model_joints)),
            dtype=float,
        )

    def _device_to_model_joint_values(self, device_joints: list[float] | np.ndarray) -> np.ndarray:
        return np.asarray(LEAPhand_to_LEAPsim(device_joints), dtype=float)

    def _action_to_targets(self, action: dict[str, float]) -> dict[str, list[float]]:
        def xyz(name: str) -> list[float]:
            return [float(action[f"{name}.position.{axis}"]) for axis in "xyz"]

        return {
            "wrist": xyz("wrist"),
            **{tip: xyz(tip) for tip in TIPS},
        }

    def _fingertip_positions(self, qpos: np.ndarray) -> dict[str, list[float]]:
        return self.retargeter.fingertip_positions_in_palm(
            qpos,
            palm_link_name=self.config.palm_link_name,
            tip_link_names=self.config.tip_point_link_names,
        )

    def _tip_positions_to_values(self, tip_positions: dict[str, list[float]]) -> dict[str, float]:
        return {
            f"{tip}.position.{axis}": float(value)
            for tip, pos in tip_positions.items()
            for axis, value in zip(AXES, pos, strict=True)
        }
