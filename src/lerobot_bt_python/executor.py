# Comment: executes this BT logic statement.
"""@file executor.py
@brief Execution backend for learned BT skills.

@details
This module is the only layer that turns a BT command name into real robot work.
It loads policy runtimes lazily, keeps the control loop serialized with a lock,
and returns compact command results to the ROS2 server.

Flow role:
1. The Python ROS2 server receives a named command from the BT.
2. This backend resolves the name to a configured skill.
3. It runs the selected policy inference loop on the real robot.
4. It returns SUCCESS/FAILURE/ERROR back to the server.
"""

# Comment: imports dependencies or symbols required by the module.
from __future__ import annotations

# Comment: imports dependencies or symbols required by the module.
import logging
# Comment: imports dependencies or symbols required by the module.
import threading
# Comment: imports dependencies or symbols required by the module.
import time
# Comment: imports dependencies or symbols required by the module.
from dataclasses import dataclass
# Comment: imports dependencies or symbols required by the module.
from pathlib import Path
# Comment: imports dependencies or symbols required by the module.
from typing import TYPE_CHECKING, Any

# Comment: imports dependencies or symbols required by the module.
from huggingface_hub import snapshot_download

# Comment: imports dependencies or symbols required by the module.
from lerobot.common.control_utils import predict_action
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.factory import make_policy, make_pre_post_processors
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.pretrained import PreTrainedPolicy
# Comment: imports dependencies or symbols required by the module.
from lerobot.policies.utils import make_robot_action
# Comment: imports dependencies or symbols required by the module.
from lerobot.processor import PolicyAction, PolicyProcessorPipeline, RobotProcessorPipeline
# Comment: imports dependencies or symbols required by the module.
from lerobot.processor.rename_processor import rename_stats
# Comment: imports dependencies or symbols required by the module.
from lerobot.utils.constants import OBS_STR
# Comment: imports dependencies or symbols required by the module.
from lerobot.utils.device_utils import get_safe_torch_device
# Comment: imports dependencies or symbols required by the module.
from lerobot.utils.feature_utils import build_dataset_frame, combine_feature_dicts
# Comment: imports dependencies or symbols required by the module.
from lerobot.utils.robot_utils import precise_sleep
# Comment: imports dependencies or symbols required by the module.
from lerobot.utils.visualization_utils import log_rerun_data

# Comment: imports dependencies or symbols required by the module.
from .conditions import evaluate_all, evaluate_any
# Comment: imports dependencies or symbols required by the module.
from .config import PrimitiveSkillConfig, SkillCommandServerConfig
# Comment: imports dependencies or symbols required by the module.
from .verification import VLM_FAILURE, VLM_NEEDS_MANUAL_HELP, VLM_SUCCESS, VLM_WAIT_HUMAN

# Comment: evaluates a condition and chooses the branch to run.
if TYPE_CHECKING:
    # Comment: imports dependencies or symbols required by the module.
    from lerobot.robots.custom_manipulator.custom_manipulator import CustomManipulator


# Comment: assigns or prepares a value used by later statements.
_ACTIVE_SKILL_STOP_STATUSES = {
    # Comment: executes this BT logic statement.
    VLM_SUCCESS,
    # Comment: executes this BT logic statement.
    VLM_FAILURE,
    # Comment: executes this BT logic statement.
    VLM_WAIT_HUMAN,
    # Comment: executes this BT logic statement.
    VLM_NEEDS_MANUAL_HELP,
# Comment: closes a call, data structure, or multiline block.
}
# Comment: executes this BT logic statement.
"""VLM/manual statuses that should stop a live policy rollout immediately."""


# Comment: applies a decorator to the following definition.
@dataclass
class SkillRuntime:
    # Comment: executes this BT logic statement.
    """@brief Runtime bundle for one configured learned primitive.

    The bundle is cached per skill name so repeated BT retries do not reload the
    checkpoint. `reset()` still clears policy and processor state before every
    execution attempt.
    """

    # Comment: executes this BT logic statement.
    cfg: PrimitiveSkillConfig
    # Comment: executes this BT logic statement.
    """Skill YAML entry that owns names, policy config, task text, and transitions."""

    # Comment: executes this BT logic statement.
    ds_meta: Any
    # Comment: executes this BT logic statement.
    """Dataset metadata or live robot metadata used to build policy features."""

    # Comment: executes this BT logic statement.
    policy: PreTrainedPolicy
    # Comment: executes this BT logic statement.
    """Loaded LeRobot policy object used for inference."""

    # Comment: closes a call, data structure, or multiline block.
    preprocessor: PolicyProcessorPipeline[dict, dict]
    # Comment: executes this BT logic statement.
    """Policy observation preprocessor applied before inference."""

    # Comment: closes a call, data structure, or multiline block.
    postprocessor: PolicyProcessorPipeline[PolicyAction, PolicyAction]
    # Comment: executes this BT logic statement.
    """Policy action postprocessor applied after inference."""

    # Comment: defines the function or method reset.
    def reset(self) -> None:
        # Comment: executes this BT logic statement.
        """@brief Reset stateful policy/preprocessor/postprocessor queues."""
        # Comment: closes a call, data structure, or multiline block.
        self.policy.reset()
        # Comment: closes a call, data structure, or multiline block.
        self.preprocessor.reset()
        # Comment: closes a call, data structure, or multiline block.
        self.postprocessor.reset()


