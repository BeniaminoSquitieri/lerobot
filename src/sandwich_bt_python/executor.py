"""Execution backend for learned skills and scripted recoveries."""

from __future__ import annotations

"""Execution backend for learned skills and scripted recoveries.

Flow role:
1. The Python ROS2 server receives a named command from the BT.
2. This backend resolves the name to a configured skill or recovery.
3. If it is a skill, it runs the ACT inference loop on the real robot.
4. If it is a recovery, it executes a deterministic scripted sequence.
5. It returns SUCCESS/FAILURE/ERROR back to the server.
"""

import logging
import threading
import time
from dataclasses import dataclass

from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.policies.pretrained import PreTrainedPolicy
from lerobot.policies.utils import make_robot_action
from lerobot.processor import PolicyAction, PolicyProcessorPipeline, RobotProcessorPipeline
from lerobot.processor.rename_processor import rename_stats
from lerobot.common.control_utils import predict_action
from lerobot.utils.device_utils import get_safe_torch_device
from lerobot.utils.feature_utils import build_dataset_frame
from lerobot.utils.constants import OBS_STR
from lerobot.utils.robot_utils import precise_sleep
from lerobot.utils.visualization_utils import log_rerun_data

from .conditions import evaluate_all, evaluate_any
from .config import PrimitiveSkillConfig, RecoveryConfig, SkillCommandServerConfig
from .recoveries import execute_recovery


@dataclass
class SkillRuntime:
    # Runtime bundle for one learned primitive:
    # config + dataset metadata + policy + processors.
    cfg: PrimitiveSkillConfig
    ds_meta: "LeRobotDatasetMetadata"
    policy: PreTrainedPolicy
    preprocessor: PolicyProcessorPipeline[dict, dict]
    postprocessor: PolicyProcessorPipeline[PolicyAction, PolicyAction]

    def reset(self) -> None:
        self.policy.reset()
        self.preprocessor.reset()
        self.postprocessor.reset()


@dataclass
class CommandResult:
    success: bool
    status: str
    elapsed_s: float
    message: str


def _build_skill_runtime(
    skill_cfg: PrimitiveSkillConfig,
    rename_map: dict[str, str],
) -> SkillRuntime:
    # Prepares everything needed to execute one named skill at runtime.
    # This is where a skill name becomes:
    # dataset metadata + policy checkpoint + processors.
    from lerobot.datasets.lerobot_dataset import LeRobotDatasetMetadata
    
    ds_meta = LeRobotDatasetMetadata(
        skill_cfg.dataset_repo_id,
        root=skill_cfg.dataset_root,
        revision=skill_cfg.dataset_revision,
    )
    policy = make_policy(skill_cfg.policy, ds_meta=ds_meta, rename_map=rename_map)
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=skill_cfg.policy,
        pretrained_path=skill_cfg.policy.pretrained_path,
        dataset_stats=rename_stats(ds_meta.stats, rename_map),
        preprocessor_overrides={
            "device_processor": {"device": skill_cfg.policy.device},
            "rename_observations_processor": {"rename_map": rename_map},
        },
    )
    return SkillRuntime(
        cfg=skill_cfg,
        ds_meta=ds_meta,
        policy=policy,
        preprocessor=preprocessor,
        postprocessor=postprocessor,
    )


