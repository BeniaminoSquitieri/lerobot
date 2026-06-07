"""Schema for real-robot executor YAML files consumed by server.py.

This module belongs to the execution side of the real robot runtime path. It
defines the dataclass contract for task executor YAMLs that configure service
names, skill entries, cameras, processors, timeouts, and robot backends before
the ROS2 skill server starts. Main input is one *_executor.yaml file; main
output is a validated SkillCommandServerConfig tree. Do not change this schema
casually, because server.py and robot-day configs depend on it staying aligned.
"""

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lerobot.configs.policies import PreTrainedConfig

# Import known policy families so `draccus` can deserialize them when the YAML
# contains a `policy` entry. These imports are intentionally here to register
# the subclasses; they are not referenced directly in code below.
from lerobot.policies.act.configuration_act import ACTConfig  # noqa: F401
from lerobot.policies.diffusion.configuration_diffusion import DiffusionConfig  # noqa: F401
from lerobot.policies.groot.configuration_groot import GrootConfig  # noqa: F401
from lerobot.policies.multi_task_dit.configuration_multi_task_dit import MultiTaskDiTConfig  # noqa: F401
from lerobot.policies.pi0.configuration_pi0 import PI0Config  # noqa: F401
from lerobot.policies.pi0_fast.configuration_pi0_fast import PI0FastConfig  # noqa: F401
from lerobot.policies.pi05.configuration_pi05 import PI05Config  # noqa: F401
from lerobot.policies.sac.configuration_sac import SACConfig  # noqa: F401
from lerobot.policies.sac.reward_model.configuration_classifier import RewardClassifierConfig  # noqa: F401
from lerobot.policies.sarm.configuration_sarm import SARMConfig  # noqa: F401
from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig  # noqa: F401
from lerobot.policies.tdmpc.configuration_tdmpc import TDMPCConfig  # noqa: F401
from lerobot.policies.vqbet.configuration_vqbet import VQBeTConfig  # noqa: F401
from lerobot.policies.wall_x.configuration_wall_x import WallXConfig  # noqa: F401
from lerobot.policies.xvla.configuration_xvla import XVLAConfig  # noqa: F401
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

    # Termination mode for rollout completion.
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
            raise ValueError(
                f"Unsupported transition mode '{self.mode}'. Expected one of {sorted(allowed_modes)}."
            )
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
    # Active policy config selected from `policy_variants`, or the legacy direct
    # policy config used by older YAML files.
    policy: PreTrainedConfig | None = None
    # Optional named policies for the same BT skill, e.g. "act", "smolvla",
    # "diffusion", or any other registered LeRobot policy type.
    policy_variants: dict[str, PreTrainedConfig] = field(default_factory=dict)
    # Optional per-skill override. When unset, the top-level/default
    # policy_variant is used.
    policy_variant: str | None = None
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
        if self.policy is None and not self.policy_variants:
            raise ValueError(f"Skill '{self.name}' requires either policy or policy_variants.")
        if self.policy is not None and not self.policy_variants:
            self._validate_policy(self.policy)

    def select_policy_variant(self, variant_name: str) -> None:
        """@brief Select and validate the policy variant used for this skill."""
        selected_variant = self.policy_variant or variant_name
        if self.policy_variants:
            if selected_variant not in self.policy_variants:
                available = sorted(self.policy_variants)
                raise ValueError(
                    f"Skill '{self.name}' has no policy variant {selected_variant!r}. "
                    f"Available variants: {available}."
                )
            self.policy = self.policy_variants[selected_variant]
        if self.policy is None:
            raise ValueError(f"Skill '{self.name}' has no active policy config.")
        self._validate_policy(self.policy)

    def _validate_policy(self, policy: PreTrainedConfig) -> None:
        """@brief Validate the active pretrained policy checkpoint reference."""
        # The active skill must reference a pretrained model path (either local
        # folder or a Hugging Face Hub id). This prevents accidental runtime
        # failures where a skill is declared but has no model to run.
        pretrained_path = policy.pretrained_path
        if pretrained_path is None:
            raise ValueError(
                f"Skill '{self.name}' requires a pretrained checkpoint. "
                "Set skill.policy.pretrained_path to a local checkpoint or Hub model."
            )
        pretrained_path_str = str(pretrained_path).strip()
        if not pretrained_path_str:
            raise ValueError(f"Skill '{self.name}' requires a non-empty pretrained checkpoint path.")
        if pretrained_path_str.upper().startswith("TODO"):
            raise ValueError(
                f"Skill '{self.name}' still uses placeholder checkpoint "
                f"{pretrained_path_str!r}. Replace it with a real local path or Hub model id."
            )