# Comment: applies a decorator to the following definition.
@dataclass
class LiveRobotDatasetMetadata:
    # Comment: executes this BT logic statement.
    """@brief Minimal metadata object for live robot rollouts.

    `make_policy` expects dataset-like metadata. When `metadata_source="robot"`,
    this small object provides the required attributes without creating a
    `LeRobotDataset` on disk.
    """

    # Comment: executes this BT logic statement.
    repo_id: str
    # Comment: executes this BT logic statement.
    """Logical dataset repository id used by policy loading code."""

    # Comment: closes a call, data structure, or multiline block.
    features: dict[str, dict]
    # Comment: executes this BT logic statement.
    """Feature schema assembled from robot action and observation pipelines."""

    # Comment: assigns or prepares a value used by later statements.
    stats: dict | None = None
    # Comment: executes this BT logic statement.
    """Optional dataset statistics; live metadata leaves this absent by default."""


# Comment: applies a decorator to the following definition.
@dataclass
class CommandResult:
    # Comment: executes this BT logic statement.
    """@brief Normalized command result returned to the ROS2 server."""

    # Comment: executes this BT logic statement.
    success: bool
    # Comment: executes this BT logic statement.
    """True when the BT leaf should receive SUCCESS."""

    # Comment: executes this BT logic statement.
    status: str
    # Comment: executes this BT logic statement.
    """Machine-readable command status, usually SUCCESS, FAILURE, or ERROR."""

    # Comment: executes this BT logic statement.
    elapsed_s: float
    # Comment: executes this BT logic statement.
    """Command duration in seconds."""

    # Comment: executes this BT logic statement.
    message: str
    # Comment: executes this BT logic statement.
    """Human-readable operator/debug message."""

    # Comment: assigns or prepares a value used by later statements.
    vlm_status: str | None = None
    # Comment: executes this BT logic statement.
    """Verifier status that ended the command, if a live VLM/manual result stopped it."""

    # Comment: assigns or prepares a value used by later statements.
    vlm_message: str = ""
    # Comment: executes this BT logic statement.
    """Verifier message paired with `vlm_status`."""


# Comment: applies a decorator to the following definition.
@dataclass(frozen=True)
class ActiveSkillVlmResult:
    # Comment: executes this BT logic statement.
    """@brief External verifier result accepted while a skill is still running."""

    # Comment: executes this BT logic statement.
    status: str
    # Comment: executes this BT logic statement.
    """VLM/manual status that should be applied to the post-skill attempt."""

    # Comment: executes this BT logic statement.
    message: str
    # Comment: executes this BT logic statement.
    """Human-readable verifier message."""


