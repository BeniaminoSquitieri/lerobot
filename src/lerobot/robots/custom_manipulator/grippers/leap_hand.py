# pyright: reportMissingImports=false
import sys
from pathlib import Path

import numpy as np

from .config_leap_hand import JOINT_ACTIONS, TIPS, LeapHandConfig
from .leap_hand_debug import LeapHandDebugTools


def _require_klampt():
    try:
        from klampt import IKObjective, IKSolver, WorldModel
        from klampt.math import so3, vectorops
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "LEAP hand support requires the optional `klampt` package."
        ) from exc

    return IKObjective, IKSolver, WorldModel, so3, vectorops


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


class LeapHand:
    end_effector_transforms = {
        "dummy": np.eye(4),
        "panda": np.array(
            [
                [1.0, 0.0, 0.0, 0.0455 + 0.065],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.036],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=float,
        ),
    }

    def __init__(self, config: LeapHandConfig | None = None):
        self.config = config or LeapHandConfig()
        self.urdf_path = _resolve_urdf_path(self.config.urdf_path)
        self.dxl_client = None

        _, _, WorldModel, so3, vectorops = _require_klampt()
        _, leap_utils = _get_leap_runtime()

        self._so3 = so3
        self._vectorops = vectorops
        self._leap_utils = leap_utils
        self._palm_center_offset = np.asarray(self.config.palm_center_offset, dtype=float)

        world = WorldModel()
        if not world.loadRobot(self.urdf_path):
            raise RuntimeError(f"Failed to load LEAP hand URDF: {self.urdf_path}")
        self.model = world.robot(0)
        self.world = world

        self.joints = {
            self.model.driver(i).getName(): self.model.driver(i) for i in range(self.model.numDrivers())
        }
        self._command_index_by_driver_name = self._resolve_command_index_by_driver_name()

        self.root_frame = self._resolve_link(self.config.root_link_name)
        self.palm_frame = self._resolve_link(self.config.palm_link_name, fallback="palm_lower")
        self.tip_points = {
            tip: self._resolve_link(self.config.tip_point_link_names[tip])
            for tip in self.config.tip_point_link_names
        }

        self._debug = LeapHandDebugTools(
            urdf_path=self.urdf_path,
            tip_names=TIPS,
            tip_scale_factors=self.config.tip_scale_factors,
            enable_tip_scale_tuner=self.config.enable_tip_scale_tuner,
            enable_rerun_visualization=self.config.visualize,
            palm_frame=self.palm_frame,
            root_frame=self.root_frame,
            palm_center_offset=self._palm_center_offset,
            tips=self.tip_points,
            palm_to_target_rot=PALM_TO_TARGET_ROT,
        )

    def get_end_effector_transform(self, arm_type: str) -> np.ndarray:
        return self.end_effector_transforms[arm_type].copy()

    def connect(self):
        DynamixelClient, _ = _get_leap_runtime()
        candidate_ports = [self.config.port] if self.config.port else []
        candidate_ports.extend(port for port in self.config.port_candidates if port not in candidate_ports)

        last_error = None
        for port in candidate_ports:
            try:
                print(f"[leap_hand] Connecting on {port}...", flush=True)
                self.dxl_client = DynamixelClient(list(self.config.motor_ids), port, self.config.baudrate)
                self.dxl_client.connect()
                self._configure_controller()
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

        raise RuntimeError(f"Failed to connect LEAP hand on ports {candidate_ports}.") from last_error

    def disconnect(self):
        if self.dxl_client is not None:
            self.dxl_client.disconnect()
        self.dxl_client = None
        self._debug.close()

    close = disconnect

    def reset(self):
        home_device_joints = self._home_device_joints()
        self._set_model_joint_values(self._device_to_model_joint_values(home_device_joints))
        self._send(self.joints)

    def _get_fingertips(self, device_joints: list[float] | np.ndarray) -> dict[str, float]:
        previous_joint_values = {
            name: self.joints[name].getValue() for name in self._command_index_by_driver_name
        }

        model_joints = self._device_to_model_joint_values(device_joints)
        for name, idx in self._command_index_by_driver_name.items():
            self.joints[name].setValue(float(model_joints[idx]))
        self.model.setConfig(self.model.getConfig())

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
            for tip, link in self.tip_points.items()
        }

        fingertips = {
            f"{tip}.position.{axis}": float(value)
            for tip, tip_position in tip_positions.items()
            for axis, value in zip("xyz", tip_position)
        }

        for name, value in previous_joint_values.items():
            self.joints[name].setValue(value)
        self.model.setConfig(self.model.getConfig())
        return fingertips

    def apply_commands(self, action: dict | None = None, **kwargs):
        del kwargs
        if not action:
            return

        self._debug.poll()

        model_joints = self._extract_model_joint_targets(action)
        if model_joints is None:
            return

        self._set_model_joint_values(model_joints)
        fingertip_values = self._get_fingertips_from_current_model_state()
        self._debug.log_state(self._link_name_to_model_joint_values(model_joints), fingertip_values)
        self._debug.poll()
        return self._send(self.joints)

    @property
    def action_features(self) -> dict:
        return JOINT_ACTIONS

    @property
    def features(self) -> dict:
        return {f"{tip}.position.{axis}": float for tip in TIPS for axis in "xyz"}

    def get_sensors(self):
        device_joints = self._read()
        fingertip_values = self._get_fingertips(device_joints)

        self._debug.log_state(
            self._link_name_to_model_joint_values(self._device_to_model_joint_values(device_joints)),
            fingertip_values,
        )
        self._debug.poll()
        return fingertip_values

    def _configure_controller(self):
        if self.dxl_client is None:
            raise RuntimeError("LEAP hand is not connected.")

        motor_ids = list(self.config.motor_ids)
        side_to_side_motor_ids = list(self.config.side_to_side_motor_ids)

        self.dxl_client.sync_write(motor_ids, np.ones(len(motor_ids)) * self.config.control_mode, 11, 1)
        self.dxl_client.set_torque_enabled(motor_ids, True)
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

    def _resolve_command_index_by_driver_name(self) -> dict[str, int]:
        command_index_by_driver_name = {}
        for driver_name, driver in self.joints.items():
            affected_link = self.model.link(driver.getAffectedLink()).getName()
            if affected_link in self.config.command_index_by_link_name:
                command_index_by_driver_name[driver_name] = self.config.command_index_by_link_name[
                    affected_link
                ]

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
                    f"[leap_hand] Link {link_name!r} not found, using {fallback!r} instead.",
                    flush=True,
                )
                return fallback_link

        raise RuntimeError(f"Link {link_name!r} was not found in {self.urdf_path}.")

    def _set_model_joint_values(self, model_joints: list[float] | np.ndarray):
        for name, idx in self._command_index_by_driver_name.items():
            self.joints[name].setValue(float(model_joints[idx]))
        self.model.setConfig(self.model.getConfig())

    def _current_model_joint_values(self) -> np.ndarray:
        model_joints = np.zeros(len(self.config.motor_ids), dtype=float)
        for name, idx in self._command_index_by_driver_name.items():
            model_joints[idx] = float(self.joints[name].getValue())
        return model_joints

    def _extract_model_joint_targets(self, action: dict[str, float]) -> np.ndarray | None:
        model_joints = self._current_model_joint_values()
        has_gripper_command = False

        for link_name, idx in self.config.command_index_by_link_name.items():
            key = f"gripper.{link_name}"
            if key not in action:
                continue
            model_joints[idx] = float(action[key])
            has_gripper_command = True

        if not has_gripper_command:
            return None
        return model_joints

    def _device_to_model_joint_values(self, device_joints: list[float] | np.ndarray) -> np.ndarray:
        return np.asarray(self._leap_utils.LEAPhand_to_LEAPsim(device_joints), dtype=float)

    def _model_to_device_joint_values(self, model_joints: list[float] | np.ndarray) -> np.ndarray:
        return np.asarray(
            self._leap_utils.angle_safety_clip(self._leap_utils.LEAPsim_to_LEAPhand(model_joints)),
            dtype=float,
        )

    def _home_device_joints(self) -> np.ndarray:
        if self.config.home_position is not None:
            return np.asarray(self.config.home_position, dtype=float)
        return np.asarray(
            self._leap_utils.allegro_to_LEAPhand(np.zeros(len(self.config.motor_ids), dtype=float)),
            dtype=float,
        )

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
            for tip, link in self.tip_points.items()
        }

        return {
            f"{tip}.position.{axis}": float(value)
            for tip, tip_position in tip_positions.items()
            for axis, value in zip("xyz", tip_position)
        }

    def _send(self, joints) -> None:
        if self.dxl_client is None:
            raise RuntimeError("LEAP hand is not connected.")

        model_joints = np.zeros(len(self.config.motor_ids), dtype=float)
        for name, joint in joints.items():
            if name not in self._command_index_by_driver_name:
                continue
            model_joints[self._command_index_by_driver_name[name]] = float(joint.getValue())

        # self.dxl_client.write_desired_pos(
        #     list(self.config.motor_ids), self._model_to_device_joint_values(model_joints)
        # )

    def _read(self) -> np.ndarray:
        if self.dxl_client is None:
            raise RuntimeError("LEAP hand is not connected.")

        obs = np.asarray(self.dxl_client.read_pos(), dtype=float)
        if obs.shape[0] != len(self.config.motor_ids):
            raise RuntimeError(
                "Unexpected LEAP hand observation size: "
                f"expected {len(self.config.motor_ids)}, got {obs.shape[0]}."
            )
        return obs