@dataclass
class SpatialPriorGateConfig:
    """Configuration for the deterministic spatial-prior OOD gate.

    The gate consults a Gaussian prior fitted offline from a skill's training
    demonstrations to check whether the object the policy is about to manipulate
    is located where the policy was trained to handle it. It is independent of
    and complementary to the VLM semantic gate.

    Modes:
    - "off"     : the gate is fully inert (default; existing flow unchanged).
    - "shadow"  : the gate evaluates and logs the verdict but never blocks a
                  skill. Use this on the real robot to measure the observed-vs-
                  prior distance and calibrate the offset/threshold.
    - "enforce" : a FAIL verdict (object out-of-distribution) blocks the skill.
                  ABSTAIN never blocks.
    """

    # One of "off", "shadow", "enforce".
    mode: str = "off"
    # Directory holding <name>.json prior files. Relative paths resolve against
    # this package directory; absolute paths are used as-is.
    priors_dir: str = "perception/spatial_priors"
    # Map BT skill name -> prior JSON file (relative to priors_dir or absolute).
    # Skills not listed here are not gated.
    skill_priors: dict[str, str] = field(default_factory=dict)
    # Optional map BT skill name -> perception object name to query. When unset
    # for a skill, the prior's own `object` field is used.
    skill_objects: dict[str, str] = field(default_factory=dict)
    # Perception QueryObjectPose service used to read the live object pose.
    query_pose_service: str = "/perception/query_pose"
    # Reject cached perception poses older than this many seconds.
    query_max_age_s: float = 2.0
    # Whether to require a fresh (non-cached) perception pose.
    require_fresh_pose: bool = True
    # Seconds to wait for the perception service to be ready and to respond.
    query_timeout_s: float = 2.0

    def __post_init__(self) -> None:
        """@brief Validate the gate mode after YAML parsing."""
        allowed_modes = {"off", "shadow", "enforce"}
        if self.mode not in allowed_modes:
            raise ValueError(
                f"spatial_prior_gate.mode={self.mode!r} is invalid. Expected one of {sorted(allowed_modes)}."
            )
        if self.query_timeout_s <= 0:
            raise ValueError("spatial_prior_gate.query_timeout_s must be > 0.")


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
    # Optional startup contract: every name here must exist in `skills`.
    # This catches a BT/executor mismatch before ROS2 starts accepting commands.
    expected_skill_names: list[str] = field(default_factory=list)
    # Camera names required by this execution profile. Empty means only "at
    # least one camera" is enforced.
    required_cameras: list[str] = field(default_factory=list)
    # ROS2 service name the server will advertise.
    bt_command_service: str = "/lerobot_bt/run"
    # ROS2 service name used by the BT runtime to query VLM check state.
    vlm_state_service: str = "/lerobot_bt/vlm_state"
    # DEPRECATED: legacy compatibility service path retained for current integrations.
    # Legacy ROS2 service name used to report success or failure.
    legacy_vlm_result_service: str = "/lerobot_bt/vlm_result_legacy"
    # Topic published whenever the BT is blocked on a scene verdict.
    vlm_request_topic: str = "/lerobot_bt/vlm_request"
    # Topic consumed from a manual tester or VLM to resolve the active scene verdict.
    vlm_result_topic: str = "/lerobot_bt/vlm_result"
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
    reset_robot_before_skill: bool = True
    # Map of feature/key renames to align dataset keys with live robot keys.
    rename_map: dict[str, str] = field(default_factory=dict)
    # Processor pipeline applied to actions before they reach the robot.
    robot_action_processor: dict = field(default_factory=lambda: {"steps": []})
    # Processor pipeline applied to observations read from the robot.
    robot_observation_processor: dict = field(default_factory=lambda: {"steps": []})
    # Default variant selected from each skill.policy_variants. Individual
    # skills may override it with their own `policy_variant`, allowing one YAML
    # to mix ACT, SmolVLA, Diffusion, GROOT, XVLA, or any registered policy.
    policy_variant: str = "act"
    # Optional mapping from BT camera names to ROS2 CompressedImage topic names.
    # When set, the server publishes live camera frames on these topics so an
    # external VLM verifier can subscribe without opening the RealSense devices
    # directly (which would conflict with the BT server's own camera usage).
    # Example: {"wrist": "/panda/camera/wrist/image_compressed", "left": "/panda/camera/front/image_compressed"}
    camera_publish_map: dict[str, str] = field(default_factory=dict)
    # Optional depth topics for the same cameras. Depth is published as
    # sensor_msgs/Image with lossless 16UC1 millimeter data when available.
    camera_depth_publish_map: dict[str, str] = field(default_factory=dict)
    # Optional CameraInfo topics for the color/depth-aligned stream.
    camera_info_publish_map: dict[str, str] = field(default_factory=dict)
    # Optional ROS frame_id override per BT camera name.
    camera_frame_id_map: dict[str, str] = field(default_factory=dict)
    # Optional static transforms per BT camera name. Each entry supports:
    # parent_frame_id, child_frame_id, translation [x,y,z], rotation_xyzw [x,y,z,w].
    camera_static_tf_map: dict[str, dict] = field(default_factory=dict)
    # Frame rate (Hz) for the camera publishing thread. 0 disables publishing.
    camera_publish_fps: float = 10.0
    # JPEG quality (0-100) for published camera frames.
    camera_publish_jpeg_quality: int = 80
    # Human-readable task descriptions for VLM gates (AwaitScene nodes).
    # Gates have no policy config, so their `task` field would be empty.
    # This map lets you provide a VLM prompt per gate, e.g.:
    #   {"make_coffee.scene_0_ready": "Check if the coffee machine area is clear and ready."}
    vlm_gate_tasks: dict[str, str] = field(default_factory=dict)
    # BT leaf names whose verified SUCCESS means the whole BT has completed.
    # Entries may be VLM gates or robot skills, depending on the final leaf in
    # that task's tree. When empty, the server falls back to "*.task_complete".
    auto_shutdown_success_names: list[str] = field(default_factory=list)
    # Minimum seconds to wait before sending the first VLM request for a
    # human gate (AwaitScene). This gives the operator time to place or
    # adjust objects before the VLM starts checking the scene.
    vlm_gate_min_wait_s: float = 5.0
    # Re-check cadence for robot skills. 0.0 means the VLM should re-evaluate
    # the scene as fast as inference allows; human gates keep the verifier
    # default cadence unless they override it per request.
    skill_vlm_check_period_s: float = 0.0
    # Re-check cadence for human/VLM gates (AwaitScene). 0.0 means the VLM
    # should re-evaluate the scene as fast as inference allows, so a gate
    # unblocks the instant the operator finishes placing objects.
    gate_vlm_check_period_s: float = 0.0
    # If True, force re-download of policy checkpoints from HuggingFace Hub
    # on every server startup, bypassing the local cache. Set to True when
    # you've pushed updated model weights and need the latest version.
    force_download_policy: bool = True
    # Deterministic spatial-prior OOD gate. Defaults to "off" so existing
    # deployments are unaffected until explicitly enabled per executor YAML.
    spatial_prior_gate: SpatialPriorGateConfig = field(default_factory=SpatialPriorGateConfig)

    def __post_init__(self) -> None:
        """@brief Validate top-level server invariants after config loading."""
        # Ensure at least one skill is configured to avoid running an empty server.
        if not self.skills:
            raise ValueError("At least one skill must be configured.")
        skill_names = [skill.name for skill in self.skills]
        empty_skill_names = [index for index, name in enumerate(skill_names) if not name]
        if empty_skill_names:
            raise ValueError(f"Skill entries at indexes {empty_skill_names} have empty names.")
        duplicate_skill_names = sorted(name for name, count in Counter(skill_names).items() if count > 1)
        if duplicate_skill_names:
            raise ValueError(
                "Duplicate skill names in server config: "
                f"{duplicate_skill_names}. Every BT skill must map to one policy entry."
            )
        duplicate_expected_names = sorted(
            name for name, count in Counter(self.expected_skill_names).items() if count > 1
        )
        if duplicate_expected_names:
            raise ValueError(f"Duplicate expected_skill_names entries: {duplicate_expected_names}.")
        duplicate_shutdown_names = sorted(
            name for name, count in Counter(self.auto_shutdown_success_names).items() if count > 1
        )
        if duplicate_shutdown_names:
            raise ValueError(f"Duplicate auto_shutdown_success_names entries: {duplicate_shutdown_names}.")
        empty_shutdown_names = [
            index for index, name in enumerate(self.auto_shutdown_success_names) if not str(name).strip()
        ]
        if empty_shutdown_names:
            raise ValueError(
                f"auto_shutdown_success_names entries at indexes {empty_shutdown_names} are empty."
            )
        if not self.policy_variant:
            raise ValueError("policy_variant must not be empty.")
        for skill in self.skills:
            skill.select_policy_variant(self.policy_variant)
        missing_expected_skills = sorted(set(self.expected_skill_names) - set(skill_names))
        if missing_expected_skills:
            raise ValueError(
                f"The executor config is missing BT-required skill entries: {missing_expected_skills}."
            )
        cameras = getattr(self.robot, "cameras", None) or {}
        if not cameras:
            raise ValueError("At least one robot camera must be configured.")
        duplicate_required_cameras = sorted(
            name for name, count in Counter(self.required_cameras).items() if count > 1
        )
        if duplicate_required_cameras:
            raise ValueError(f"Duplicate required_cameras entries: {duplicate_required_cameras}.")
        missing_cameras = sorted(set(self.required_cameras) - set(cameras))
        if missing_cameras:
            raise ValueError(
                "The robot config is missing required camera entries: "
                f"{missing_cameras}. Available cameras: {sorted(cameras)}."
            )
        camera_map_fields: dict[str, dict[str, Any]] = {
            "camera_publish_map": self.camera_publish_map,
            "camera_depth_publish_map": self.camera_depth_publish_map,
            "camera_info_publish_map": self.camera_info_publish_map,
            "camera_frame_id_map": self.camera_frame_id_map,
            "camera_static_tf_map": self.camera_static_tf_map,
        }
        for field_name, mapping in camera_map_fields.items():
            unknown = sorted(set(mapping) - set(cameras))
            if unknown:
                raise ValueError(
                    f"{field_name} references unknown cameras {unknown}. "
                    f"Available cameras: {sorted(cameras)}."
                )
        depth_cameras = set(self.camera_depth_publish_map)
        info_cameras = set(self.camera_info_publish_map)
        if depth_cameras or info_cameras:
            if depth_cameras != info_cameras:
                raise ValueError(
                    "camera_depth_publish_map and camera_info_publish_map must cover the same cameras "
                    "for RGB-D perception."
                )
            missing_rgb_publishers = sorted(depth_cameras - set(self.camera_publish_map))
            if missing_rgb_publishers:
                raise ValueError(
                    "RGB-D camera entries must also be present in camera_publish_map: "
                    f"{missing_rgb_publishers}."
                )
            depth_disabled = sorted(
                name for name in depth_cameras if not bool(getattr(cameras[name], "use_depth", False))
            )
            if depth_disabled:
                raise ValueError(f"Depth publishing requires use_depth=true for cameras: {depth_disabled}.")
        for camera_name, tf_config in self.camera_static_tf_map.items():
            translation = tf_config.get("translation", [])
            rotation = tf_config.get("rotation_xyzw", [])
            if len(translation) != 3:
                raise ValueError(
                    f"camera_static_tf_map[{camera_name!r}].translation must have exactly 3 values."
                )
            if len(rotation) != 4:
                raise ValueError(
                    f"camera_static_tf_map[{camera_name!r}].rotation_xyzw must have exactly 4 values."
                )
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
