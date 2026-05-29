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

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from lerobot.common.control_utils import predict_action
from lerobot.policies.utils import make_robot_action
from lerobot.processor import RobotProcessorPipeline
from lerobot.utils.constants import OBS_STR
from lerobot.utils.device_utils import get_safe_torch_device
from lerobot.utils.feature_utils import build_dataset_frame
from lerobot.utils.robot_utils import precise_sleep
from lerobot.utils.visualization_utils import log_rerun_data

from .conditions import evaluate_all, evaluate_any
from .config import SkillCommandServerConfig
from .skill_runtime_loader import LiveRobotDatasetMetadata, SkillRuntime, build_skill_runtime
from .verification import VLM_FAILURE, VLM_NEEDS_MANUAL_HELP, VLM_SUCCESS, VLM_WAIT_HUMAN

if TYPE_CHECKING:
    from lerobot.robots.custom_manipulator.custom_manipulator import CustomManipulator


__all__ = [
    "ActiveSkillVlmResult",
    "CommandResult",
    "LiveRobotDatasetMetadata",
    "SkillRunner",
    "SkillRuntime",
]


_ACTIVE_SKILL_STOP_STATUSES = {
    VLM_SUCCESS,
    VLM_FAILURE,
    VLM_WAIT_HUMAN,
    VLM_NEEDS_MANUAL_HELP,
}
"""VLM/manual statuses that should stop a live policy rollout immediately."""


@dataclass
class CommandResult:
    """@brief Normalized command result returned to the ROS2 server."""

    success: bool
    """True when the BT leaf should receive SUCCESS."""

    status: str
    """Machine-readable command status, usually SUCCESS, FAILURE, or ERROR."""

    elapsed_s: float
    """Command duration in seconds."""

    message: str
    """Human-readable operator/debug message."""

    vlm_status: str | None = None
    """Verifier status that ended the command, if a live VLM/manual result stopped it."""

    vlm_message: str = ""
    """Verifier message paired with `vlm_status`."""


@dataclass(frozen=True)
class ActiveSkillVlmResult:
    """@brief External verifier result accepted while a skill is still running."""

    status: str
    """VLM/manual status that should be applied to the post-skill attempt."""

    message: str
    """Human-readable verifier message."""


def _build_skill_runtime(*args, **kwargs) -> SkillRuntime:
    """@brief Backwards-compatible wrapper around `skill_runtime_loader.build_skill_runtime`."""
    return build_skill_runtime(*args, **kwargs)


