"""Configuration dataclasses for the sandwich BT Python execution layer.

Each dataclass mirrors the YAML schema used by `server.py` to load the
runtime configuration. The server reads one root config (see
`SkillCommandServerConfig`) and uses the contained skill/recovery entries to
drive execution.

The comments below annotate every field and validation to make the contract
explicit for maintainers and integrators.
"""

from dataclasses import dataclass, field
from pathlib import Path

from lerobot.configs.policies import PreTrainedConfig
# Import known policy families so `draccus` can deserialize them when the YAML
# contains a `policy` entry. These imports are intentionally here to register
# the subclasses; they are not referenced directly in code below.
from lerobot.policies.act.configuration_act import ACTConfig  # noqa: F401
from lerobot.policies.diffusion.configuration_diffusion import DiffusionConfig  # noqa: F401
from lerobot.policies.groot.configuration_groot import GrootConfig  # noqa: F401
from lerobot.robots.custom_manipulator.config_custom_manipulator import CustomManipulatorConfig


@dataclass
class ObservationConditionConfig:
    """A single scalar predicate evaluated on processed observations.

    Attributes:
    - `key`: the observation dict key to read (already processed by the pipeline).
    - `op`: comparison operator, one of 'gt','ge','lt','le','eq','between'.
    - `value`: primary numeric threshold.
    - `value_max`: secondary threshold used by 'between'.
    - `use_abs`: whether to compare against the absolute value.
    """
    # Observation key to check (string).
    key: str
    # Comparison operator (default greater-than).
    op: str = "gt"
    # Numeric threshold used for the comparison.
    value: float = 0.0
    # Optional upper bound for 'between' comparisons.
    value_max: float | None = None
    # If true, use abs(observation_value) for the comparison.
    use_abs: bool = False


@dataclass
class SkillTransitionConfig:
    """How a skill rollout should terminate.

    Fields:
    - `mode`: termination semantics (timeout-based or predicate-based).
    - `min_duration_s`/`max_duration_s`: duration bounds for the rollout.
    - `success_conditions`: list of predicates that, when all true, indicate success.
    - `failure_conditions`: list of predicates that, when any true, indicate failure.
    """
    # Termination mode. See README for semantics.
    mode: str = "timeout"
    # Minimum execution time in seconds before considering termination.
    min_duration_s: float = 0.0
    # Maximum execution time in seconds (timeout). Must be > 0.
    max_duration_s: float = 12.0
    # Success predicates: all must be true for 'all_conditions' mode.
    success_conditions: list[ObservationConditionConfig] = field(default_factory=list)
    # Failure predicates: any true will end the rollout with failure.
    failure_conditions: list[ObservationConditionConfig] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Validate that the mode is one of the supported enumerations.
        allowed_modes = {"timeout", "all_conditions", "all_conditions_or_timeout", "until_success"}
        if self.mode not in allowed_modes:
            raise ValueError(f"Unsupported transition mode '{self.mode}'. Expected one of {sorted(allowed_modes)}.")
        # Ensure we don't have a non-positive timeout which would be nonsensical.
        if self.max_duration_s <= 0:
            raise ValueError("transition.max_duration_s must be > 0.")
        # An unbounded rollout still needs an explicit success criterion,
        # otherwise it can never terminate on the success path.
        if self.mode == "until_success" and not self.success_conditions:
            raise ValueError("transition.mode='until_success' requires at least one success_condition.")


@dataclass
class PrimitiveSkillConfig:
    """Configuration for one learned primitive (a named skill).

    This dataclass describes the mapping between a BT command name and the
    underlying dataset/policy/termination semantics used at runtime.
    """
    # Unique name used by the BT to refer to this learned primitive.
    name: str
    # HF dataset or repo id used to load metadata/stats (not for replay).
    dataset_repo_id: str
    # Natural language or short description of the task this skill performs.
    task: str
    # The policy config (a PreTrainedConfig subclass) that points to the model.
    policy: PreTrainedConfig
    # How and when the skill should stop executing.
    transition: SkillTransitionConfig = field(default_factory=SkillTransitionConfig)
    # Optional local dataset root for metadata lookup
    dataset_root: str | Path | None = None
    # Optional dataset revision (branch/commit) to select metadata.
    dataset_revision: str | None = None
    # Time to wait after the rollout ends before declaring completion.
    settle_time_s: float = 0.0

    def __post_init__(self) -> None:
        # The skill must reference a pretrained model path (either local folder
        # or a Hugging Face Hub id). This prevents accidental runtime failures
        # where a skill is declared but has no model to run.
        if self.policy.pretrained_path is None:
            raise ValueError(
                f"Skill '{self.name}' requires a pretrained checkpoint. "
                "Set skill.policy.pretrained_path to a local checkpoint or Hub model."
            )


