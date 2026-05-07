# pyright: reportMissingImports=false

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import numpy as np

from lerobot.robots.custom_manipulator.grippers.config_leap_hand import LeapHandConfig, TIPS
from lerobot.robots.custom_manipulator.grippers.leap_hand_dexpilot import (
    LeapHandDexPilotRetargeter,
)
from lerobot.robots.custom_manipulator.grippers.leap_hand_utils import (
    LeapHandDebugTools,
    transform_leap_target_positions,
)


def _get_leap_runtime():
    repo_root = Path(__file__).resolve().parents[5]
    leap_hand_root = repo_root / "leap_hand"
    if leap_hand_root.is_dir() and str(leap_hand_root) not in sys.path:
        sys.path.insert(0, str(leap_hand_root))

    try:
        import dynamixel_sdk  # noqa: F401
    except ImportError:
        _append_local_dynamixel_sdk_path(repo_root)
        try:
            import dynamixel_sdk  # noqa: F401
        except ImportError as exc:
            raise ModuleNotFoundError(
                "Missing optional dependency `dynamixel_sdk` for the LEAP hand runtime. "
                "Install it in the active environment or make sure the local LEAP/SDK site-packages path is available."
            ) from exc

    try:
        from leap_hand_utils.dynamixel_client import DynamixelClient
        import leap_hand_utils.leap_hand_utils as leap_utils
    except ImportError as exc:
        raise ModuleNotFoundError(
            "LEAP hand support requires the local `leap_hand/` folder and its runtime dependencies, "
            "including `dynamixel_sdk`."
        ) from exc

    return DynamixelClient, leap_utils


def _append_local_dynamixel_sdk_path(repo_root: Path) -> None:
    leap_api_root = repo_root.parent / "LEAP_Hand_API"
    site_packages_roots = sorted(leap_api_root.glob("env_leap/lib/python*/site-packages"))
    for site_packages in site_packages_roots:
        dynamixel_pkg = site_packages / "dynamixel_sdk"
        if dynamixel_pkg.is_dir() and str(site_packages) not in sys.path:
            sys.path.append(str(site_packages))
            return


def _resolve_urdf_path(urdf_path: str) -> str:
    source = Path(urdf_path).expanduser().resolve()
    source_text = source.read_text()
    rewritten = source_text.replace("package:///", "")
    if rewritten == source_text:
        return str(source)

    resolved = source.with_name(f"{source.stem}.resolved{source.suffix}")
    if not resolved.exists() or resolved.read_text() != rewritten:
        resolved.write_text(rewritten)
    return str(resolved)


def _expand_candidate_ports(config: LeapHandConfig) -> list[str]:
    candidate_ports: list[str] = []
    if config.port:
        candidate_ports.append(config.port)
    candidate_ports.extend(port for port in config.port_candidates if port not in candidate_ports)

    # Add any currently-present serial devices (helps when /dev/serial/by-id changes across machines).
    for port_path in sorted(Path("/dev/serial/by-id").glob("*")):
        port_str = str(port_path)
        if port_str not in candidate_ports:
            candidate_ports.append(port_str)
    for port_path in sorted(Path("/dev").glob("ttyUSB*")):
        port_str = str(port_path)
        if port_str not in candidate_ports:
            candidate_ports.append(port_str)
    for port_path in sorted(Path("/dev").glob("ttyACM*")):
        port_str = str(port_path)
        if port_str not in candidate_ports:
            candidate_ports.append(port_str)

    return candidate_ports


