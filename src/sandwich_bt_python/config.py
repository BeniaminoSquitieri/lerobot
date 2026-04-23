"""Configuration objects for the Python execution layer.

Flow role:
1. The BT asks for a named skill or recovery.
2. The Python server uses these dataclasses to know:
   - which checkpoint to load,
   - which dataset metadata/stats to use,
   - how to decide success/failure,
   - which recovery motions are available.
"""

from dataclasses import dataclass, field
from pathlib import Path

from lerobot.configs.policies import PreTrainedConfig
from lerobot.policies.act.configuration_act import ACTConfig  # noqa: F401
from lerobot.policies.diffusion.configuration_diffusion import DiffusionConfig  # noqa: F401
from lerobot.policies.groot.configuration_groot import GrootConfig  # noqa: F401
from lerobot.robots.custom_manipulator.config_custom_manipulator import CustomManipulatorConfig


@dataclass
class ObservationConditionConfig:
    # One scalar check on processed robot observations.
    key: str
    op: str = "gt"
    value: float = 0.0
    value_max: float | None = None
    use_abs: bool = False


@dataclass
class SkillTransitionConfig:
    # Defines when one skill rollout should terminate.
    mode: str = "timeout"
    min_duration_s: float = 0.0
    max_duration_s: float = 12.0
    success_conditions: list[ObservationConditionConfig] = field(default_factory=list)
    failure_conditions: list[ObservationConditionConfig] = field(default_factory=list)

    def __post_init__(self) -> None:
        allowed_modes = {"timeout", "all_conditions", "all_conditions_or_timeout"}
        if self.mode not in allowed_modes:
            raise ValueError(f"Unsupported transition mode '{self.mode}'. Expected one of {sorted(allowed_modes)}.")
        if self.max_duration_s <= 0:
            raise ValueError("transition.max_duration_s must be > 0.")


@dataclass
class PrimitiveSkillConfig:
    # Full description of one learned primitive.
    name: str
    dataset_repo_id: str
    task: str
    policy: PreTrainedConfig
    transition: SkillTransitionConfig = field(default_factory=SkillTransitionConfig)
    dataset_root: str | Path | None = None
    dataset_revision: str | None = None
    settle_time_s: float = 0.0

    def __post_init__(self) -> None:
        if self.policy.pretrained_path is None:
            raise ValueError(
                f"Skill '{self.name}' requires a pretrained checkpoint. "
                "Set skill.policy.pretrained_path to a local checkpoint or Hub model."
            )


@dataclass
class RecoveryStepConfig:
    # One deterministic recovery primitive executed between BT attempts.
    kind: str
    duration_s: float = 0.5
    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0
    droll: float = 0.0
    dpitch: float = 0.0
    dyaw: float = 0.0
    gripper_value: float | None = None

    def __post_init__(self) -> None:
        allowed_kinds = {"pause", "robot_reset", "cartesian_delta", "set_gripper"}
        if self.kind not in allowed_kinds:
            raise ValueError(f"Unsupported recovery step '{self.kind}'. Expected one of {sorted(allowed_kinds)}.")
        if self.kind != "robot_reset" and self.duration_s < 0:
            raise ValueError("recovery duration_s must be >= 0.")
        if self.kind == "set_gripper" and self.gripper_value is None:
            raise ValueError("Recovery step 'set_gripper' requires gripper_value.")


@dataclass
class RecoveryConfig:
    # Named list of recovery steps. The BT refers to recoveries by this name.
    name: str
    steps: list[RecoveryStepConfig] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.steps:
            raise ValueError(f"Recovery '{self.name}' must define at least one step.")


@dataclass
class SkillCommandServerConfig:
    # Root config for the Python ROS2 server.
    # This is the file the server reads at startup.
    robot: CustomManipulatorConfig
    skills: list[PrimitiveSkillConfig]
    recoveries: list[RecoveryConfig] = field(default_factory=list)
    service_name: str = "/sandwich_bt/run_command"
    fps: int = 10
    display_data: bool = True
    play_sounds: bool = True
    reset_robot_on_startup: bool = True
    rename_map: dict[str, str] = field(default_factory=dict)
    robot_action_processor: dict = field(default_factory=lambda: {"steps": []})
    robot_observation_processor: dict = field(default_factory=lambda: {"steps": []})

    def __post_init__(self) -> None:
        if not self.skills:
            raise ValueError("At least one skill must be configured.")
        if self.fps <= 0:
            raise ValueError("fps must be > 0.")
