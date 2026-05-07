import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from lerobot.teleoperators.teleoperator import Teleoperator
from lerobot.utils.rotation import Rotation as R
from lerobot.utils.errors import DeviceNotConnectedError

from .config_metareader import MetaReaderConfig

repo_root = Path(__file__).resolve().parents[4]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


TIPS = ("thumb", "index", "middle", "ring", "little")
METAREADER_TRANSFORM = np.array([[0, 0, -1], [-1, 0, 0], [0, 1, 0]], dtype=float)
HOME_ROT = R.from_rotvec([np.pi, 0.0, 0.0])


def _get_metareader_module():
    try:
        import metareader
    except ImportError as exc:
        raise ImportError(
            "Missing optional dependency `metareader`. "
            "It is only required when using the `metareader` teleoperator."
        ) from exc

    return metareader


def _tip_features(prefix: str = "") -> dict[str, type[float]]:
    return {f"{prefix}{tip}.position.{axis}": float for tip in TIPS for axis in "xyz"}


def _wrist_features(prefix: str = "") -> dict[str, type[float]]:
    return {f"{prefix}wrist.position.{axis}": float for axis in "xyz"}


class _CtrlClutch:
    def __init__(self):
        self.pressed = False
        self._listener = None

    def start(self) -> None:
        from pynput import keyboard

        clutch_keys = {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}

        self._listener = keyboard.Listener(
            on_press=lambda key: setattr(self, "pressed", self.pressed or key in clutch_keys),
            on_release=lambda key: setattr(self, "pressed", False if key in clutch_keys else self.pressed),
        )
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
        self._listener = None
        self.pressed = False


class MetaReaderTeleoperator(Teleoperator):
    config_class = MetaReaderConfig
    name = "metareader"

    def __init__(self, config: MetaReaderConfig):
        self.config = config
        self._clutch = _CtrlClutch()
        self._reader = None
        self._is_connected = False
        self._last_action = self._neutral_action(0.0)
        super().__init__(config)

    @property
    def action_features(self) -> dict:
        return {
            "position.x": float,
            "position.y": float,
            "position.z": float,
            "orientation.x": float,
            "orientation.y": float,
            "orientation.z": float,
            "is_engaged": float,
            "exit_episode": float,
            "discard_episode": float,
            "hand_tracking_valid": float,
            **_wrist_features(),
            **_tip_features(),
        }

    @property
    def feedback_features(self) -> dict:
        return {}

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def is_calibrated(self) -> bool:
        return True

    def connect(self, calibrate: bool = True) -> None:
        del calibrate
        if self._is_connected:
            return
        print("[metareader] Creating MetaReader client...", flush=True)
        self._reader = _get_metareader_module().MetaReader(
            port=self.config.port,
            tcp_port=self.config.tcp_port,
            no_advertise=self.config.no_advertise,
            auto_adb_reverse=self.config.auto_adb_reverse,
        )
        if hasattr(self._reader, "__enter__"):
            print("[metareader] Entering MetaReader context...", flush=True)
            self._reader.__enter__()
        print("[metareader] Starting clutch listener...", flush=True)
        self._clutch.start()
        print("[metareader] Waiting for first frame...", flush=True)
        deadline = time.monotonic() + self.config.connection_timeout_s
        while time.monotonic() < deadline:
            frame = self._reader.read_latest(timeout=self.config.read_timeout_s)
            if frame is not None:
                self._last_action = self._frame_to_action(frame)
                self._is_connected = True
                print("[metareader] First frame received.", flush=True)
                return
        self.disconnect()
        raise TimeoutError("MetaReader did not produce any frame before timeout.")

    def calibrate(self) -> None:
        pass

    def configure(self) -> None:
        pass

    def get_action(self) -> dict[str, Any]:
        if not self._is_connected or self._reader is None:
            raise DeviceNotConnectedError(f"{self} is not connected.")
        frame = self._reader.read_latest(timeout=self.config.read_timeout_s)
        if frame is None:
            return {**self._last_action, "is_engaged": 0.0, "hand_tracking_valid": 0.0}
        self._last_action = self._frame_to_action(frame)
        return dict(self._last_action)

    def send_feedback(self, feedback: dict[str, Any]) -> None:
        del feedback

    def disconnect(self) -> None:
        self._clutch.stop()
        if self._reader is not None and hasattr(self._reader, "__exit__"):
            self._reader.__exit__(None, None, None)
        self._reader = None
        self._is_connected = False

    def _neutral_action(self, engaged: float) -> dict[str, float]:
        return {
            "position.x": 0.0,
            "position.y": 0.0,
            "position.z": 0.0,
            "orientation.x": 0.0,
            "orientation.y": 0.0,
            "orientation.z": 0.0,
            "is_engaged": engaged,
            "exit_episode": 0.0,
            "discard_episode": 0.0,
            "hand_tracking_valid": 0.0,
            **{key: 0.0 for key in _wrist_features()},
            **{key: 0.0 for key in _tip_features()},
        }

    def _frame_to_action(self, frame: Any) -> dict[str, float]:
        hand = frame.right_hand
        palm = getattr(hand.palm, "pose", None)
        engaged = 1.0
        if engaged == 0.0 or palm is None or not palm.valid:
            return self._neutral_action(engaged)

        palm_rotation = METAREADER_TRANSFORM @ R.from_quat(palm.orientation).as_matrix()
        rotvec = (HOME_ROT.inv() * R.from_matrix(palm_rotation)).as_rotvec()
        palm_position = METAREADER_TRANSFORM @ np.asarray(palm.position, dtype=float)
        palm_inverse = R.from_matrix(palm_rotation).inv()
        action = self._neutral_action(engaged)
        hand_tracking_valid = bool(hand.wrist.tracked)
        action.update(
            {
                "position.x": float(palm_position[0]),
                "position.y": float(palm_position[1]),
                "position.z": float(palm_position[2]),
                "orientation.x": float(rotvec[0]),
                "orientation.y": float(rotvec[1]),
                "orientation.z": float(rotvec[2]),
            }
        )

        wrist_pose = getattr(hand.wrist, "pose", None)
        if wrist_pose is not None and wrist_pose.valid:
            wrist_position = METAREADER_TRANSFORM @ np.asarray(wrist_pose.position, dtype=float)
            wrist_relative = palm_inverse.apply(wrist_position - palm_position)
            for axis, value in zip("xyz", wrist_relative, strict=True):
                action[f"wrist.position.{axis}"] = float(value)

        for tip in TIPS:
            fingertip = hand.fingertips.get(f"{tip}_tip")
            pose = getattr(fingertip, "pose", None)
            if pose is None or not pose.valid:
                if tip != "little":
                    hand_tracking_valid = False
                continue
            tip_position = METAREADER_TRANSFORM @ np.asarray(pose.position, dtype=float)
            relative = palm_inverse.apply(tip_position - palm_position)
            action[f"{tip}.position.x"] = float(relative[0])
            action[f"{tip}.position.y"] = float(relative[1])
            action[f"{tip}.position.z"] = float(relative[2])
        action["hand_tracking_valid"] = float(
            hand_tracking_valid and wrist_pose is not None and wrist_pose.valid
        )
        return action
