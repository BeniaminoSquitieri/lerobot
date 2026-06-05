"""Fake ROS2 BT executor server and pure-Python scenario simulator.

This module deliberately avoids robot, policy, camera, VLM, and transformer
imports. The ROS2 server path imports rclpy and generated service bindings only
inside ``main`` so unit tests can use the pure-Python simulator without ROS2.

Smoke-test only: this is NOT the real robot skill server. The real skill server
is ``lerobot_bt_python.server``. Do not use this fake on robot day.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from lerobot_bt_python.bt_generation.registry import ROBOT_SKILL

SUCCESS = "SUCCESS"
FAILURE = "FAILURE"
RUNNING = "RUNNING"
ERROR = "ERROR"
TIMEOUT = "TIMEOUT"

ALLOWED_VLM_STATUSES = {RUNNING, SUCCESS, FAILURE}
TERMINAL_FAILURE_STATUSES = {FAILURE, ERROR, TIMEOUT}


@dataclass
class CommandOutcome:
    """Fake RunNamedCommand result for one command name."""

    status: str = SUCCESS
    elapsed_s: float = 0.0
    message: str = ""

    @property
    def success(self) -> bool:
        return self.status == SUCCESS


@dataclass
class FakeScenario:
    """Configurable command and VLM responses for fake BT execution."""

    commands: dict[str, CommandOutcome] = field(default_factory=dict)
    verifications: dict[str, list[str]] = field(default_factory=dict)

    def command_for(self, name: str) -> CommandOutcome:
        return self.commands.get(name, CommandOutcome(message=f"Fake command {name} succeeded."))

    def verification_for(self, name: str, poll_index: int) -> str:
        statuses = self.verifications.get(name, [SUCCESS])
        if not statuses:
            return SUCCESS
        return statuses[min(poll_index, len(statuses) - 1)]


@dataclass
class FakeExecutionResult:
    """Pure-Python execution result for a Linear IR plan."""

    status: str
    message: str
    visited_steps: list[str]
    robot_skills: list[str]


def load_fake_scenario(name: str | None = None, scenario_file: Path | None = None) -> FakeScenario:
    """Load a built-in or YAML scenario."""

    if scenario_file is not None:
        data = yaml.safe_load(scenario_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{scenario_file} must contain a YAML mapping.")
        return scenario_from_dict(data)

    scenario_name = name or "success_all"
    scenarios = builtin_scenarios()
    if scenario_name not in scenarios:
        known = ", ".join(sorted(scenarios))
        raise ValueError(f"Unknown fake scenario {scenario_name!r}. Known scenarios: {known}.")
    return scenarios[scenario_name]


def scenario_from_dict(data: dict[str, Any]) -> FakeScenario:
    """Build a fake scenario from YAML-compatible data."""

    command_data = data.get("commands", {}) or {}
    verification_data = data.get("verifications", {}) or {}
    if not isinstance(command_data, dict):
        raise ValueError("scenario.commands must be a mapping.")
    if not isinstance(verification_data, dict):
        raise ValueError("scenario.verifications must be a mapping.")

    commands = {
        str(name): CommandOutcome(
            status=str(raw.get("status", SUCCESS) if isinstance(raw, dict) else raw),
            elapsed_s=float(raw.get("elapsed_s", 0.0)) if isinstance(raw, dict) else 0.0,
            message=str(raw.get("message", "")) if isinstance(raw, dict) else "",
        )
        for name, raw in command_data.items()
    }
    verifications = {
        str(name): [str(status) for status in statuses]
        if isinstance(statuses, list)
        else [str(statuses)]
        for name, statuses in verification_data.items()
    }
    return FakeScenario(commands=commands, verifications=verifications)


def builtin_scenarios() -> dict[str, FakeScenario]:
    """Return built-in scenarios used by tests and manual fake-server runs."""

    success_verifications = _success_verifications()
    return {
        "success_all": FakeScenario(verifications=success_verifications),
        "initial_scene_failed": FakeScenario(
            verifications={**success_verifications, "initial_scene_ready": [FAILURE]},
        ),
        "robot_first_toast_failed": FakeScenario(
            commands={"place_first_toast": CommandOutcome(status=FAILURE, message="first toast command failed")},
            verifications=success_verifications,
        ),
        "human_pouring_timeout": FakeScenario(
            verifications={
                **success_verifications,
                "pour_ingredient": [RUNNING],
                "ingredient_poured": [RUNNING],
            },
        ),
        "vlm_postcondition_failed": FakeScenario(
            verifications={
                **success_verifications,
                "place_first_toast": [FAILURE],
                "first_toast_placed": [FAILURE],
            },
        ),
        "unknown_status": FakeScenario(
            verifications={
                **success_verifications,
                "place_first_toast": ["DONE"],
                "first_toast_placed": ["SUCESS"],
            },
        ),
    }


def execute_linear_plan_with_fake_responses(
    plan: dict,
    scenario: FakeScenario,
    *,
    running_poll_limit: int = 3,
) -> FakeExecutionResult:
    """Execute Linear IR against fake command/VLM responses without ROS2."""

    visited_steps: list[str] = []
    robot_skills: list[str] = []
    for step in plan.get("steps", []):
        kind = step["kind"]
        name = step["name"]
        visited_steps.append(name)
        if kind == ROBOT_SKILL:
            robot_skills.append(name)

        command = scenario.command_for(name)
        command_status = normalize_terminal_status(command.status)
        if command_status != SUCCESS:
            return FakeExecutionResult(
                status=command_status,
                message=command.message or f"Command {name} ended as {command_status}.",
                visited_steps=visited_steps,
                robot_skills=robot_skills,
            )

        status = _poll_verification(name, scenario, running_poll_limit=running_poll_limit)
        if status != SUCCESS:
            return FakeExecutionResult(
                status=status,
                message=f"Verification for {name} ended as {status}.",
                visited_steps=visited_steps,
                robot_skills=robot_skills,
            )

    return FakeExecutionResult(
        status=SUCCESS,
        message="Fake plan execution completed.",
        visited_steps=visited_steps,
        robot_skills=robot_skills,
    )


def normalize_vlm_status(status: str) -> str:
    """Normalize fake VLM status so typos never spin forever."""

    normalized = str(status).strip().upper()
    if normalized in ALLOWED_VLM_STATUSES:
        return normalized
    return ERROR


def normalize_terminal_status(status: str) -> str:
    """Normalize command status for the fake command path."""

    normalized = str(status).strip().upper()
    if normalized in {SUCCESS, FAILURE, ERROR, TIMEOUT}:
        return normalized
    return ERROR


def _poll_verification(name: str, scenario: FakeScenario, *, running_poll_limit: int) -> str:
    for poll_index in range(max(1, running_poll_limit)):
        status = normalize_vlm_status(scenario.verification_for(name, poll_index))
        if status == SUCCESS:
            return SUCCESS
        if status in TERMINAL_FAILURE_STATUSES:
            return status
    return TIMEOUT


def _success_verifications() -> dict[str, list[str]]:
    names = [
        "initial_scene_ready",
        "place_first_toast",
        "first_toast_placed",
        "pour_ingredient",
        "ingredient_poured",
        "place_second_toast",
        "second_toast_placed",
        "make_sandwich.task_complete",
    ]
    return {name: [SUCCESS] for name in names}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a fake ROS2 BT executor server.")
    parser.add_argument("--scenario", default="success_all", help="Built-in fake scenario name.")
    parser.add_argument("--scenario-file", type=Path, help="YAML scenario file.")
    parser.add_argument("--bt-command-service", default="/lerobot_bt/run")
    parser.add_argument("--vlm-state-service", default="/lerobot_bt/vlm_state")
    parser.add_argument(
        "--running-polls-before-failure",
        type=int,
        default=3,
        help="Convert repeated RUNNING fake statuses to FAILURE after this many polls.",
    )
    args = parser.parse_args(argv)

    from lerobot_bt_python.bt_interface_paths import load_bt_services

    import rclpy
    from rclpy.node import Node

    run_named_command, get_skill_verification, _ = load_bt_services()
    scenario = load_fake_scenario(args.scenario, args.scenario_file)

    class FakeBtExecutorServer(Node):
        def __init__(self) -> None:
            super().__init__("fake_bt_executor_server")
            self._scenario = scenario
            self._polls: dict[str, int] = {}
            self._attempts: dict[str, int] = {}
            self._command_calls: list[str] = []
            self.create_service(run_named_command, args.bt_command_service, self._handle_command)
            self.create_service(get_skill_verification, args.vlm_state_service, self._handle_vlm_state)
            self.get_logger().info(
                f"Fake BT executor serving scenario={args.scenario!r} "
                f"command_service={args.bt_command_service!r} "
                f"vlm_state_service={args.vlm_state_service!r}"
            )

        def _handle_command(self, request, response):
            name = str(request.name)
            self._command_calls.append(name)
            self._attempts[name] = self._attempts.get(name, 0) + 1
            self._polls[name] = 0

            outcome = self._scenario.command_for(name)
            status = normalize_terminal_status(outcome.status)
            response.success = status == SUCCESS
            response.status = status
            response.elapsed_s = float(outcome.elapsed_s)
            response.message = outcome.message or f"Fake command {request.kind}:{name} -> {status}"
            self.get_logger().info(response.message)
            return response

        def _handle_vlm_state(self, request, response):
            name = str(request.skill_name)
            poll_index = self._polls.get(name, 0)
            self._polls[name] = poll_index + 1

            status = normalize_vlm_status(self._scenario.verification_for(name, poll_index))
            if status == RUNNING and poll_index + 1 >= max(1, args.running_polls_before_failure):
                status = FAILURE
                message = f"Fake VLM timeout for {name} after {poll_index + 1} RUNNING polls."
            elif status == ERROR:
                status = FAILURE
                message = f"Fake VLM status for {name} was unknown; normalized to FAILURE."
            else:
                message = f"Fake VLM state {name} -> {status}"

            response.has_attempt = name in self._attempts or name in self._scenario.verifications
            response.attempt_id = int(self._attempts.get(name, 1))
            response.status = status
            response.message = message
            self.get_logger().info(message)
            return response

    rclpy.init()
    node = FakeBtExecutorServer()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
