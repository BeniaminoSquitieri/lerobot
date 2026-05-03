"""Deterministic recovery actions executed between BT attempts.

Flow role:
1. A learned primitive fails.
2. The BT calls a named recovery instead of retrying blindly.
3. This module executes small scripted motions that change the context before
   the next ACT attempt starts.
"""

from __future__ import annotations

import time

import numpy as np
from scipy.spatial.transform import Rotation as R

from lerobot.utils.robot_utils import precise_sleep

from .config import RecoveryConfig, RecoveryStepConfig


def _current_robot_state(robot: "CustomManipulator") -> tuple[np.ndarray, np.ndarray, float]:
    # Reads the minimum robot state needed to build recovery commands.
    obs = robot.get_observation()
    position = np.array([obs["position.x"], obs["position.y"], obs["position.z"]], dtype=float)
    rotation = np.array([obs["orientation.x"], obs["orientation.y"], obs["orientation.z"]], dtype=float)
    gripper = float(obs.get("gripper", 0.0))
    return position, rotation, gripper


def _set_gripper(robot: "CustomManipulator", gripper_value: float) -> None:
    # Supports both dict-based and scalar-based gripper driver APIs.
    try:
        robot.gripper_interface.apply_commands({"gripper": float(gripper_value)})
    except TypeError:
        robot.gripper_interface.apply_commands(float(gripper_value))


def _run_cartesian_delta(
    robot: "CustomManipulator",
    step_cfg: RecoveryStepConfig,
    fps: int,
    timeout_override_s: float,
) -> None:
    # Runs a short scripted Cartesian motion.
    # If the arm is configured for delta actions, we send per-step deltas.
    # Otherwise we interpolate toward an absolute target pose.
    duration_s = timeout_override_s if timeout_override_s > 0 else step_cfg.duration_s
    steps = max(1, int(round(duration_s * fps)))
    start_pos, start_rotvec, current_gripper = _current_robot_state(robot)

    total_translation = np.array([step_cfg.dx, step_cfg.dy, step_cfg.dz], dtype=float)
    total_rotvec = np.array([step_cfg.droll, step_cfg.dpitch, step_cfg.dyaw], dtype=float)

    target_gripper = current_gripper if step_cfg.gripper_value is None else float(step_cfg.gripper_value)
    target_dt_s = 1.0 / fps

    if robot.config.arm.use_delta_actions:
        per_step_translation = total_translation / steps
        per_step_rotvec = total_rotvec / steps
        for _ in range(steps):
            loop_t = time.perf_counter()
            robot.send_action(
                {
                    "position.x": float(per_step_translation[0]),
                    "position.y": float(per_step_translation[1]),
                    "position.z": float(per_step_translation[2]),
                    "orientation.x": float(per_step_rotvec[0]),
                    "orientation.y": float(per_step_rotvec[1]),
                    "orientation.z": float(per_step_rotvec[2]),
                    "gripper": target_gripper,
                }
            )
            precise_sleep(target_dt_s - (time.perf_counter() - loop_t))
        return

    start_rotation = R.from_rotvec(start_rotvec)
    for step_idx in range(1, steps + 1):
        loop_t = time.perf_counter()
        alpha = step_idx / steps
        target_pos = start_pos + alpha * total_translation
        target_rot = (R.from_rotvec(alpha * total_rotvec) * start_rotation).as_rotvec()
        robot.send_action(
            {
                "position.x": float(target_pos[0]),
                "position.y": float(target_pos[1]),
                "position.z": float(target_pos[2]),
                "orientation.x": float(target_rot[0]),
                "orientation.y": float(target_rot[1]),
                "orientation.z": float(target_rot[2]),
                "gripper": target_gripper,
            }
        )
        precise_sleep(target_dt_s - (time.perf_counter() - loop_t))


def execute_recovery(
    robot: "CustomManipulator",
    recovery_cfg: RecoveryConfig,
    fps: int,
    timeout_override_s: float = 0.0,
) -> None:
    # Entry point called by the Python server when the BT asks for a recovery.
    for step in recovery_cfg.steps:
        if step.kind == "pause":
            duration_s = timeout_override_s if timeout_override_s > 0 else step.duration_s
            time.sleep(duration_s)
            continue

        if step.kind == "robot_reset":
            robot.reset()
            continue

        if step.kind == "set_gripper":
            _set_gripper(robot, step.gripper_value)
            duration_s = timeout_override_s if timeout_override_s > 0 else step.duration_s
            if duration_s > 0:
                time.sleep(duration_s)
            continue

        if step.kind == "cartesian_delta":
            _run_cartesian_delta(robot, step, fps=fps, timeout_override_s=timeout_override_s)
            continue

        raise ValueError(f"Unsupported recovery step '{step.kind}'.")