@dataclass
class RecoveryStepConfig:
    """One deterministic recovery primitive executed between BT attempts.

    Recovery steps are small, deterministic motions or state changes (pauses,
    robot resets, small cartesian deltas, or explicit gripper positions).
    """
    # The kind of recovery: 'pause', 'robot_reset', 'cartesian_delta', 'set_gripper'.
    kind: str
    # Duration the step should take, in seconds (ignored for 'robot_reset').
    duration_s: float = 0.5
    # Cartesian delta in meters to apply (x,y,z) for 'cartesian_delta'.
    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0
    # Orientation deltas in radians for roll/pitch/yaw.
    droll: float = 0.0
    dpitch: float = 0.0
    dyaw: float = 0.0
    # Optional gripper target value for 'set_gripper'. Range depends on driver.
    gripper_value: float | None = None

    def __post_init__(self) -> None:
        # Validate allowed kinds to catch typos in YAML configs early.
        allowed_kinds = {"pause", "robot_reset", "cartesian_delta", "set_gripper"}
        if self.kind not in allowed_kinds:
            raise ValueError(f"Unsupported recovery step '{self.kind}'. Expected one of {sorted(allowed_kinds)}.")
        # Durations must be non-negative for motion steps.
        if self.kind != "robot_reset" and self.duration_s < 0:
            raise ValueError("recovery duration_s must be >= 0.")
        # set_gripper requires an explicit target value.
        if self.kind == "set_gripper" and self.gripper_value is None:
            raise ValueError("Recovery step 'set_gripper' requires gripper_value.")


@dataclass
class RecoveryConfig:
    """Named list of recovery steps referenced by the BT.

    The BT only refers to recoveries by name; this dataclass maps that name to
    the concrete sequence of `RecoveryStepConfig` steps to execute when the
    recovery is requested.
    """
    # Name referenced by the BT XML.
    name: str
    # Ordered list of steps that compose the recovery.
    steps: list[RecoveryStepConfig] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.steps:
            raise ValueError(f"Recovery '{self.name}' must define at least one step.")


@dataclass
class SkillCommandServerConfig:
    """Top-level configuration for the Python ROS2 skill command server.

    This root config is what `server.py` parses at startup. It contains the
    robot description, the list of learned skills, named recoveries, and
    server-level adapters/processors used during execution.
    """
    # Robot hardware configuration (CustomManipulatorConfig contains arm/gripper/cameras).
    robot: CustomManipulatorConfig
    # List of learned skills available to the BT runtime.
    skills: list[PrimitiveSkillConfig]
    # Optional named recoveries.
    recoveries: list[RecoveryConfig] = field(default_factory=list)
    # ROS2 service name the server will advertise.
    service_name: str = "/sandwich_bt/run_command"
    # ROS2 service name used by the BT runtime to query external verification state.
    verification_query_service_name: str = "/sandwich_bt/get_skill_verification"
    # ROS2 service name used by an external verifier/VLM to report success or failure.
    verification_report_service_name: str = "/sandwich_bt/report_skill_verification"
    # Control loop frequency in Hz used by the executor.
    fps: int = 10
    # Whether to publish/display diagnostic data for debugging.
    display_data: bool = True
    # Whether the server should play audible feedback sounds on events.
    play_sounds: bool = True
    # Attempt to reset the robot hardware when the server starts.
    reset_robot_on_startup: bool = True
    # Map of feature/key renames to align dataset keys with live robot keys.
    rename_map: dict[str, str] = field(default_factory=dict)
    # Processor pipeline applied to actions before they reach the robot.
    robot_action_processor: dict = field(default_factory=lambda: {"steps": []})
    # Processor pipeline applied to observations read from the robot.
    robot_observation_processor: dict = field(default_factory=lambda: {"steps": []})

    def __post_init__(self) -> None:
        # Ensure at least one skill is configured to avoid running an empty server.
        if not self.skills:
            raise ValueError("At least one skill must be configured.")
        # Validate the frame rate is positive.
        if self.fps <= 0:
            raise ValueError("fps must be > 0.")
        if not self.service_name:
            raise ValueError("service_name must not be empty.")
        if not self.verification_query_service_name:
            raise ValueError("verification_query_service_name must not be empty.")
        if not self.verification_report_service_name:
            raise ValueError("verification_report_service_name must not be empty.")
