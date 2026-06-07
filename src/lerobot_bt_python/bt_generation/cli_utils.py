"""Shared helpers for BT generation command-line entry points."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import env_snapshot


def add_planner_source_arguments(
    parser: argparse.ArgumentParser,
    *,
    planner_help: str,
) -> None:
    """Add planner-source options shared by generation entry points."""

    parser.add_argument(
        "--planner",
        choices=("template", "model-response", "ros-service"),
        default="template",
        help=planner_help,
    )
    parser.add_argument(
        "--model-response-file",
        type=Path,
        help="Path to a pre-generated model Linear IR JSON response.",
    )
    parser.add_argument(
        "--plan-service-name",
        type=str,
        default="/lerobot_bt/generate_plan",
        help="ROS2 service name for ros-service planner mode.",
    )
    parser.add_argument(
        "--plan-service-timeout-s",
        type=float,
        default=0.0,
        help="Timeout (seconds) for ROS2 planning service. Use 0 to wait indefinitely.",
    )
    parser.add_argument(
        "--scene-facts-file",
        type=Path,
        help="Optional JSON file with scene facts for planning.",
    )


def add_registry_arguments(parser: argparse.ArgumentParser) -> None:
    """Add registry and executor-config options shared by generation CLIs."""

    parser.add_argument("--registry", required=True, type=Path, help="skills_registry.yaml path.")
    parser.add_argument("--executor-yaml", type=Path, help="Executor YAML used for consistency checks.")


def add_explicit_postcondition_gates_argument(
    parser: argparse.ArgumentParser,
    *,
    help_text: str,
) -> None:
    """Add the opt-in postcondition-gate rendering flag."""

    parser.add_argument(
        "--explicit-postcondition-gates",
        action="store_true",
        help=help_text,
    )


def add_experiment_label_arguments(
    parser: argparse.ArgumentParser,
    *,
    trial_id_help: str,
) -> None:
    """Add trial and label options shared by generation experiment CLIs."""

    parser.add_argument(
        "--trial-id",
        type=str,
        help=trial_id_help,
    )
    parser.add_argument(
        "--planner-label",
        type=str,
        help="Human-readable planner label for experiment grouping (defaults to --planner).",
    )
    parser.add_argument(
        "--condition-label",
        type=str,
        help="Experiment condition label for grouping (defaults to 'default').",
    )


def environment_snapshot(module_name: str, argv: list[str] | None) -> dict:
    """Build a provenance snapshot for a module-style CLI invocation."""

    repo_root = Path(__file__).resolve().parents[3]
    if argv is None:
        command_argv = list(sys.argv)
    else:
        command_argv = [
            f"python -m {module_name}",
            *[str(part) for part in argv],
        ]
    return env_snapshot.build_environment_snapshot(repo_root, command_argv)


def print_errors(header: str, errors: list[str]) -> None:
    """Print a consistent stderr error list for CLI failures."""

    print(header, file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
