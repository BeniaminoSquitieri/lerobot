#!/usr/bin/env python

"""@file service_probe.py
@brief Probe the live sandwich supervisor ROS2 services."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

import rclpy

from .collaborative_runner import (
    DEFAULT_CONFIG_PATH,
    CollaborativeRunnerExitCode,
    SupervisorRos2Client,
    SupervisorServiceUnavailableError,
    load_supervisor_config,
)
from .ros_services import GeneratedInterfaceError
from .scene_state import SandwichSceneObservation


def main(argv: list[str] | None = None) -> int:
    """@brief CLI entry point for a one-shot supervisor service probe."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-path",
        default=None,
        help="Optional path to the supervisor YAML config. Defaults to the package config.",
    )
    parser.add_argument(
        "--goal",
        default="make_sandwich",
        help="Goal string to send to /sandwich_supervisor/next_action.",
    )
    parser.add_argument(
        "--current-task",
        default="sandwich_collaborative",
        help="Task name to send to /sandwich_supervisor/next_action.",
    )
    parser.add_argument(
        "--verify-step",
        default="",
        help="Optional step name to verify against the current observed state.",
    )
    parser.add_argument("--first-toast-on-plate", action="store_true")
    parser.add_argument("--ingredient-on-first-toast", action="store_true")
    parser.add_argument("--second-toast-on-top", action="store_true")
    args = parser.parse_args(argv)

    try:
        cfg = load_supervisor_config(args.config_path or DEFAULT_CONFIG_PATH)
    except Exception as exc:  # noqa: BLE001
        print(f"Invalid supervisor probe config: {exc}", file=sys.stderr)
        return int(CollaborativeRunnerExitCode.INVALID_RUNTIME)

    observation = SandwichSceneObservation(
        first_toast_on_plate=args.first_toast_on_plate,
        ingredient_on_first_toast=args.ingredient_on_first_toast,
        second_toast_on_top=args.second_toast_on_top,
    )

    initialized_rclpy = False
    client: SupervisorRos2Client | None = None
    if not rclpy.ok():
        rclpy.init()
        initialized_rclpy = True

    try:
        client = SupervisorRos2Client(cfg)
        client.wait_for_services()
        plan = client.plan_next_action(
            goal=args.goal,
            current_task=args.current_task,
            available_robot_skills=cfg.available_robot_skills,
            available_human_skills=cfg.available_human_skills,
            observation=observation,
        )
        print(json.dumps({"plan_next_action": asdict(plan)}, indent=2))

        if args.verify_step:
            verification = client.verify_step(
                step_name=args.verify_step,
                observation=observation,
            )
            print(json.dumps({"verify_step": asdict(verification)}, indent=2))

        return int(CollaborativeRunnerExitCode.DONE)
    except SupervisorServiceUnavailableError as exc:
        print(f"ROS2 supervisor service error: {exc}", file=sys.stderr)
        return int(CollaborativeRunnerExitCode.SERVICE_UNAVAILABLE)
    except (GeneratedInterfaceError, ValueError) as exc:
        print(f"Supervisor probe runtime error: {exc}", file=sys.stderr)
        return int(CollaborativeRunnerExitCode.INVALID_RUNTIME)
    finally:
        if client is not None:
            client.destroy_node()
        if initialized_rclpy and rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