class _ActiveSkillTracker:
    """@brief Owner of the live-stop state for the currently running skill.

    Centralizes the lock, the active skill name, and the optional external
    verifier verdict so the rollout loop and the ROS2 server share a single,
    serialized view of "is something running, and has the VLM stopped it?".
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._skill_name: str | None = None
        self._vlm_result: ActiveSkillVlmResult | None = None

    def begin(self, skill_name: str) -> None:
        """@brief Mark `skill_name` as the externally-stoppable active skill."""
        with self._lock:
            self._skill_name = skill_name
            self._vlm_result = None

    def clear(self, skill_name: str) -> None:
        """@brief Clear active state if it still belongs to `skill_name`."""
        with self._lock:
            if self._skill_name == skill_name:
                self._skill_name = None
                self._vlm_result = None

    def get(self, skill_name: str) -> ActiveSkillVlmResult | None:
        """@brief Return the live verifier verdict for `skill_name`, if any."""
        with self._lock:
            if self._skill_name != skill_name:
                return None
            return self._vlm_result

    def report(self, *, skill_name: str, status: str, message: str, attempt_id: int) -> bool:
        """@brief Try to register a live verifier verdict for the active skill.

        Only `attempt_id == 0` and statuses in `_ACTIVE_SKILL_STOP_STATUSES`
        can target a still-running skill; everything else falls through to the
        normal registry path.
        """
        if attempt_id != 0 or status not in _ACTIVE_SKILL_STOP_STATUSES:
            return False
        with self._lock:
            if self._skill_name != skill_name:
                return False
            if self._vlm_result is not None:
                return False
            self._vlm_result = ActiveSkillVlmResult(status=status, message=message)
            return True





class SkillRunner:
    """@brief Serialized executor for real learned skills.

    The executor owns the robot-side critical section. Every skill goes through
    `_command_lock`, because two BT leaves must never command the same
    Panda/Robotiq stack concurrently.
    """

    def __init__(self, cfg: SkillCommandServerConfig, robot: CustomManipulator) -> None:
        """@brief Index configured commands and keep the robot handle.

        @param cfg Server config containing skills, FPS, and flags.
        @param robot Connected or connectable `CustomManipulator` instance.
        """
        self.cfg = cfg
        self.robot = robot
        # Names are the bridge between the BT XML and the policy configs.
        self.skill_configs = {skill_cfg.name: skill_cfg for skill_cfg in cfg.skills}
        self.skills: dict[str, SkillRuntime] = {}
        # Only one command at a time should touch the real robot.
        self._command_lock = threading.Lock()
        self._active_skill_tracker = _ActiveSkillTracker()

    def report_active_vlm_result(
        self,
        *,
        skill_name: str,
        status: str,
        message: str = "",
        attempt_id: int = 0,
    ) -> bool:
        """@brief Stop the currently running skill from an external VLM/manual result.

        @details Post-skill VLM results normally apply to an already-open
        registry attempt. During real robot bring-up, operators may also need
        to say "this skill is done now" while the policy is still rolling out.
        In that case there is no attempt id yet, so only `attempt_id=0` can
        target the active command.
        """
        return self._active_skill_tracker.report(
            skill_name=skill_name,
            status=status,
            message=message,
            attempt_id=attempt_id,
        )

    def _begin_active_skill(self, skill_name: str) -> None:
        """@brief Mark a skill as externally stoppable."""
        self._active_skill_tracker.begin(skill_name)

    def _clear_active_skill(self, skill_name: str) -> None:
        """@brief Clear active skill state after the rollout returns."""
        self._active_skill_tracker.clear(skill_name)

    def _get_active_vlm_result(self, skill_name: str) -> ActiveSkillVlmResult | None:
        """@brief Return the live verifier result for this skill, if one arrived."""
        return self._active_skill_tracker.get(skill_name)

    def _command_result_from_active_vlm(
        self,
        *,
        skill_name: str,
        elapsed_s: float,
        vlm_result: ActiveSkillVlmResult,
    ) -> CommandResult:
        """@brief Convert a live VLM/manual stop into a BT command result."""
        message = (
            f"Skill '{skill_name}' stopped after {elapsed_s:.2f}s by external VLM status "
            f"{vlm_result.status}."
        )
        if vlm_result.message:
            message = f"{message} {vlm_result.message}"
        logging.info(message)
        return CommandResult(
            True,
            "SUCCESS",
            elapsed_s,
            message,
            vlm_status=vlm_result.status,
            vlm_message=vlm_result.message,
        )

    def _get_skill_runtime(
        self,
        skill_name: str,
        robot_action_processor: RobotProcessorPipeline,
        robot_observation_processor: RobotProcessorPipeline,
    ) -> SkillRuntime:
        """@brief Return the loaded runtime for a skill, loading it on first use.

        @param skill_name Name requested by the BT XML.
        @param robot_action_processor Action processor used to build live features.
        @param robot_observation_processor Observation processor used to build live features.
        @return Cached `SkillRuntime` for `skill_name`.
        """
        if skill_name not in self.skills:
            self.skills[skill_name] = build_skill_runtime(
                self.skill_configs[skill_name],
                self.cfg.rename_map,
                self.robot,
                robot_action_processor,
                robot_observation_processor,
                force_download=self.cfg.force_download_policy,
            )
        return self.skills[skill_name]

    def execute_skill(
        self,
        skill_name: str,
        robot_action_processor: RobotProcessorPipeline,
        robot_observation_processor: RobotProcessorPipeline,
        timeout_override_s: float = 0.0,
    ) -> CommandResult:
        """@brief Execute one learned primitive requested by the BT.

        @param skill_name Runtime skill name from the BT leaf.
        @param robot_action_processor Converts policy actions to robot commands.
        @param robot_observation_processor Converts robot observations to policy inputs.
        @param timeout_override_s Optional BT-side timeout override.
        @return Normalized command result for the ROS2 response.
        """
        if skill_name not in self.skill_configs:
            return CommandResult(False, "ERROR", 0.0, f"Unknown skill '{skill_name}'.")

        with self._command_lock:
            start_t = time.perf_counter()
            try:
                skill = self._get_skill_runtime(
                    skill_name,
                    robot_action_processor,
                    robot_observation_processor,
                )
                if self.cfg.reset_robot_before_skill:
                    # Match custom_manipulator/record.py: load runtime first,
                    # then bring the robot home immediately before rollout.
                    logging.info("Resetting robot before skill '%s'.", skill_name)
                    self.robot.reset()
                    logging.info("Robot reset before skill '%s' complete.", skill_name)

                skill.reset()
                robot_action_processor.reset()
                robot_observation_processor.reset()
                if skill.cfg.settle_time_s > 0:
                    # Give robot/camera state time to settle before inference starts.
                    time.sleep(skill.cfg.settle_time_s)

                start_t = time.perf_counter()
                self._begin_active_skill(skill_name)
                target_dt_s = 1 / self.cfg.fps
                timeout_s = (
                    None
                    if skill.cfg.transition.mode == "until_success"
                    else timeout_override_s if timeout_override_s > 0 else skill.cfg.transition.max_duration_s
                )

                step_idx = 0
                while True:
                    loop_t = time.perf_counter()
                    active_vlm_result = self._get_active_vlm_result(skill_name)
                    if active_vlm_result is not None:
                        elapsed_s = time.perf_counter() - start_t
                        return self._command_result_from_active_vlm(
                            skill_name=skill_name,
                            elapsed_s=elapsed_s,
                            vlm_result=active_vlm_result,
                        )

                    # Live rollout: read observation -> evaluate status -> maybe predict action.
                    obs = self.robot.get_observation()
                    obs_processed = robot_observation_processor(obs)

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

                    active_vlm_result = self._get_active_vlm_result(skill_name)
                    if active_vlm_result is not None:
                        elapsed_s = time.perf_counter() - start_t
                        return self._command_result_from_active_vlm(
                            skill_name=skill_name,
                            elapsed_s=elapsed_s,
                            vlm_result=active_vlm_result,
                        )

                    self._run_skill_step(skill, obs, obs_processed, robot_action_processor, step_idx=step_idx)
                    step_idx += 1

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
            finally:
                self._clear_active_skill(skill_name)

    def _skill_status(
        self,
        skill: SkillRuntime,
        obs_processed: dict,
        elapsed_s: float,
        timeout_s: float | None,
    ) -> str:
        """@brief Evaluate whether the current skill rollout should stop.

        @param skill Runtime bundle whose transition config defines semantics.
        @param obs_processed Processed observation dictionary.
        @param elapsed_s Seconds since the command started.
        @param timeout_s Effective timeout, or `None` for `until_success`.
        @return `RUNNING`, `SUCCESS`, or `FAILURE`.
        """
        transition = skill.cfg.transition

        if evaluate_any(transition.failure_conditions, obs_processed):
            return "FAILURE"

        if transition.mode == "timeout":
            return "SUCCESS" if elapsed_s >= timeout_s else "RUNNING"

        if elapsed_s >= transition.min_duration_s and evaluate_all(
            transition.success_conditions,
            obs_processed,
        ):
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
        *,
        step_idx: int,
    ) -> None:
        """@brief Run one policy inference step and send the resulting action.

        @param skill Runtime bundle for the active primitive.
        @param obs Raw robot observation used for robot-action conversion.
        @param obs_processed Processed observation used for policy inference.
        @param robot_action_processor Pipeline that prepares robot commands.
        @param step_idx Zero-based control step index for debug logging.
        """
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
        if self.cfg.display_data:
            try:
                from lerobot.robots.custom_manipulator.policy_rollout_viewer import log_policy_rollout

                log_policy_rollout(
                    action_values,
                    list(skill.policy._action_queue),
                    skill.ds_meta.features,
                    skill.postprocessor,
                )
            except Exception as exc:  # noqa: BLE001
                logging.debug("Policy rollout visualization skipped: %s", exc)
        selected_action = make_robot_action(action_values, skill.ds_meta.features)
        robot_action_to_send = robot_action_processor((selected_action, obs))
        if step_idx < 5:
            current_pos = [float(obs[f"position.{axis}"]) for axis in "xyz"]
            target_pos = [float(selected_action[f"position.{axis}"]) for axis in "xyz"]
            current_ori = [float(obs[f"orientation.{axis}"]) for axis in "xyz"]
            target_ori = [float(selected_action[f"orientation.{axis}"]) for axis in "xyz"]
            logging.info(
                "Skill '%s' action debug #%d: current_pos=%s target_pos=%s current_ori=%s "
                "target_ori=%s gripper=%.4f",
                skill.cfg.name,
                step_idx + 1,
                [round(v, 4) for v in current_pos],
                [round(v, 4) for v in target_pos],
                [round(v, 4) for v in current_ori],
                [round(v, 4) for v in target_ori],
                float(selected_action.get("gripper", 0.0)),
            )
        sent_action = self.robot.send_action(robot_action_to_send)
        if self.cfg.display_data:
            log_rerun_data(observation=obs_processed, action=selected_action)
        return sent_action
