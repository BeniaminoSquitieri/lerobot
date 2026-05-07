"""@file config.py
@brief Configuration dataclasses for the sandwich BT Python execution layer.

Each dataclass mirrors the YAML schema used by `server.py` to load the
runtime configuration. The server reads one root config (see
`SkillCommandServerConfig`) and uses the contained skill entries to
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
        """@brief Validate transition semantics immediately after YAML parsing."""
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
    # Metadata source for policy features. "dataset" loads LeRobot metadata from
    # dataset_repo_id; "robot" builds metadata from the live robot features, like
    # custom_manipulator/record.py does for rollout.
    metadata_source: str = "dataset"
    # Time to wait after the rollout ends before declaring completion.
    settle_time_s: float = 0.0

    def __post_init__(self) -> None:
        """@brief Validate policy metadata and checkpoint requirements."""
        if self.metadata_source not in {"dataset", "robot"}:
            raise ValueError(
                f"Skill '{self.name}' has unsupported metadata_source={self.metadata_source!r}. "
                "Expected 'dataset' or 'robot'."
            )
        # The skill must reference a pretrained model path (either local folder
        # or a Hugging Face Hub id). This prevents accidental runtime failures
        # where a skill is declared but has no model to run.
        if self.policy.pretrained_path is None:
            raise ValueError(
                f"Skill '{self.name}' requires a pretrained checkpoint. "
                "Set skill.policy.pretrained_path to a local checkpoint or Hub model."
            )


@dataclass
class SkillCommandServerConfig:
    """Top-level configuration for the Python ROS2 skill command server.

    This root config is what `server.py` parses at startup. It contains the
    robot description, the list of learned skills, and server-level
    adapters/processors used during execution.
    """
    # Robot hardware configuration (CustomManipulatorConfig contains arm/gripper/cameras).
    robot: CustomManipulatorConfig
    # List of learned skills available to the BT runtime.
    skills: list[PrimitiveSkillConfig]
    # ROS2 service name the server will advertise.
    bt_command_service: str = "/sandwich_bt/run"
    # ROS2 service name used by the BT runtime to query VLM check state.
    vlm_state_service: str = "/sandwich_bt/vlm_state"
    # Legacy ROS2 service name used to report success or failure.
    legacy_vlm_result_service: str = "/sandwich_bt/vlm_result_legacy"
    # Topic published whenever the BT is blocked on a scene verdict.
    vlm_request_topic: str = "/sandwich_bt/vlm_request"
    # Topic consumed from a manual tester or VLM to resolve the active scene verdict.
    vlm_result_topic: str = "/sandwich_bt/vlm_result"
    # Maximum seconds to wait for an external verifier SUCCESS after a command
    # opens a VLM check attempt. Zero disables automatic timeout-to-failure.
    vlm_timeout_s: float = 30.0
    # Control loop frequency in Hz used by the executor.
    fps: int = 10
    # Whether to publish/display diagnostic data for debugging.
    display_data: bool = True
    # Whether the server should play audible feedback sounds on events.
    play_sounds: bool = True
    # Attempt to reset the robot hardware when the server starts.
    reset_robot_on_startup: bool = True
    # Reset the robot immediately before every learned skill rollout, matching
    # the standalone custom_manipulator record/rollout entrypoint.
    reset_robot_before_skill: bool = False
    # Testing convenience: after a real skill finishes, automatically accept its
    # VLM check attempt as if a VLM had returned SUCCESS.
    auto_pass_vlm_check_for_real_skills: bool = False
    # Map of feature/key renames to align dataset keys with live robot keys.
    rename_map: dict[str, str] = field(default_factory=dict)
    # Processor pipeline applied to actions before they reach the robot.
    robot_action_processor: dict = field(default_factory=lambda: {"steps": []})
    # Processor pipeline applied to observations read from the robot.
    robot_observation_processor: dict = field(default_factory=lambda: {"steps": []})

    def __post_init__(self) -> None:
        """@brief Validate top-level server invariants after config loading."""
        # Ensure at least one skill is configured to avoid running an empty server.
        if not self.skills:
            raise ValueError("At least one skill must be configured.")
        # Validate the frame rate is positive.
        if self.fps <= 0:
            raise ValueError("fps must be > 0.")
        if not self.bt_command_service:
            raise ValueError("bt_command_service must not be empty.")
        if not self.vlm_state_service:
            raise ValueError("vlm_state_service must not be empty.")
        if not self.legacy_vlm_result_service:
            raise ValueError("legacy_vlm_result_service must not be empty.")
        if not self.vlm_request_topic:
            raise ValueError("vlm_request_topic must not be empty.")
        if not self.vlm_result_topic:
            raise ValueError("vlm_result_topic must not be empty.")
        if self.vlm_timeout_s < 0:
            raise ValueError("vlm_timeout_s must be >= 0.")
