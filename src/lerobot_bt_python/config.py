# Comment: executes this BT logic statement.
"""@file config.py
@brief Configuration dataclasses for the LeRobot BT Python execution layer.

Each dataclass mirrors the YAML schema used by `server.py` to load the
runtime configuration. The server reads one root config (see
`SkillCommandServerConfig`) and uses the contained skill entries to
drive execution.

The comments below annotate every field and validation to make the contract
explicit for maintainers and integrators.
"""

# Comment: imports dependencies or symbols required by the module.
from collections import Counter
# Comment: imports dependencies or symbols required by the module.
from dataclasses import dataclass, field
# Comment: imports dependencies or symbols required by the module.
from pathlib import Path

# Comment: imports dependencies or symbols required by the module.
from lerobot.configs.policies import PreTrainedConfig

# Import known policy families so `draccus` can deserialize them when the YAML
# contains a `policy` entry. These imports are intentionally here to register
# the subclasses; they are not referenced directly in code below.
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.act.configuration_act import ACTConfig  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.diffusion.configuration_diffusion import DiffusionConfig  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.groot.configuration_groot import GrootConfig  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.multi_task_dit.configuration_multi_task_dit import MultiTaskDiTConfig  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.pi0.configuration_pi0 import PI0Config  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.pi0_fast.configuration_pi0_fast import PI0FastConfig  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.pi05.configuration_pi05 import PI05Config  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.sac.configuration_sac import SACConfig  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.sac.reward_model.configuration_classifier import RewardClassifierConfig  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.sarm.configuration_sarm import SARMConfig  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.tdmpc.configuration_tdmpc import TDMPCConfig  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.vqbet.configuration_vqbet import VQBeTConfig  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.wall_x.configuration_wall_x import WallXConfig  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.xvla.configuration_xvla import XVLAConfig  # noqa: F401
# Comment: imports dependencies or symbols required by the module.
from lerobot.robots.custom_manipulator.config_custom_manipulator import CustomManipulatorConfig


# Comment: applies a decorator to the following definition.
@dataclass
class ObservationConditionConfig:
    # Comment: executes this BT logic statement.
    """A single scalar predicate evaluated on processed observations.

    Attributes:
    - `key`: the observation dict key to read (already processed by the pipeline).
    - `op`: comparison operator, one of 'gt','ge','lt','le','eq','between'.
    - `value`: primary numeric threshold.
    - `value_max`: secondary threshold used by 'between'.
    - `use_abs`: whether to compare against the absolute value.
    """
    # Observation key to check (string).
    # Comment: executes this BT logic statement.
    key: str
    # Comparison operator (default greater-than).
    # Comment: assigns or prepares a value used by later statements.
    op: str = "gt"
    # Numeric threshold used for the comparison.
    # Comment: assigns or prepares a value used by later statements.
    value: float = 0.0
    # Optional upper bound for 'between' comparisons.
    # Comment: assigns or prepares a value used by later statements.
    value_max: float | None = None
    # If true, use abs(observation_value) for the comparison.
    # Comment: assigns or prepares a value used by later statements.
    use_abs: bool = False


# Comment: applies a decorator to the following definition.
@dataclass
class SkillTransitionConfig:
    # Comment: executes this BT logic statement.
    """How a skill rollout should terminate.

    Fields:
    - `mode`: termination semantics (timeout-based or predicate-based).
    - `min_duration_s`/`max_duration_s`: duration bounds for the rollout.
    - `success_conditions`: list of predicates that, when all true, indicate success.
    - `failure_conditions`: list of predicates that, when any true, indicate failure.
    """
    # Termination mode. See README for semantics.
    # Comment: assigns or prepares a value used by later statements.
    mode: str = "timeout"
    # Minimum execution time in seconds before considering termination.
    # Comment: assigns or prepares a value used by later statements.
    min_duration_s: float = 0.0
    # Maximum execution time in seconds (timeout). Must be > 0.
    # Comment: assigns or prepares a value used by later statements.
    max_duration_s: float = 12.0
    # Success predicates: all must be true for 'all_conditions' mode.
    # Comment: assigns or prepares a value used by later statements.
    success_conditions: list[ObservationConditionConfig] = field(default_factory=list)
    # Failure predicates: any true will end the rollout with failure.
    # Comment: assigns or prepares a value used by later statements.
    failure_conditions: list[ObservationConditionConfig] = field(default_factory=list)

    # Comment: defines the function or method __post_init__.
    def __post_init__(self) -> None:
        # Comment: executes this BT logic statement.
        """@brief Validate transition semantics immediately after YAML parsing."""
        # Validate that the mode is one of the supported enumerations.
        # Comment: assigns or prepares a value used by later statements.
        allowed_modes = {"timeout", "all_conditions", "all_conditions_or_timeout", "until_success"}
        # Comment: evaluates a condition and chooses the branch to run.
        if self.mode not in allowed_modes:
            # Comment: raises an explicit error for the caller.
            raise ValueError(f"Unsupported transition mode '{self.mode}'. Expected one of {sorted(allowed_modes)}.")
        # Ensure we don't have a non-positive timeout which would be nonsensical.
        # Comment: evaluates a condition and chooses the branch to run.
        if self.max_duration_s <= 0:
            # Comment: raises an explicit error for the caller.
            raise ValueError("transition.max_duration_s must be > 0.")
        # An unbounded rollout still needs an explicit success criterion,
        # otherwise it can never terminate on the success path.
        # Comment: evaluates a condition and chooses the branch to run.
        if self.mode == "until_success" and not self.success_conditions:
            # Comment: raises an explicit error for the caller.
            raise ValueError("transition.mode='until_success' requires at least one success_condition.")


