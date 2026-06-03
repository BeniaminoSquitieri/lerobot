"""Robot-day entry point for one-shot BT generation and optional execution.

This module runs at episode start on the real runtime path. It generates one
validated BT from a task name and planner source, writes XML/YAML/manifest
artifacts, and can then launch the thin C++ BehaviorTree.CPP runner. Raw VLM
output never executes directly here: generation must pass lerobot validation
before the runner is allowed to load the produced files.
"""

from __future__ import annotations

import argparse
import atexit
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import env_snapshot, experiment_log, generate


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
    parser.add_argument(
        "--cleanup-output-dir-on-exit",
        action="store_true",
        help=(
            "Best-effort cleanup of --output-dir when this command exits. "
            "Useful for temporary robot-day runs where you do not want generated "
            "BT artifacts to persist."
        ),
    )
    parser.add_argument(
        "--experiment-log",
        type=Path,
        help=(
            "Append-only JSONL file for experiment events. When omitted, defaults to "
            "<output-dir>/experiments/trials.jsonl."
        ),
    )
    parser.add_argument(
        "--trial-id",
        type=str,
        help="Stable trial id shared by generation and runner events.",
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
    args = parser.parse_args(argv)

    trial_id = args.trial_id or experiment_log.new_trial_id(args.task, args.planner)
    planner_label = args.planner_label or args.planner
    condition_label = args.condition_label or "default"
    log_path = experiment_log.resolve_log_path(args.experiment_log, args.output_dir)
    env = _environment_snapshot(argv)

    if args.cleanup_output_dir_on_exit:
        _register_output_dir_cleanup(args.output_dir)

    # Print the trial id up front so an operator can copy it before the run
    # starts (needed later for the annotation step).
    print(f"trial_id: {trial_id}")

    generation_args = _generation_args(args, trial_id=trial_id, log_path=log_path)
    generation_status = generate.main(generation_args)
    if generation_status != 0:
        print("BT generation failed; not starting lerobot_bt_runner.", file=sys.stderr)
        return generation_status

    tree_path = args.output_dir / "trees" / f"{args.task}.xml"
    config_path = args.output_dir / "config" / f"{args.task}_bt.yaml"
    plan_path = _generated_plan_path(args)
    manifest_path = _generated_manifest_path(args)
    missing = [path for path in (tree_path, config_path) if not path.exists()]
    if missing:
        _print_errors([f"Expected generated file does not exist: {path}" for path in missing])
        return 1

    runner_command = build_runner_command(tree_path, config_path)
    if plan_path is not None and plan_path.exists():
        print(f"generated plan: {plan_path}")
    print(f"generated tree: {tree_path}")
    print(f"generated config: {config_path}")
    if manifest_path.exists():
        print(f"generated manifest: {manifest_path}")
    print(f"runner command: {_format_command(runner_command)}")

    # Semantics for --no-run: no runner event is logged. The runner never
    # starts, so it must not affect runner_success_rate. The generation event
    # written by generate.py already records that artifacts were produced.
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
        _log_runner_event(
            args,
            log_path=log_path,
            trial_id=trial_id,
            planner_label=planner_label,
            condition_label=condition_label,
            runner_started=False,
            runner_return_code=127,
            duration_s=0.0,
            tree_path=tree_path,
            config_path=config_path,
            plan_path=plan_path,
            manifest_path=manifest_path,
            env=env,
        )
        return 127

    start_time = time.time()
    result = subprocess.run(runner_command, check=False)
    return_code = int(result.returncode)
    _log_runner_event(
        args,
        log_path=log_path,
        trial_id=trial_id,
        planner_label=planner_label,
        condition_label=condition_label,
        runner_started=True,
        runner_return_code=return_code,
        duration_s=time.time() - start_time,
        tree_path=tree_path,
        config_path=config_path,
        plan_path=plan_path,
        manifest_path=manifest_path,
        env=env,
    )
    return return_code


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


def _generated_manifest_path(args: argparse.Namespace) -> Path:
    return args.output_dir / "manifests" / f"{args.task}_manifest.json"


def _generation_args(
    args: argparse.Namespace,
    *,
    trial_id: str,
    log_path: Path | None,
) -> list[str]:
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
        "--trial-id",
        trial_id,
    ]
    if log_path is not None:
        generation_args.extend(["--experiment-log", str(log_path)])
    if args.planner_label is not None:
        generation_args.extend(["--planner-label", args.planner_label])
    if args.condition_label is not None:
        generation_args.extend(["--condition-label", args.condition_label])
    if args.executor_yaml is not None:
        generation_args.extend(["--executor-yaml", str(args.executor_yaml)])
    if args.model_response_file is not None:
        generation_args.extend(["--model-response-file", str(args.model_response_file)])
    if args.scene_facts_file is not None:
        generation_args.extend(["--scene-facts-file", str(args.scene_facts_file)])
    if args.explicit_postcondition_gates:
        generation_args.append("--explicit-postcondition-gates")
    return generation_args


def _log_runner_event(
    args: argparse.Namespace,
    *,
    log_path: Path | None,
    trial_id: str,
    planner_label: str,
    condition_label: str,
    runner_started: bool,
    runner_return_code: int | None,
    duration_s: float,
    tree_path: Path,
    config_path: Path,
    plan_path: Path | None,
    manifest_path: Path,
    env: dict | None = None,
) -> None:
    if log_path is None:
        return
    env = env or {}
    success = runner_return_code == 0
    failure_stage = None if success else experiment_log.STAGE_RUNNER
    event = experiment_log.build_event(
        event_type=experiment_log.EVENT_RUNNER,
        trial_id=trial_id,
        task_name=args.task,
        planner=args.planner,
        planner_label=planner_label,
        condition_label=condition_label,
        success=success,
        failure_stage=failure_stage,
        failure_reason=None
        if success
        else f"runner exited with return code {runner_return_code}.",
        duration_s=duration_s,
        output_dir=str(args.output_dir),
        linear_ir_path=str(plan_path) if plan_path is not None else None,
        raw_response_path=None,
        tree_xml_path=str(tree_path),
        bt_yaml_path=str(config_path),
        manifest_path=str(manifest_path) if manifest_path.exists() else None,
        runner_started=runner_started,
        runner_return_code=runner_return_code,
        git_commit=env.get("git_commit"),
        git_branch=env.get("git_branch"),
        hostname=env.get("hostname"),
        ros_distro=env.get("ros_distro"),
        command=env.get("command"),
    )
    experiment_log.append_event(log_path, event)


def _environment_snapshot(argv: list[str] | None) -> dict:
    repo_root = Path(__file__).resolve().parents[3]
    if argv is None:
        command_argv = list(sys.argv)
    else:
        command_argv = [
            "python -m lerobot_bt_python.bt_generation.generate_and_run",
            *[str(part) for part in argv],
        ]
    return env_snapshot.build_environment_snapshot(repo_root, command_argv)


def _register_output_dir_cleanup(output_dir: Path) -> None:
    output_dir = output_dir.resolve()

    def _cleanup() -> None:
        if not output_dir.exists():
            return
        # Refuse suspiciously broad deletions.
        if str(output_dir) in {"/", str(Path.home()), str(Path.cwd())}:
            print(
                f"Skipping cleanup of suspicious output dir: {output_dir}",
                file=sys.stderr,
            )
            return
        shutil.rmtree(output_dir, ignore_errors=True)

    atexit.register(_cleanup)


def _format_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _print_errors(errors: list[str]) -> None:
    print("BT generate-and-run failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