class SkillCommandExecutor:
    def __init__(self, cfg: SkillCommandServerConfig, robot: "CustomManipulator") -> None:
        self.cfg = cfg
        self.robot = robot
        # Names are the bridge between the BT XML and the policy configs.
        self.skill_configs = {skill_cfg.name: skill_cfg for skill_cfg in cfg.skills}
        self.skills: dict[str, SkillRuntime] = {}
        self.recoveries = {recovery.name: recovery for recovery in cfg.recoveries}
        # Only one command at a time should touch the real robot.
        self._command_lock = threading.Lock()

    def _get_skill_runtime(self, skill_name: str) -> SkillRuntime:
        if skill_name not in self.skills:
            self.skills[skill_name] = _build_skill_runtime(self.skill_configs[skill_name], self.cfg.rename_map)
        return self.skills[skill_name]

    def execute_skill(
        self,
        skill_name: str,
        robot_action_processor: RobotProcessorPipeline,
        robot_observation_processor: RobotProcessorPipeline,
        timeout_override_s: float = 0.0,
    ) -> CommandResult:
        # Called when the BT asks to run one learned primitive.
        if skill_name not in self.skill_configs:
            return CommandResult(False, "ERROR", 0.0, f"Unknown skill '{skill_name}'.")

        with self._command_lock:
            start_t = time.perf_counter()
            try:
                skill = self._get_skill_runtime(skill_name)
                skill.reset()
                if skill.cfg.settle_time_s > 0:
                    time.sleep(skill.cfg.settle_time_s)

                target_dt_s = 1 / self.cfg.fps
                timeout_s = (
                    None
                    if skill.cfg.transition.mode == "until_success"
                    else timeout_override_s if timeout_override_s > 0 else skill.cfg.transition.max_duration_s
                )

                while True:
                    loop_t = time.perf_counter()
                    # Live rollout: read observation -> evaluate status -> maybe predict action.
                    obs = self.robot.get_observation()
                    obs_processed = robot_observation_processor(obs)

                    if self.cfg.display_data:
                        log_rerun_data(observation=obs_processed, action=None)

                    elapsed_s = time.perf_counter() - start_t
                    status = self._skill_status(skill, obs_processed, elapsed_s, timeout_s)
                    if status == "SUCCESS":
                        message = f"Skill '{skill_name}' completed in {elapsed_s:.2f}s."
                        logging.info(message)
                        return CommandResult(True, status, elapsed_s, message)
                    if status == "FAILURE":
                        message = f"Skill '{skill_name}' failed after {elapsed_s:.2f}s."
                        logging.error(message)
                        return CommandResult(False, status, elapsed_s, message)

                    self._run_skill_step(skill, obs, obs_processed, robot_action_processor)

                    dt_s = time.perf_counter() - loop_t
                    if dt_s > target_dt_s:
                        logging.warning(
                            "Control frequency dropped below target: %.1f Hz (actual) vs %d Hz (target). "
                            "Loop took %.1fms vs target %.1fms.",
                            1 / dt_s,
                            self.cfg.fps,
                            dt_s * 1000,
                            target_dt_s * 1000,
                        )
                    precise_sleep(target_dt_s - dt_s)
            except Exception as exc:  # noqa: BLE001
                elapsed_s = time.perf_counter() - start_t
                message = f"Skill '{skill_name}' crashed with error: {exc}"
                logging.exception(message)
                return CommandResult(False, "ERROR", elapsed_s, message)

    def execute_named_recovery(self, recovery_name: str, timeout_override_s: float = 0.0) -> CommandResult:
        # Called when the BT asks to run one named recovery instead of a learned skill.
        if recovery_name not in self.recoveries:
            return CommandResult(False, "ERROR", 0.0, f"Unknown recovery '{recovery_name}'.")

        with self._command_lock:
            recovery_cfg = self.recoveries[recovery_name]
            start_t = time.perf_counter()
            try:
                execute_recovery(
                    robot=self.robot,
                    recovery_cfg=recovery_cfg,
                    fps=self.cfg.fps,
                    timeout_override_s=timeout_override_s,
                )
            except Exception as exc:  # noqa: BLE001
                elapsed_s = time.perf_counter() - start_t
                message = f"Recovery '{recovery_name}' failed with error: {exc}"
                logging.exception(message)
                return CommandResult(False, "ERROR", elapsed_s, message)

            elapsed_s = time.perf_counter() - start_t
            message = f"Recovery '{recovery_name}' completed in {elapsed_s:.2f}s."
            logging.info(message)
            return CommandResult(True, "SUCCESS", elapsed_s, message)

    def _skill_status(
        self,
        skill: SkillRuntime,
        obs_processed: dict,
        elapsed_s: float,
        timeout_s: float | None,
    ) -> str:
        # Decides whether the current rollout is still running or should terminate.
        transition = skill.cfg.transition

        if evaluate_any(transition.failure_conditions, obs_processed):
            return "FAILURE"

        if transition.mode == "timeout":
            return "SUCCESS" if elapsed_s >= timeout_s else "RUNNING"

        if elapsed_s >= transition.min_duration_s and evaluate_all(transition.success_conditions, obs_processed):
            return "SUCCESS"

        if transition.mode == "until_success":
            return "RUNNING"

        assert timeout_s is not None
        if elapsed_s >= timeout_s:
            return "SUCCESS" if transition.mode == "all_conditions_or_timeout" else "FAILURE"

        return "RUNNING"

    def _run_skill_step(
        self,
        skill: SkillRuntime,
        obs: dict,
        obs_processed: dict,
        robot_action_processor: RobotProcessorPipeline,
    ) -> None:
        # One control step of the learned primitive:
        # processed observation -> ACT prediction -> robot action -> send to robot.
        observation_frame = build_dataset_frame(skill.ds_meta.features, obs_processed, prefix=OBS_STR)
        action_values = predict_action(
            observation=observation_frame,
            policy=skill.policy,
            device=get_safe_torch_device(skill.policy.config.device),
            preprocessor=skill.preprocessor,
            postprocessor=skill.postprocessor,
            use_amp=skill.policy.config.use_amp,
            task=skill.cfg.task,
            robot_type=self.robot.robot_type,
        )
        selected_action = make_robot_action(action_values, skill.ds_meta.features)
        robot_action_to_send = robot_action_processor((selected_action, obs))
        self.robot.send_action(robot_action_to_send)