class LeapHand:
    end_effector_transforms = {"panda": np.eye(4, dtype=float), "dummy": np.eye(4, dtype=float)}

    def __init__(self, config: LeapHandConfig | None = None):
        self.config = config or LeapHandConfig()

        from klampt import WorldModel
        from klampt.math import so3, vectorops

        self._so3 = so3
        self._vectorops = vectorops
        _, self._leap_utils = _get_leap_runtime()
        self.dxl_client = None
        self._command_lock = threading.Lock()
        self._command_thread = None
        self._command_thread_stop = threading.Event()
        self._command_rate_hz = float(self.config.command_rate_hz)
        self._interp_duration_s = float(self.config.command_interp_duration_s)
        self._last_sent_qpos = np.zeros(16, dtype=float)
        self._interp_start_qpos = np.zeros(16, dtype=float)
        self._target_qpos = np.zeros(16, dtype=float)
        self._interp_start_time = time.perf_counter()

        urdf_path = _resolve_urdf_path(self.config.urdf_path)

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
            disabled_link_names=self.config.disabled_joints,
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
        self._last_sent_qpos[:] = self.qpos
        self._interp_start_qpos[:] = self.qpos
        self._target_qpos[:] = self.qpos
        self._apply_qpos_to_model(self.qpos)

    def get_end_effector_transform(self, arm_type: str) -> np.ndarray:
        return self.end_effector_transforms[arm_type].copy()

    def connect(self):
        DynamixelClient, _ = _get_leap_runtime()
        candidate_ports = _expand_candidate_ports(self.config)

        last_error = None
        attempted_ports: list[str] = []
        missing_ports: list[str] = []
        for port in candidate_ports:
            if not Path(port).exists():
                missing_ports.append(port)
                continue
            attempted_ports.append(port)
            try:
                print(f"[leap_hand] Connecting on {port}...", flush=True)
                self.dxl_client = DynamixelClient(list(self.config.motor_ids), port, self.config.baudrate)
                self.dxl_client.connect()
                self._configure_controller()
                self._start_command_thread()
                print(f"[leap_hand] Connected on {port}.", flush=True)
                return
            except Exception as exc:
                last_error = exc
                if self.dxl_client is not None:
                    try:
                        self.dxl_client.disconnect()
                    except Exception:
                        pass
                    self.dxl_client = None

        message = (
            "Failed to connect LEAP hand."
            f" attempted_ports={attempted_ports or '[]'}"
            f" missing_ports={missing_ports or '[]'}"
            " (If you ran `sudo usermod -aG dialout $USER`, log out/in or run `newgrp dialout`.)"
        )
        raise RuntimeError(message) from last_error

    def reset(self):
        self.qpos[:] = 0.0
        if self.config.home_position is not None:
            self.qpos[:] = np.asarray(self.config.home_position, dtype=float)
        self._apply_qpos_to_model(self.qpos)
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
            self._apply_qpos_to_model(self.qpos)
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
        if self.dxl_client is not None:
            self._set_target_qpos(self.qpos)

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

    def _configure_controller(self) -> None:
        if self.dxl_client is None:
            raise RuntimeError("LEAP hand is not connected.")

        motor_ids = list(self.config.motor_ids)
        side_to_side_motor_ids = list(self.config.side_to_side_motor_ids)

        self.dxl_client.sync_write(motor_ids, np.ones(len(motor_ids)) * self.config.control_mode, 11, 1)
        remaining_ids = self.dxl_client.set_torque_enabled(motor_ids, True)
        if remaining_ids:
            raise RuntimeError(
                "LEAP hand did not respond to torque enable for motor IDs "
                f"{remaining_ids}. Common causes: wrong `baudrate`, wrong `port`, "
                "insufficient power, or wrong Dynamixel protocol/wiring."
            )
        self.dxl_client.sync_write(motor_ids, np.ones(len(motor_ids)) * self.config.kp, 84, 2)
        self.dxl_client.sync_write(
            side_to_side_motor_ids,
            np.ones(len(side_to_side_motor_ids)) * (self.config.kp * 0.75),
            84,
            2,
        )
        self.dxl_client.sync_write(motor_ids, np.ones(len(motor_ids)) * self.config.ki, 82, 2)
        self.dxl_client.sync_write(motor_ids, np.ones(len(motor_ids)) * self.config.kd, 80, 2)
        self.dxl_client.sync_write(
            side_to_side_motor_ids,
            np.ones(len(side_to_side_motor_ids)) * (self.config.kd * 0.75),
            80,
            2,
        )
        self.dxl_client.sync_write(motor_ids, np.ones(len(motor_ids)) * self.config.curr_lim, 102, 2)
        self.dxl_client.write_desired_pos(motor_ids, self._home_device_joints())

    def _home_device_joints(self) -> np.ndarray:
        if self.config.home_position is not None:
            return np.asarray(self.config.home_position, dtype=float)
        return np.asarray(
            self._leap_utils.allegro_to_LEAPhand(np.zeros(len(self.config.motor_ids), dtype=float)),
            dtype=float,
        )

    def _model_to_device_joint_values(self, model_joints: list[float] | np.ndarray) -> np.ndarray:
        return np.asarray(
            self._leap_utils.angle_safety_clip(self._leap_utils.LEAPsim_to_LEAPhand(model_joints)),
            dtype=float,
        )

    def _device_to_model_joint_values(self, device_joints: list[float] | np.ndarray) -> np.ndarray:
        return np.asarray(self._leap_utils.LEAPhand_to_LEAPsim(device_joints), dtype=float)

    def _write_qpos_to_hardware(self, qpos: np.ndarray) -> None:
        if self.dxl_client is None:
            raise RuntimeError("LEAP hand is not connected.")
        self.dxl_client.write_desired_pos(
            list(self.config.motor_ids),
            self._model_to_device_joint_values(qpos),
        )

    def _set_target_qpos(self, qpos: np.ndarray, immediate: bool = False) -> None:
        with self._command_lock:
            if immediate:
                self._last_sent_qpos[:] = qpos
                self._interp_start_qpos[:] = qpos
                self._target_qpos[:] = qpos
                self._interp_start_time = time.perf_counter()
                self._write_qpos_to_hardware(qpos)
                return

            self._interp_start_qpos[:] = self._last_sent_qpos
            self._target_qpos[:] = qpos
            self._interp_start_time = time.perf_counter()

    def _start_command_thread(self) -> None:
        if self._command_thread is not None and self._command_thread.is_alive():
            return
        self._command_thread_stop.clear()
        self._command_thread = threading.Thread(target=self._command_loop, name="leap-hand-command", daemon=True)
        self._command_thread.start()

    def _stop_command_thread(self) -> None:
        self._command_thread_stop.set()
        if self._command_thread is not None:
            self._command_thread.join(timeout=1.0)
        self._command_thread = None

    def _command_loop(self) -> None:
        period_s = 1.0 / self._command_rate_hz
        while not self._command_thread_stop.is_set():
            start_time = time.perf_counter()
            with self._command_lock:
                elapsed = time.perf_counter() - self._interp_start_time
                alpha = min(1.0, elapsed / self._interp_duration_s)
                qpos = (1.0 - alpha) * self._interp_start_qpos + alpha * self._target_qpos
                self._last_sent_qpos[:] = qpos
            self._write_qpos_to_hardware(qpos)
            elapsed = time.perf_counter() - start_time
            time.sleep(period_s - elapsed if elapsed < period_s else 0.0)
            print(f"[leap_hand] Command loop iteration took {elapsed:.6f}s", flush=True)

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

    def _action_to_targets(self, action: dict[str, float]) -> dict[str, list[float]]:
        targets = {
            "wrist": [float(action[f"wrist.position.{a}"]) for a in "xyz"],
        }
        for tip in ("thumb", "index", "middle", "ring"):
            if all(f"{tip}.position.{a}" in action for a in "xyz"):
                scale = float(self.config.target_scale_factors.get(tip, 1.0))
                targets[tip] = [scale * float(action[f"{tip}.position.{a}"]) for a in "xyz"]
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
    hand.connect()

    while True:
        action = teleop.get_action()
        hand.apply_commands(action)
        time.sleep(0.01)