# Comment: applies a decorator to the following definition.
@dataclass
class PrimitiveSkillConfig:
    # Comment: executes this BT logic statement.
    """Configuration for one learned primitive (a named skill).

    This dataclass describes the mapping between a BT command name and the
    underlying dataset/policy/termination semantics used at runtime.
    """
    # Unique name used by the BT to refer to this learned primitive.
    # Comment: executes this BT logic statement.
    name: str
    # HF dataset or repo id used to load metadata/stats (not for replay).
    # Comment: executes this BT logic statement.
    dataset_repo_id: str
    # Natural language or short description of the task this skill performs.
    # Comment: executes this BT logic statement.
    task: str
    # Active policy config selected from `policy_variants`, or the legacy direct
    # policy config used by older YAML files.
    # Comment: assigns or prepares a value used by later statements.
    policy: PreTrainedConfig | None = None
    # Optional named policies for the same BT skill, e.g. "act", "smolvla",
    # "diffusion", or any other registered LeRobot policy type.
    # Comment: assigns or prepares a value used by later statements.
    policy_variants: dict[str, PreTrainedConfig] = field(default_factory=dict)
    # Optional per-skill override. When unset, the top-level/default
    # policy_variant is used.
    # Comment: assigns or prepares a value used by later statements.
    policy_variant: str | None = None
    # How and when the skill should stop executing.
    # Comment: assigns or prepares a value used by later statements.
    transition: SkillTransitionConfig = field(default_factory=SkillTransitionConfig)
    # Optional local dataset root for metadata lookup
    # Comment: assigns or prepares a value used by later statements.
    dataset_root: str | Path | None = None
    # Optional dataset revision (branch/commit) to select metadata.
    # Comment: assigns or prepares a value used by later statements.
    dataset_revision: str | None = None
    # Metadata source for policy features. "dataset" loads LeRobot metadata from
    # dataset_repo_id; "robot" builds metadata from the live robot features, like
    # custom_manipulator/record.py does for rollout.
    # Comment: assigns or prepares a value used by later statements.
    metadata_source: str = "dataset"
    # Time to wait after the rollout ends before declaring completion.
    # Comment: assigns or prepares a value used by later statements.
    settle_time_s: float = 0.0

    # Comment: defines the function or method __post_init__.
    def __post_init__(self) -> None:
        # Comment: executes this BT logic statement.
        """@brief Validate policy metadata and checkpoint requirements."""
        # Comment: evaluates a condition and chooses the branch to run.
        if self.metadata_source not in {"dataset", "robot"}:
            # Comment: raises an explicit error for the caller.
            raise ValueError(
                # Comment: assigns or prepares a value used by later statements.
                f"Skill '{self.name}' has unsupported metadata_source={self.metadata_source!r}. "
                # Comment: executes this BT logic statement.
                "Expected 'dataset' or 'robot'."
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: evaluates a condition and chooses the branch to run.
        if self.policy is None and not self.policy_variants:
            # Comment: raises an explicit error for the caller.
            raise ValueError(
                # Comment: executes this BT logic statement.
                f"Skill '{self.name}' requires either policy or policy_variants."
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: evaluates a condition and chooses the branch to run.
        if self.policy is not None and not self.policy_variants:
            # Comment: closes a call, data structure, or multiline block.
            self._validate_policy(self.policy)

    # Comment: defines the function or method select_policy_variant.
    def select_policy_variant(self, variant_name: str) -> None:
        # Comment: executes this BT logic statement.
        """@brief Select and validate the policy variant used for this skill."""
        # Comment: assigns or prepares a value used by later statements.
        selected_variant = self.policy_variant or variant_name
        # Comment: evaluates a condition and chooses the branch to run.
        if self.policy_variants:
            # Comment: evaluates a condition and chooses the branch to run.
            if selected_variant not in self.policy_variants:
                # Comment: assigns or prepares a value used by later statements.
                available = sorted(self.policy_variants)
                # Comment: raises an explicit error for the caller.
                raise ValueError(
                    # Comment: executes this BT logic statement.
                    f"Skill '{self.name}' has no policy variant {selected_variant!r}. "
                    # Comment: executes this BT logic statement.
                    f"Available variants: {available}."
                # Comment: closes a call, data structure, or multiline block.
                )
            # Comment: updates state or a field on the current object.
            self.policy = self.policy_variants[selected_variant]
        # Comment: evaluates a condition and chooses the branch to run.
        if self.policy is None:
            # Comment: raises an explicit error for the caller.
            raise ValueError(f"Skill '{self.name}' has no active policy config.")
        # Comment: closes a call, data structure, or multiline block.
        self._validate_policy(self.policy)

    # Comment: defines the function or method _validate_policy.
    def _validate_policy(self, policy: PreTrainedConfig) -> None:
        # Comment: executes this BT logic statement.
        """@brief Validate the active pretrained policy checkpoint reference."""
        # The active skill must reference a pretrained model path (either local
        # folder or a Hugging Face Hub id). This prevents accidental runtime
        # failures where a skill is declared but has no model to run.
        # Comment: assigns or prepares a value used by later statements.
        pretrained_path = policy.pretrained_path
        # Comment: evaluates a condition and chooses the branch to run.
        if pretrained_path is None:
            # Comment: raises an explicit error for the caller.
            raise ValueError(
                # Comment: executes this BT logic statement.
                f"Skill '{self.name}' requires a pretrained checkpoint. "
                # Comment: executes this BT logic statement.
                "Set skill.policy.pretrained_path to a local checkpoint or Hub model."
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: assigns or prepares a value used by later statements.
        pretrained_path_str = str(pretrained_path).strip()
        # Comment: evaluates a condition and chooses the branch to run.
        if not pretrained_path_str:
            # Comment: raises an explicit error for the caller.
            raise ValueError(
                # Comment: executes this BT logic statement.
                f"Skill '{self.name}' requires a non-empty pretrained checkpoint path."
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: evaluates a condition and chooses the branch to run.
        if pretrained_path_str.upper().startswith("TODO"):
            # Comment: raises an explicit error for the caller.
            raise ValueError(
                # Comment: executes this BT logic statement.
                f"Skill '{self.name}' still uses placeholder checkpoint "
                # Comment: executes this BT logic statement.
                f"{pretrained_path_str!r}. Replace it with a real local path or Hub model id."
            # Comment: closes a call, data structure, or multiline block.
            )


# Comment: applies a decorator to the following definition.
@dataclass
class SkillCommandServerConfig:
    # Comment: executes this BT logic statement.
    """Top-level configuration for the Python ROS2 skill command server.

    This root config is what `server.py` parses at startup. It contains the
    robot description, the list of learned skills, and server-level
    adapters/processors used during execution.
    """
    # Robot hardware configuration (CustomManipulatorConfig contains arm/gripper/cameras).
    # Comment: executes this BT logic statement.
    robot: CustomManipulatorConfig
    # List of learned skills available to the BT runtime.
    # Comment: closes a call, data structure, or multiline block.
    skills: list[PrimitiveSkillConfig]
    # Optional startup contract: every name here must exist in `skills`.
    # This catches a BT/executor mismatch before ROS2 starts accepting commands.
    # Comment: assigns or prepares a value used by later statements.
    expected_skill_names: list[str] = field(default_factory=list)
    # Camera names required by this execution profile. Empty means only "at
    # least one camera" is enforced.
    # Comment: assigns or prepares a value used by later statements.
    required_cameras: list[str] = field(default_factory=list)
    # ROS2 service name the server will advertise.
    # Comment: assigns or prepares a value used by later statements.
    bt_command_service: str = "/lerobot_bt/run"
    # ROS2 service name used by the BT runtime to query VLM check state.
    # Comment: assigns or prepares a value used by later statements.
    vlm_state_service: str = "/lerobot_bt/vlm_state"
    # Legacy ROS2 service name used to report success or failure.
    # Comment: assigns or prepares a value used by later statements.
    legacy_vlm_result_service: str = "/lerobot_bt/vlm_result_legacy"
    # Topic published whenever the BT is blocked on a scene verdict.
    # Comment: assigns or prepares a value used by later statements.
    vlm_request_topic: str = "/lerobot_bt/vlm_request"
    # Topic consumed from a manual tester or VLM to resolve the active scene verdict.
    # Comment: assigns or prepares a value used by later statements.
    vlm_result_topic: str = "/lerobot_bt/vlm_result"
    # Maximum seconds to wait for an external verifier SUCCESS after a command
    # opens a VLM check attempt. Zero disables automatic timeout-to-failure.
    # Comment: assigns or prepares a value used by later statements.
    vlm_timeout_s: float = 30.0
    # Control loop frequency in Hz used by the executor.
    # Comment: assigns or prepares a value used by later statements.
    fps: int = 10
    # Whether to publish/display diagnostic data for debugging.
    # Comment: assigns or prepares a value used by later statements.
    display_data: bool = True
    # Whether the server should play audible feedback sounds on events.
    # Comment: assigns or prepares a value used by later statements.
    play_sounds: bool = True
    # Attempt to reset the robot hardware when the server starts.
    # Comment: assigns or prepares a value used by later statements.
    reset_robot_on_startup: bool = True
    # Reset the robot immediately before every learned skill rollout, matching
    # the standalone custom_manipulator record/rollout entrypoint.
    # Comment: assigns or prepares a value used by later statements.
    reset_robot_before_skill: bool = True
    # Map of feature/key renames to align dataset keys with live robot keys.
    # Comment: assigns or prepares a value used by later statements.
    rename_map: dict[str, str] = field(default_factory=dict)
    # Processor pipeline applied to actions before they reach the robot.
    # Comment: assigns or prepares a value used by later statements.
    robot_action_processor: dict = field(default_factory=lambda: {"steps": []})
    # Processor pipeline applied to observations read from the robot.
    # Comment: assigns or prepares a value used by later statements.
    robot_observation_processor: dict = field(default_factory=lambda: {"steps": []})
    # Default variant selected from each skill.policy_variants. Individual
    # skills may override it with their own `policy_variant`, allowing one YAML
    # to mix ACT, SmolVLA, Diffusion, GROOT, XVLA, or any registered policy.
    # Comment: assigns or prepares a value used by later statements.
    policy_variant: str = "act"
    # Optional mapping from BT camera names to ROS2 CompressedImage topic names.
    # When set, the server publishes live camera frames on these topics so an
    # external VLM verifier can subscribe without opening the RealSense devices
    # directly (which would conflict with the BT server's own camera usage).
    # Example: {"wrist": "/panda/camera/wrist/image_compressed", "left": "/panda/camera/front/image_compressed"}
    # Comment: assigns or prepares a value used by later statements.
    camera_publish_map: dict[str, str] = field(default_factory=dict)
    # Frame rate (Hz) for the camera publishing thread. 0 disables publishing.
    # Comment: assigns or prepares a value used by later statements.
    camera_publish_fps: float = 10.0
    # JPEG quality (0-100) for published camera frames.
    # Comment: assigns or prepares a value used by later statements.
    camera_publish_jpeg_quality: int = 80
    # Human-readable task descriptions for VLM gates (AwaitScene nodes).
    # Gates have no policy config, so their `task` field would be empty.
    # This map lets you provide a VLM prompt per gate, e.g.:
    #   {"make_coffee.scene_0_ready": "Check if the coffee machine area is clear and ready."}
    # Comment: assigns or prepares a value used by later statements.
    vlm_gate_tasks: dict[str, str] = field(default_factory=dict)
    # Minimum seconds to wait before sending the first VLM request for a
    # human gate (AwaitScene). This gives the operator time to place or
    # adjust objects before the VLM starts checking the scene.
    # Comment: assigns or prepares a value used by later statements.
    vlm_gate_min_wait_s: float = 5.0

    # Comment: defines the function or method __post_init__.
    def __post_init__(self) -> None:
        # Comment: executes this BT logic statement.
        """@brief Validate top-level server invariants after config loading."""
        # Ensure at least one skill is configured to avoid running an empty server.
        # Comment: evaluates a condition and chooses the branch to run.
        if not self.skills:
            # Comment: raises an explicit error for the caller.
            raise ValueError("At least one skill must be configured.")
        # Comment: assigns or prepares a value used by later statements.
        skill_names = [skill.name for skill in self.skills]
        # Comment: assigns or prepares a value used by later statements.
        empty_skill_names = [index for index, name in enumerate(skill_names) if not name]
        # Comment: evaluates a condition and chooses the branch to run.
        if empty_skill_names:
            # Comment: raises an explicit error for the caller.
            raise ValueError(f"Skill entries at indexes {empty_skill_names} have empty names.")
        # Comment: assigns or prepares a value used by later statements.
        duplicate_skill_names = sorted(
            # Comment: executes this BT logic statement.
            name for name, count in Counter(skill_names).items() if count > 1
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: evaluates a condition and chooses the branch to run.
        if duplicate_skill_names:
            # Comment: raises an explicit error for the caller.
            raise ValueError(
                # Comment: executes this BT logic statement.
                "Duplicate skill names in server config: "
                # Comment: executes this BT logic statement.
                f"{duplicate_skill_names}. Every BT skill must map to one policy entry."
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: assigns or prepares a value used by later statements.
        duplicate_expected_names = sorted(
            # Comment: executes this BT logic statement.
            name for name, count in Counter(self.expected_skill_names).items() if count > 1
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: evaluates a condition and chooses the branch to run.
        if duplicate_expected_names:
            # Comment: raises an explicit error for the caller.
            raise ValueError(f"Duplicate expected_skill_names entries: {duplicate_expected_names}.")
        # Comment: evaluates a condition and chooses the branch to run.
        if not self.policy_variant:
            # Comment: raises an explicit error for the caller.
            raise ValueError("policy_variant must not be empty.")
        # Comment: iterates over the elements of the selected sequence.
        for skill in self.skills:
            # Comment: closes a call, data structure, or multiline block.
            skill.select_policy_variant(self.policy_variant)
        # Comment: assigns or prepares a value used by later statements.
        missing_expected_skills = sorted(set(self.expected_skill_names) - set(skill_names))
        # Comment: evaluates a condition and chooses the branch to run.
        if missing_expected_skills:
            # Comment: raises an explicit error for the caller.
            raise ValueError(
                # Comment: executes this BT logic statement.
                "The executor config is missing BT-required skill entries: "
                # Comment: executes this BT logic statement.
                f"{missing_expected_skills}."
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: assigns or prepares a value used by later statements.
        cameras = getattr(self.robot, "cameras", None) or {}
        # Comment: evaluates a condition and chooses the branch to run.
        if not cameras:
            # Comment: raises an explicit error for the caller.
            raise ValueError("At least one robot camera must be configured.")
        # Comment: assigns or prepares a value used by later statements.
        duplicate_required_cameras = sorted(
            # Comment: executes this BT logic statement.
            name for name, count in Counter(self.required_cameras).items() if count > 1
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: evaluates a condition and chooses the branch to run.
        if duplicate_required_cameras:
            # Comment: raises an explicit error for the caller.
            raise ValueError(f"Duplicate required_cameras entries: {duplicate_required_cameras}.")
        # Comment: assigns or prepares a value used by later statements.
        missing_cameras = sorted(set(self.required_cameras) - set(cameras))
        # Comment: evaluates a condition and chooses the branch to run.
        if missing_cameras:
            # Comment: raises an explicit error for the caller.
            raise ValueError(
                # Comment: executes this BT logic statement.
                "The robot config is missing required camera entries: "
                # Comment: executes this BT logic statement.
                f"{missing_cameras}. Available cameras: {sorted(cameras)}."
            # Comment: closes a call, data structure, or multiline block.
            )
        # Validate the frame rate is positive.
        # Comment: evaluates a condition and chooses the branch to run.
        if self.fps <= 0:
            # Comment: raises an explicit error for the caller.
            raise ValueError("fps must be > 0.")
        # Comment: evaluates a condition and chooses the branch to run.
        if not self.bt_command_service:
            # Comment: raises an explicit error for the caller.
            raise ValueError("bt_command_service must not be empty.")
        # Comment: evaluates a condition and chooses the branch to run.
        if not self.vlm_state_service:
            # Comment: raises an explicit error for the caller.
            raise ValueError("vlm_state_service must not be empty.")
        # Comment: evaluates a condition and chooses the branch to run.
        if not self.legacy_vlm_result_service:
            # Comment: raises an explicit error for the caller.
            raise ValueError("legacy_vlm_result_service must not be empty.")
        # Comment: evaluates a condition and chooses the branch to run.
        if not self.vlm_request_topic:
            # Comment: raises an explicit error for the caller.
            raise ValueError("vlm_request_topic must not be empty.")
        # Comment: evaluates a condition and chooses the branch to run.
        if not self.vlm_result_topic:
            # Comment: raises an explicit error for the caller.
            raise ValueError("vlm_result_topic must not be empty.")
        # Comment: evaluates a condition and chooses the branch to run.
        if self.vlm_timeout_s < 0:
            # Comment: raises an explicit error for the caller.
            raise ValueError("vlm_timeout_s must be >= 0.")
