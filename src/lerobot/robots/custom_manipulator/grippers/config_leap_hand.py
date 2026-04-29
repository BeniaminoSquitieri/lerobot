from dataclasses import dataclass, field
from pathlib import Path

from ..configs import GripperConfig

TIPS = ("thumb", "index", "middle", "ring")
TIP_ACTIONS = {f"action.{tip}.position.{axis}": float for tip in TIPS for axis in "xyz"}
DEFAULT_TIP_LINK_NAMES = {
    "thumb": "thumb_fingertip",
    "index": "shifted_fingertip",
    "middle": "fingertip_2",
    "ring": "fingertip_3",
}
DEFAULT_TIP_SCALE_FACTORS = {tip: 1.0 for tip in TIPS}
DEFAULT_PALM_CENTER_OFFSET = (-0.0, -0.0, -0.0)
DEFAULT_COMMAND_INDEX_BY_LINK_NAME = {
    "pip": 0,
    "mcp_joint": 1,
    "dip": 2,
    "fingertip": 3,
    "pip_2": 4,
    "mcp_joint_2": 5,
    "dip_2": 6,
    "fingertip_2": 7,
    "pip_3": 8,
    "mcp_joint_3": 9,
    "dip_3": 10,
    "fingertip_3": 11,
    "pip_4": 12,
    "thumb_pip": 13,
    "thumb_dip": 14,
    "thumb_fingertip": 15,
}
DEFAULT_MOTOR_IDS = tuple(range(16))
DEFAULT_PORT_CANDIDATES = ("/dev/ttyUSB0", "/dev/ttyUSB1", "COM13")
DEFAULT_SIDE_TO_SIDE_MOTOR_IDS = (0, 4, 8)


def _default_leap_urdf_path() -> str:
    return str(Path(__file__).resolve().parents[5] / "leap_hand" / "leap_hand_urdf" / "robot.urdf")


@GripperConfig.register_subclass("leap_hand")
@dataclass
class LeapHandConfig(GripperConfig):
    port: str | None = None
    port_candidates: tuple[str, ...] = DEFAULT_PORT_CANDIDATES
    baudrate: int = 4_000_000
    motor_ids: tuple[int, ...] = DEFAULT_MOTOR_IDS
    side_to_side_motor_ids: tuple[int, ...] = DEFAULT_SIDE_TO_SIDE_MOTOR_IDS
    control_mode: int = 5
    use_delta_actions: bool = False
    kp: int = 600
    ki: int = 0
    kd: int = 200
    curr_lim: int = 350
    urdf_path: str = field(default_factory=_default_leap_urdf_path)
    palm_link_name: str = "shifted_palm"
    palm_center_offset: tuple[float, float, float] = DEFAULT_PALM_CENTER_OFFSET
    niter: int = 20000
    tip_link_names: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_TIP_LINK_NAMES))
    tip_scale_factors: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_TIP_SCALE_FACTORS))
    command_index_by_link_name: dict[str, int] = field(
        default_factory=lambda: dict(DEFAULT_COMMAND_INDEX_BY_LINK_NAME)
    )
    home_position: list[float] | None = None
    enable_tip_scale_tuner: bool = False
    visualize: bool = False

    @property
    def type(self) -> str:
        return "leap_hand"
