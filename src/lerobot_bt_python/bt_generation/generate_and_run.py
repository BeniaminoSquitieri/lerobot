"""Generate a runtime BT once, then run the existing C++ BT runner."""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from . import generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a runtime BT XML/YAML pair and run lerobot_bt_runner.",
    )
    parser.add_argument("--task", required=True, help="Known task name.")
    parser.add_argument(
        "--planner",
        choices=("template", "model-response", "ros-service"),
        default="template",
        help="Planner source passed through to bt_generation.generate.",
    )
    parser.add_argument(
        "--model-response-file",
        type=Path,
        help="Path to a pre-generated model Linear IR JSON response.",
    )
    parser.add_argument(
        "--plan-service-name",
        default="/lerobot_bt/generate_plan",
        help="ROS2 service name for ros-service planner mode.",
    )
    parser.add_argument(
        "--plan-service-timeout-s",
        type=float,
        default=30.0,
        help="Timeout (seconds) for ROS2 planning service.",
    )
    parser.add_argument(
        "--scene-facts-file",
        type=Path,
        help="Optional JSON file with scene facts for planning.",
    )
    parser.add_argument("--registry", required=True, type=Path, help="skills_registry.yaml path.")
    parser.add_argument("--executor-yaml", type=Path, help="Executor YAML used for consistency checks.")
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Generated BT output directory containing trees/ and config/ subdirectories.",
    )
    parser.add_argument(
        "--explicit-postcondition-gates",
        action="store_true",
        help="Pass through to the generator for manual experiments.",
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Generate artifacts and print the runner command without executing ros2.",
    )
    args = parser.parse_args(argv)

    generation_args = _generation_args(args)
    generation_status = generate.main(generation_args)
    if generation_status != 0:
        print("BT generation failed; not starting lerobot_bt_runner.", file=sys.stderr)
        return generation_status

    tree_path = args.output_dir / "trees" / f"{args.task}.xml"
    config_path = args.output_dir / "config" / f"{args.task}_bt.yaml"
    plan_path = _generated_plan_path(args)
    missing = [path for path in (tree_path, config_path) if not path.exists()]
    if missing:
        _print_errors([f"Expected generated file does not exist: {path}" for path in missing])
        return 1

    runner_command = build_runner_command(tree_path, config_path)
    if plan_path is not None and plan_path.exists():
        print(f"generated plan: {plan_path}")
    print(f"generated tree: {tree_path}")
    print(f"generated config: {config_path}")
    print(f"runner command: {_format_command(runner_command)}")

    if args.no_run:
        return 0

    if shutil.which("ros2") is None:
        _print_errors(
            [
                "ros2 command not found. Source ROS2 and the built workspace before running "
                "without --no-run.",
                "Example: source /opt/ros/<distro>/setup.bash && source install/setup.bash",
            ]
        )
        return 127

    result = subprocess.run(runner_command, check=False)
    return int(result.returncode)


def build_runner_command(tree_path: Path, config_path: Path) -> list[str]:
    return [
        "ros2",
        "run",
        "lerobot_bt_runtime_cpp",
        "lerobot_bt_runner",
        "--ros-args",
        "--params-file",
        str(config_path),
        "-p",
        f"tree_xml_path:={tree_path}",
    ]


def _generated_plan_path(args: argparse.Namespace) -> Path | None:
    if args.planner not in {"model-response", "ros-service"}:
        return None
    return args.output_dir / "plans" / f"{args.task}_linear_ir.json"


def _generation_args(args: argparse.Namespace) -> list[str]:
    generation_args = [
        "--task",
        args.task,
        "--planner",
        args.planner,
        "--registry",
        str(args.registry),
        "--output-dir",
        str(args.output_dir),
        "--plan-service-name",
        args.plan_service_name,
        "--plan-service-timeout-s",
        str(args.plan_service_timeout_s),
    ]
    if args.executor_yaml is not None:
        generation_args.extend(["--executor-yaml", str(args.executor_yaml)])
    if args.model_response_file is not None:
        generation_args.extend(["--model-response-file", str(args.model_response_file)])
    if args.scene_facts_file is not None:
        generation_args.extend(["--scene-facts-file", str(args.scene_facts_file)])
    if args.explicit_postcondition_gates:
        generation_args.append("--explicit-postcondition-gates")
    return generation_args


def _format_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _print_errors(errors: list[str]) -> None:
    print("BT generate-and-run failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