# Comment: defines the function or method _build_skill_runtime.
def _build_skill_runtime(
    # Comment: executes this BT logic statement.
    skill_cfg: PrimitiveSkillConfig,
    # Comment: executes this BT logic statement.
    rename_map: dict[str, str],
    # Comment: executes this BT logic statement.
    robot: CustomManipulator,
    # Comment: executes this BT logic statement.
    robot_action_processor: RobotProcessorPipeline,
    # Comment: executes this BT logic statement.
    robot_observation_processor: RobotProcessorPipeline,
    # Comment: assigns or prepares a value used by later statements.
    force_download: bool = False,
# Comment: executes this BT logic statement.
) -> SkillRuntime:
    # Comment: executes this BT logic statement.
    """@brief Create the cached runtime bundle for one skill.

    @param skill_cfg YAML config for the primitive.
    @param rename_map Feature-name mapping between dataset and live robot.
    @param robot Robot instance used to infer live feature schemas when needed.
    @param robot_action_processor Runtime action processor pipeline.
    @param robot_observation_processor Runtime observation processor pipeline.
    @param force_download If True, force re-download from HuggingFace Hub.
    @return A fully loaded `SkillRuntime`.

    This is where a skill name becomes dataset metadata, a policy checkpoint, and
    processor pipelines that can run inside the control loop.
    """
    # Comment: evaluates a condition and chooses the branch to run.
    if skill_cfg.policy is None:
        # Comment: raises an explicit error for the caller.
        raise ValueError(f"Skill '{skill_cfg.name}' has no active policy selected.")

    # Force re-download policy checkpoint from HuggingFace Hub before loading,
    # so updated model weights are picked up even if a cached copy exists.
    if force_download and skill_cfg.policy.pretrained_path:
        pretrained_path_str = str(skill_cfg.policy.pretrained_path)
        if not Path(pretrained_path_str).is_dir():
            logging.info(
                "Force-downloading policy '%s' from HuggingFace Hub (force_download=True).",
                pretrained_path_str,
            )
            try:
                snapshot_download(
                    repo_id=pretrained_path_str,
                    force_download=True,
                    resume_download=True,
                )
            except Exception as exc:
                logging.warning(
                    "Force-download of '%s' failed (%s). Falling back to cached copy.",
                    pretrained_path_str, exc,
                )

    # Comment: evaluates a condition and chooses the branch to run.
    if skill_cfg.metadata_source == "robot":
        # Comment: imports dependencies or symbols required by the module.
        from lerobot.datasets.pipeline_features import (
            # Comment: executes this BT logic statement.
            aggregate_pipeline_dataset_features,
            # Comment: executes this BT logic statement.
            create_initial_features,
        # Comment: closes a call, data structure, or multiline block.
        )

        # Comment: assigns or prepares a value used by later statements.
        features = combine_feature_dicts(
            # Comment: executes this BT logic statement.
            aggregate_pipeline_dataset_features(
                # Comment: assigns or prepares a value used by later statements.
                pipeline=robot_action_processor,
                # Comment: assigns or prepares a value used by later statements.
                initial_features=create_initial_features(action=robot.action_features),
                # Comment: assigns or prepares a value used by later statements.
                use_videos=True,
            # Comment: executes this BT logic statement.
            ),
            # Comment: executes this BT logic statement.
            aggregate_pipeline_dataset_features(
                # Comment: assigns or prepares a value used by later statements.
                pipeline=robot_observation_processor,
                # Comment: assigns or prepares a value used by later statements.
                initial_features=create_initial_features(observation=robot.observation_features),
                # Comment: assigns or prepares a value used by later statements.
                use_videos=True,
            # Comment: executes this BT logic statement.
            ),
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: assigns or prepares a value used by later statements.
        ds_meta = LiveRobotDatasetMetadata(repo_id=skill_cfg.dataset_repo_id, features=features)
        # Comment: executes this BT logic statement.
        logging.info(
            # Comment: assigns or prepares a value used by later statements.
            "Skill '%s' using live robot rollout metadata with features=%s.",
            # Comment: executes this BT logic statement.
            skill_cfg.name,
            # Comment: executes this BT logic statement.
            sorted(features),
        # Comment: closes a call, data structure, or multiline block.
        )
    # Comment: handles the fallback branch when previous conditions do not match.
    else:
        # Comment: imports dependencies or symbols required by the module.
        from lerobot.datasets.lerobot_dataset import LeRobotDatasetMetadata

        # Comment: assigns or prepares a value used by later statements.
        ds_meta = LeRobotDatasetMetadata(
            # Comment: executes this BT logic statement.
            skill_cfg.dataset_repo_id,
            # Comment: assigns or prepares a value used by later statements.
            root=skill_cfg.dataset_root,
            # Comment: assigns or prepares a value used by later statements.
            revision=skill_cfg.dataset_revision,
        # Comment: closes a call, data structure, or multiline block.
        )

    # Comment: assigns or prepares a value used by later statements.
    policy = make_policy(skill_cfg.policy, ds_meta=ds_meta, rename_map=rename_map)
    # Comment: assigns or prepares a value used by later statements.
    preprocessor, postprocessor = make_pre_post_processors(
        # Comment: assigns or prepares a value used by later statements.
        policy_cfg=skill_cfg.policy,
        # Comment: assigns or prepares a value used by later statements.
        pretrained_path=skill_cfg.policy.pretrained_path,
        # Comment: assigns or prepares a value used by later statements.
        dataset_stats=rename_stats(ds_meta.stats, rename_map),
        # Comment: assigns or prepares a value used by later statements.
        preprocessor_overrides={
            # Comment: executes this BT logic statement.
            "device_processor": {"device": skill_cfg.policy.device},
            # Comment: executes this BT logic statement.
            "rename_observations_processor": {"rename_map": rename_map},
        # Comment: executes this BT logic statement.
        },
    # Comment: closes a call, data structure, or multiline block.
    )
    # Comment: returns the computed value to the caller.
    return SkillRuntime(
        # Comment: assigns or prepares a value used by later statements.
        cfg=skill_cfg,
        # Comment: assigns or prepares a value used by later statements.
        ds_meta=ds_meta,
        # Comment: assigns or prepares a value used by later statements.
        policy=policy,
        # Comment: assigns or prepares a value used by later statements.
        preprocessor=preprocessor,
        # Comment: assigns or prepares a value used by later statements.
        postprocessor=postprocessor,
    # Comment: closes a call, data structure, or multiline block.
    )


# Comment: declares the class SkillCommandExecutor.
class SkillCommandExecutor:
    # Comment: executes this BT logic statement.
    """@brief Serialized executor for real learned skills.

    The executor owns the robot-side critical section. Every skill goes through
    `_command_lock`, because two BT leaves must never command the same
    Panda/Robotiq stack concurrently.
    """

    # Comment: defines the function or method __init__.
    def __init__(self, cfg: SkillCommandServerConfig, robot: CustomManipulator) -> None:
        # Comment: executes this BT logic statement.
        """@brief Index configured commands and keep the robot handle.

        @param cfg Server config containing skills, FPS, and flags.
        @param robot Connected or connectable `CustomManipulator` instance.
        """
        # Comment: updates state or a field on the current object.
        self.cfg = cfg
        # Comment: updates state or a field on the current object.
        self.robot = robot
        # Names are the bridge between the BT XML and the policy configs.
        # Comment: updates state or a field on the current object.
        self.skill_configs = {skill_cfg.name: skill_cfg for skill_cfg in cfg.skills}
        # Comment: updates state or a field on the current object.
        self.skills: dict[str, SkillRuntime] = {}
        # Only one command at a time should touch the real robot.
        # Comment: updates state or a field on the current object.
        self._command_lock = threading.Lock()
        # Comment: updates state or a field on the current object.
        self._active_lock = threading.Lock()
        # Comment: updates state or a field on the current object.
        self._active_skill_name: str | None = None
        # Comment: updates state or a field on the current object.
        self._active_vlm_result: ActiveSkillVlmResult | None = None

    # Comment: defines the function or method report_active_vlm_result.
    def report_active_vlm_result(
        # Comment: executes this BT logic statement.
        self,
        # Comment: executes this BT logic statement.
        *,
        # Comment: executes this BT logic statement.
        skill_name: str,
        # Comment: executes this BT logic statement.
        status: str,
        # Comment: assigns or prepares a value used by later statements.
        message: str = "",
        # Comment: assigns or prepares a value used by later statements.
        attempt_id: int = 0,
    # Comment: executes this BT logic statement.
    ) -> bool:
        # Comment: executes this BT logic statement.
        """@brief Stop the currently running skill from an external VLM/manual result.

        @details Post-skill VLM results normally apply to an already-open
        registry attempt. During real robot bring-up, operators may also need
        to say "this skill is done now" while the policy is still rolling out.
        In that case there is no attempt id yet, so only `attempt_id=0` can
        target the active command.
        """
        # Comment: evaluates a condition and chooses the branch to run.
        if attempt_id != 0 or status not in _ACTIVE_SKILL_STOP_STATUSES:
            # Comment: returns the computed value to the caller.
            return False

        # Comment: opens a managed context and guarantees its cleanup.
        with self._active_lock:
            # Comment: evaluates a condition and chooses the branch to run.
            if self._active_skill_name != skill_name:
                # Comment: returns the computed value to the caller.
                return False
            # Comment: evaluates a condition and chooses the branch to run.
            if self._active_vlm_result is not None:
                # Comment: returns the computed value to the caller.
                return False
            # Comment: updates state or a field on the current object.
            self._active_vlm_result = ActiveSkillVlmResult(status=status, message=message)
            # Comment: returns the computed value to the caller.
            return True

    # Comment: defines the function or method _begin_active_skill.
    def _begin_active_skill(self, skill_name: str) -> None:
        # Comment: executes this BT logic statement.
        """@brief Mark a skill as externally stoppable."""
        # Comment: opens a managed context and guarantees its cleanup.
        with self._active_lock:
            # Comment: updates state or a field on the current object.
            self._active_skill_name = skill_name
            # Comment: updates state or a field on the current object.
            self._active_vlm_result = None

    # Comment: defines the function or method _clear_active_skill.
    def _clear_active_skill(self, skill_name: str) -> None:
        # Comment: executes this BT logic statement.
        """@brief Clear active skill state after the rollout returns."""
        # Comment: opens a managed context and guarantees its cleanup.
        with self._active_lock:
            # Comment: evaluates a condition and chooses the branch to run.
            if self._active_skill_name == skill_name:
                # Comment: updates state or a field on the current object.
                self._active_skill_name = None
                # Comment: updates state or a field on the current object.
                self._active_vlm_result = None

    # Comment: defines the function or method _get_active_vlm_result.
    def _get_active_vlm_result(self, skill_name: str) -> ActiveSkillVlmResult | None:
        # Comment: executes this BT logic statement.
        """@brief Return the live verifier result for this skill, if one arrived."""
        # Comment: opens a managed context and guarantees its cleanup.
        with self._active_lock:
            # Comment: evaluates a condition and chooses the branch to run.
            if self._active_skill_name != skill_name:
                # Comment: returns the computed value to the caller.
                return None
            # Comment: returns the computed value to the caller.
            return self._active_vlm_result

    # Comment: defines the function or method _command_result_from_active_vlm.
    def _command_result_from_active_vlm(
        # Comment: executes this BT logic statement.
        self,
        # Comment: executes this BT logic statement.
        *,
        # Comment: executes this BT logic statement.
        skill_name: str,
        # Comment: executes this BT logic statement.
        elapsed_s: float,
        # Comment: executes this BT logic statement.
        vlm_result: ActiveSkillVlmResult,
    # Comment: executes this BT logic statement.
    ) -> CommandResult:
        # Comment: executes this BT logic statement.
        """@brief Convert a live VLM/manual stop into a BT command result."""
        # Comment: assigns or prepares a value used by later statements.
        message = (
            # Comment: executes this BT logic statement.
            f"Skill '{skill_name}' stopped after {elapsed_s:.2f}s by external VLM status "
            # Comment: executes this BT logic statement.
            f"{vlm_result.status}."
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: evaluates a condition and chooses the branch to run.
        if vlm_result.message:
            # Comment: assigns or prepares a value used by later statements.
            message = f"{message} {vlm_result.message}"
        # Comment: closes a call, data structure, or multiline block.
        logging.info(message)
        # Comment: returns the computed value to the caller.
        return CommandResult(
            # Comment: executes this BT logic statement.
            True,
            # Comment: executes this BT logic statement.
            "SUCCESS",
            # Comment: executes this BT logic statement.
            elapsed_s,
            # Comment: executes this BT logic statement.
            message,
            # Comment: assigns or prepares a value used by later statements.
            vlm_status=vlm_result.status,
            # Comment: assigns or prepares a value used by later statements.
            vlm_message=vlm_result.message,
        # Comment: closes a call, data structure, or multiline block.
        )

    # Comment: defines the function or method _get_skill_runtime.
    def _get_skill_runtime(
        # Comment: executes this BT logic statement.
        self,
        # Comment: executes this BT logic statement.
        skill_name: str,
        # Comment: executes this BT logic statement.
        robot_action_processor: RobotProcessorPipeline,
        # Comment: executes this BT logic statement.
        robot_observation_processor: RobotProcessorPipeline,
    # Comment: executes this BT logic statement.
    ) -> SkillRuntime:
        # Comment: executes this BT logic statement.
        """@brief Return the loaded runtime for a skill, loading it on first use.

        @param skill_name Name requested by the BT XML.
        @param robot_action_processor Action processor used to build live features.
        @param robot_observation_processor Observation processor used to build live features.
        @return Cached `SkillRuntime` for `skill_name`.
        """
        # Comment: evaluates a condition and chooses the branch to run.
        if skill_name not in self.skills:
            # Comment: updates state or a field on the current object.
            self.skills[skill_name] = _build_skill_runtime(
                # Comment: executes this BT logic statement.
                self.skill_configs[skill_name],
                # Comment: executes this BT logic statement.
                self.cfg.rename_map,
                # Comment: executes this BT logic statement.
                self.robot,
                # Comment: executes this BT logic statement.
                robot_action_processor,
                # Comment: executes this BT logic statement.
                robot_observation_processor,
                # Comment: assigns or prepares a value used by later statements.
                force_download=self.cfg.force_download_policy,
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: returns the computed value to the caller.
        return self.skills[skill_name]

    # Comment: defines the function or method execute_skill.
    def execute_skill(
        # Comment: executes this BT logic statement.
        self,
        # Comment: executes this BT logic statement.
        skill_name: str,
        # Comment: executes this BT logic statement.
        robot_action_processor: RobotProcessorPipeline,
        # Comment: executes this BT logic statement.
        robot_observation_processor: RobotProcessorPipeline,
        # Comment: assigns or prepares a value used by later statements.
        timeout_override_s: float = 0.0,
    # Comment: executes this BT logic statement.
    ) -> CommandResult:
        # Comment: executes this BT logic statement.
        """@brief Execute one learned primitive requested by the BT.

        @param skill_name Runtime skill name from the BT leaf.
        @param robot_action_processor Converts policy actions to robot commands.
        @param robot_observation_processor Converts robot observations to policy inputs.
        @param timeout_override_s Optional BT-side timeout override.
        @return Normalized command result for the ROS2 response.
        """
        # Comment: evaluates a condition and chooses the branch to run.
        if skill_name not in self.skill_configs:
            # Comment: returns the computed value to the caller.
            return CommandResult(False, "ERROR", 0.0, f"Unknown skill '{skill_name}'.")

        # Comment: opens a managed context and guarantees its cleanup.
        with self._command_lock:
            # Comment: assigns or prepares a value used by later statements.
            start_t = time.perf_counter()
            # Comment: opens a protected block to catch possible errors.
            try:
                # Comment: assigns or prepares a value used by later statements.
                skill = self._get_skill_runtime(
                    # Comment: executes this BT logic statement.
                    skill_name,
                    # Comment: executes this BT logic statement.
                    robot_action_processor,
                    # Comment: executes this BT logic statement.
                    robot_observation_processor,
                # Comment: closes a call, data structure, or multiline block.
                )
                # Comment: evaluates a condition and chooses the branch to run.
                if self.cfg.reset_robot_before_skill:
                    # Match custom_manipulator/record.py: load runtime first,
                    # then bring the robot home immediately before rollout.
                    # Comment: closes a call, data structure, or multiline block.
                    logging.info("Resetting robot before skill '%s'.", skill_name)
                    # Comment: closes a call, data structure, or multiline block.
                    self.robot.reset()
                    # Comment: closes a call, data structure, or multiline block.
                    logging.info("Robot reset before skill '%s' complete.", skill_name)

                # Comment: closes a call, data structure, or multiline block.
                skill.reset()
                # Comment: closes a call, data structure, or multiline block.
                robot_action_processor.reset()
                # Comment: closes a call, data structure, or multiline block.
                robot_observation_processor.reset()
                # Comment: evaluates a condition and chooses the branch to run.
                if skill.cfg.settle_time_s > 0:
                    # Give robot/camera state time to settle before inference starts.
                    # Comment: closes a call, data structure, or multiline block.
                    time.sleep(skill.cfg.settle_time_s)

                # Comment: assigns or prepares a value used by later statements.
                start_t = time.perf_counter()
                # Comment: closes a call, data structure, or multiline block.
                self._begin_active_skill(skill_name)
                # Comment: assigns or prepares a value used by later statements.
                target_dt_s = 1 / self.cfg.fps
                # Comment: assigns or prepares a value used by later statements.
                timeout_s = (
                    # Comment: executes this BT logic statement.
                    None
                    # Comment: evaluates a condition and chooses the branch to run.
                    if skill.cfg.transition.mode == "until_success"
                    # Comment: handles the fallback branch when previous conditions do not match.
                    else timeout_override_s if timeout_override_s > 0 else skill.cfg.transition.max_duration_s
                # Comment: closes a call, data structure, or multiline block.
                )

                # Comment: assigns or prepares a value used by later statements.
                step_idx = 0
                # Comment: repeats the block while the condition remains true.
                while True:
                    # Comment: assigns or prepares a value used by later statements.
                    loop_t = time.perf_counter()
                    # Comment: assigns or prepares a value used by later statements.
                    active_vlm_result = self._get_active_vlm_result(skill_name)
                    # Comment: evaluates a condition and chooses the branch to run.
                    if active_vlm_result is not None:
                        # Comment: assigns or prepares a value used by later statements.
                        elapsed_s = time.perf_counter() - start_t
                        # Comment: returns the computed value to the caller.
                        return self._command_result_from_active_vlm(
                            # Comment: assigns or prepares a value used by later statements.
                            skill_name=skill_name,
                            # Comment: assigns or prepares a value used by later statements.
                            elapsed_s=elapsed_s,
                            # Comment: assigns or prepares a value used by later statements.
                            vlm_result=active_vlm_result,
                        # Comment: closes a call, data structure, or multiline block.
                        )

                    # Live rollout: read observation -> evaluate status -> maybe predict action.
                    # Comment: assigns or prepares a value used by later statements.
                    obs = self.robot.get_observation()
                    # Comment: assigns or prepares a value used by later statements.
                    obs_processed = robot_observation_processor(obs)

                    # Comment: assigns or prepares a value used by later statements.
                    elapsed_s = time.perf_counter() - start_t
                    # Comment: assigns or prepares a value used by later statements.
                    status = self._skill_status(skill, obs_processed, elapsed_s, timeout_s)
                    # Comment: evaluates a condition and chooses the branch to run.
                    if status == "SUCCESS":
                        # Comment: assigns or prepares a value used by later statements.
                        message = f"Skill '{skill_name}' completed in {elapsed_s:.2f}s."
                        # Comment: closes a call, data structure, or multiline block.
                        logging.info(message)
                        # Comment: returns the computed value to the caller.
                        return CommandResult(True, status, elapsed_s, message)
                    # Comment: evaluates a condition and chooses the branch to run.
                    if status == "FAILURE":
                        # Comment: assigns or prepares a value used by later statements.
                        message = f"Skill '{skill_name}' failed after {elapsed_s:.2f}s."
                        # Comment: closes a call, data structure, or multiline block.
                        logging.error(message)
                        # Comment: returns the computed value to the caller.
                        return CommandResult(False, status, elapsed_s, message)

                    # Comment: assigns or prepares a value used by later statements.
                    active_vlm_result = self._get_active_vlm_result(skill_name)
                    # Comment: evaluates a condition and chooses the branch to run.
                    if active_vlm_result is not None:
                        # Comment: assigns or prepares a value used by later statements.
                        elapsed_s = time.perf_counter() - start_t
                        # Comment: returns the computed value to the caller.
                        return self._command_result_from_active_vlm(
                            # Comment: assigns or prepares a value used by later statements.
                            skill_name=skill_name,
                            # Comment: assigns or prepares a value used by later statements.
                            elapsed_s=elapsed_s,
                            # Comment: assigns or prepares a value used by later statements.
                            vlm_result=active_vlm_result,
                        # Comment: closes a call, data structure, or multiline block.
                        )

                    # Comment: updates state or a field on the current object.
                    self._run_skill_step(skill, obs, obs_processed, robot_action_processor, step_idx=step_idx)
                    # Comment: assigns or prepares a value used by later statements.
                    step_idx += 1

                    # Comment: assigns or prepares a value used by later statements.
                    dt_s = time.perf_counter() - loop_t
                    # Comment: evaluates a condition and chooses the branch to run.
                    if dt_s > target_dt_s:
                        # Comment: executes this BT logic statement.
                        logging.warning(
                            # Comment: executes this BT logic statement.
                            "Control frequency dropped below target: %.1f Hz (actual) vs %d Hz (target). "
                            # Comment: executes this BT logic statement.
                            "Loop took %.1fms vs target %.1fms.",
                            # Comment: executes this BT logic statement.
                            1 / dt_s,
                            # Comment: executes this BT logic statement.
                            self.cfg.fps,
                            # Comment: executes this BT logic statement.
                            dt_s * 1000,
                            # Comment: executes this BT logic statement.
                            target_dt_s * 1000,
                        # Comment: closes a call, data structure, or multiline block.
                        )
                    # Comment: closes a call, data structure, or multiline block.
                    precise_sleep(target_dt_s - dt_s)
            # Comment: handles a specific exception raised by the protected block.
            except Exception as exc:  # noqa: BLE001
                # Comment: assigns or prepares a value used by later statements.
                elapsed_s = time.perf_counter() - start_t
                # Comment: assigns or prepares a value used by later statements.
                message = f"Skill '{skill_name}' crashed with error: {exc}"
                # Comment: closes a call, data structure, or multiline block.
                logging.exception(message)
                # Comment: returns the computed value to the caller.
                return CommandResult(False, "ERROR", elapsed_s, message)
            # Comment: always runs the final cleanup for the protected block.
            finally:
                # Comment: closes a call, data structure, or multiline block.
                self._clear_active_skill(skill_name)

    # Comment: defines the function or method _skill_status.
    def _skill_status(
        # Comment: executes this BT logic statement.
        self,
        # Comment: executes this BT logic statement.
        skill: SkillRuntime,
        # Comment: executes this BT logic statement.
        obs_processed: dict,
        # Comment: executes this BT logic statement.
        elapsed_s: float,
        # Comment: executes this BT logic statement.
        timeout_s: float | None,
    # Comment: executes this BT logic statement.
    ) -> str:
        # Comment: executes this BT logic statement.
        """@brief Evaluate whether the current skill rollout should stop.

        @param skill Runtime bundle whose transition config defines semantics.
        @param obs_processed Processed observation dictionary.
        @param elapsed_s Seconds since the command started.
        @param timeout_s Effective timeout, or `None` for `until_success`.
        @return `RUNNING`, `SUCCESS`, or `FAILURE`.
        """
        # Comment: assigns or prepares a value used by later statements.
        transition = skill.cfg.transition

        # Comment: evaluates a condition and chooses the branch to run.
        if evaluate_any(transition.failure_conditions, obs_processed):
            # Comment: returns the computed value to the caller.
            return "FAILURE"

        # Comment: evaluates a condition and chooses the branch to run.
        if transition.mode == "timeout":
            # Comment: returns the computed value to the caller.
            return "SUCCESS" if elapsed_s >= timeout_s else "RUNNING"

        # Comment: evaluates a condition and chooses the branch to run.
        if elapsed_s >= transition.min_duration_s and evaluate_all(
            # Comment: executes this BT logic statement.
            transition.success_conditions,
            # Comment: executes this BT logic statement.
            obs_processed,
        # Comment: executes this BT logic statement.
        ):
            # Comment: returns the computed value to the caller.
            return "SUCCESS"

        # Comment: evaluates a condition and chooses the branch to run.
        if transition.mode == "until_success":
            # Comment: returns the computed value to the caller.
            return "RUNNING"

        # Comment: checks an invariant that must remain true.
        assert timeout_s is not None
        # Comment: evaluates a condition and chooses the branch to run.
        if elapsed_s >= timeout_s:
            # Comment: returns the computed value to the caller.
            return "SUCCESS" if transition.mode == "all_conditions_or_timeout" else "FAILURE"

        # Comment: returns the computed value to the caller.
        return "RUNNING"

    # Comment: defines the function or method _run_skill_step.
    def _run_skill_step(
        # Comment: executes this BT logic statement.
        self,
        # Comment: executes this BT logic statement.
        skill: SkillRuntime,
        # Comment: executes this BT logic statement.
        obs: dict,
        # Comment: executes this BT logic statement.
        obs_processed: dict,
        # Comment: executes this BT logic statement.
        robot_action_processor: RobotProcessorPipeline,
        # Comment: executes this BT logic statement.
        *,
        # Comment: executes this BT logic statement.
        step_idx: int,
    # Comment: executes this BT logic statement.
    ) -> None:
        # Comment: executes this BT logic statement.
        """@brief Run one policy inference step and send the resulting action.

        @param skill Runtime bundle for the active primitive.
        @param obs Raw robot observation used for robot-action conversion.
        @param obs_processed Processed observation used for policy inference.
        @param robot_action_processor Pipeline that prepares robot commands.
        @param step_idx Zero-based control step index for debug logging.
        """
        # Comment: assigns or prepares a value used by later statements.
        observation_frame = build_dataset_frame(skill.ds_meta.features, obs_processed, prefix=OBS_STR)
        # Comment: assigns or prepares a value used by later statements.
        action_values = predict_action(
            # Comment: assigns or prepares a value used by later statements.
            observation=observation_frame,
            # Comment: assigns or prepares a value used by later statements.
            policy=skill.policy,
            # Comment: assigns or prepares a value used by later statements.
            device=get_safe_torch_device(skill.policy.config.device),
            # Comment: assigns or prepares a value used by later statements.
            preprocessor=skill.preprocessor,
            # Comment: assigns or prepares a value used by later statements.
            postprocessor=skill.postprocessor,
            # Comment: assigns or prepares a value used by later statements.
            use_amp=skill.policy.config.use_amp,
            # Comment: assigns or prepares a value used by later statements.
            task=skill.cfg.task,
            # Comment: assigns or prepares a value used by later statements.
            robot_type=self.robot.robot_type,
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: evaluates a condition and chooses the branch to run.
        if self.cfg.display_data:
            # Comment: opens a protected block to catch possible errors.
            try:
                # Comment: imports dependencies or symbols required by the module.
                from lerobot.robots.custom_manipulator.policy_rollout_viewer import log_policy_rollout

                # Comment: executes this BT logic statement.
                log_policy_rollout(
                    # Comment: executes this BT logic statement.
                    action_values,
                    # Comment: executes this BT logic statement.
                    list(skill.policy._action_queue),
                    # Comment: executes this BT logic statement.
                    skill.ds_meta.features,
                    # Comment: executes this BT logic statement.
                    skill.postprocessor,
                # Comment: closes a call, data structure, or multiline block.
                )
            # Comment: handles a specific exception raised by the protected block.
            except Exception as exc:  # noqa: BLE001
                # Comment: closes a call, data structure, or multiline block.
                logging.debug("Policy rollout visualization skipped: %s", exc)
        # Comment: assigns or prepares a value used by later statements.
        selected_action = make_robot_action(action_values, skill.ds_meta.features)
        # Comment: assigns or prepares a value used by later statements.
        robot_action_to_send = robot_action_processor((selected_action, obs))
        # Comment: evaluates a condition and chooses the branch to run.
        if step_idx < 5:
            # Comment: assigns or prepares a value used by later statements.
            current_pos = [float(obs[f"position.{axis}"]) for axis in "xyz"]
            # Comment: assigns or prepares a value used by later statements.
            target_pos = [float(selected_action[f"position.{axis}"]) for axis in "xyz"]
            # Comment: assigns or prepares a value used by later statements.
            current_ori = [float(obs[f"orientation.{axis}"]) for axis in "xyz"]
            # Comment: assigns or prepares a value used by later statements.
            target_ori = [float(selected_action[f"orientation.{axis}"]) for axis in "xyz"]
            # Comment: executes this BT logic statement.
            logging.info(
                # Comment: assigns or prepares a value used by later statements.
                "Skill '%s' action debug #%d: current_pos=%s target_pos=%s current_ori=%s "
                # Comment: assigns or prepares a value used by later statements.
                "target_ori=%s gripper=%.4f",
                # Comment: executes this BT logic statement.
                skill.cfg.name,
                # Comment: executes this BT logic statement.
                step_idx + 1,
                # Comment: executes this BT logic statement.
                [round(v, 4) for v in current_pos],
                # Comment: executes this BT logic statement.
                [round(v, 4) for v in target_pos],
                # Comment: executes this BT logic statement.
                [round(v, 4) for v in current_ori],
                # Comment: executes this BT logic statement.
                [round(v, 4) for v in target_ori],
                # Comment: executes this BT logic statement.
                float(selected_action.get("gripper", 0.0)),
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: assigns or prepares a value used by later statements.
        sent_action = self.robot.send_action(robot_action_to_send)
        # Comment: evaluates a condition and chooses the branch to run.
        if self.cfg.display_data:
            # Comment: assigns or prepares a value used by later statements.
            log_rerun_data(observation=obs_processed, action=selected_action)
        # Comment: returns the computed value to the caller.
        return sent_action
