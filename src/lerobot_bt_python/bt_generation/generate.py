"""CLI for runtime BT generation."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

from . import env_snapshot
from . import experiment_log
from .manifest import build_generation_manifest, write_generation_manifest
from .planner import TASK_TEMPLATES, build_linear_plan
from .registry import load_registry, validate_registry
from .renderer import render_bt_params_yaml, render_xml
from .static_checks import validate_xml_yaml_blackboard_text
from .validator import validate_linear_plan
from .vlm_planner import canonicalize_plan, parse_planner_response


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a runtime BT XML/YAML pair.")
    parser.add_argument("--task", required=True, help="Known deterministic task name.")
    parser.add_argument(
        "--planner",
        choices=("template", "model-response", "ros-service"),
        default="template",
        help="Planner source. template is deterministic; model-response reads Linear IR JSON; ros-service queries a ROS2 planning service.",
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
        default=30.0,
        help="Timeout (seconds) for ROS2 planning service.",
    )
    parser.add_argument(
        "--scene-facts-file",
        type=Path,
        help="Optional JSON file with scene facts for planning.",
    )
    parser.add_argument(
        "--model-response-file",
        type=Path,
        help="Path to a pre-generated model Linear IR JSON response.",
    )
    parser.add_argument("--registry", required=True, type=Path, help="skills_registry.yaml path.")
    parser.add_argument("--executor-yaml", type=Path, help="Executor YAML used for consistency checks.")
    parser.add_argument("--out-tree", type=Path, help="Output BehaviorTree.CPP XML path.")
    parser.add_argument("--out-config", type=Path, help="Output BT params YAML path.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help=(
            "Repository-local output directory. When --out-tree/--out-config are not provided, "
            "writes trees/<task>.xml and config/<task>_bt.yaml under this directory."
        ),
    )
    parser.add_argument(
        "--explicit-postcondition-gates",
        action="store_true",
        help=(
            "Also render robot_skill verify_after gates. Off by default because "
            "the current DoSkill C++ node already waits for GetSkillVerification."
        ),
    )
    parser.add_argument(
        "--experiment-log",
        type=Path,
        help=(
            "Append-only JSONL file for experiment events. When omitted and "
            "--output-dir is set, defaults to <output-dir>/experiments/trials.jsonl."
        ),
    )
    parser.add_argument(
        "--trial-id",
        type=str,
        help="Stable trial id. Generated automatically when not provided.",
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

    start_time = time.time()
    trial_id = args.trial_id or experiment_log.new_trial_id(args.task, args.planner)
    planner_label = args.planner_label or args.planner
    condition_label = args.condition_label or "default"
    env = _environment_snapshot(argv)
    setattr(args, "_env_snapshot", env)

    errors: list[str] = []
    failure_stage: str | None = None
    out_tree, out_config, output_errors = _resolve_tree_config_paths(args)
    errors.extend(output_errors)
    if output_errors:
        failure_stage = experiment_log.STAGE_VALIDATION
    plan_output_path = _plan_output_path(args)
    raw_response_output_path: Path | None = None
    model_response_text: str | None = None

    try:
        if not errors:
            registry = load_registry(args.registry)
            registry_errors = validate_registry(registry)
            if registry_errors:
                errors.extend(registry_errors)
                failure_stage = experiment_log.STAGE_VALIDATION

        if not errors:
            if args.planner == "template":
                plan = build_linear_plan(
                    args.task,
                    registry,
                    explicit_robot_postcondition_gates=args.explicit_postcondition_gates,
                )
                template_errors = validate_linear_plan(plan, registry, args.executor_yaml)
                if template_errors:
                    errors.extend(template_errors)
                    failure_stage = experiment_log.STAGE_VALIDATION
            elif args.planner == "model-response":
                if args.model_response_file is None:
                    errors.append("--planner model-response requires --model-response-file.")
                    failure_stage = experiment_log.STAGE_VALIDATION
                    plan = None
                else:
                    model_response_text = args.model_response_file.read_text(encoding="utf-8")
                    raw_response_output_path = _raw_response_output_path(args, model_response_text)
                    try:
                        parsed = parse_planner_response(model_response_text)
                    except Exception as exc:  # noqa: BLE001
                        errors.append(str(exc))
                        failure_stage = experiment_log.STAGE_PARSE
                        plan = None
                    else:
                        try:
                            plan = canonicalize_plan(parsed, registry)
                        except Exception as exc:  # noqa: BLE001
                            errors.append(str(exc))
                            failure_stage = experiment_log.STAGE_VALIDATION
                            plan = None
                        else:
                            if plan["task_name"] != args.task:
                                errors.append(
                                    f"Planner response task_name {plan['task_name']!r} does not "
                                    f"match requested task_name {args.task!r}."
                                )
                                failure_stage = experiment_log.STAGE_VALIDATION
                            else:
                                validation_errors = validate_linear_plan(
                                    plan,
                                    registry,
                                    args.executor_yaml,
                                    strict_generated=True,
                                )
                                if validation_errors:
                                    errors.extend(validation_errors)
                                    failure_stage = experiment_log.STAGE_VALIDATION
            elif args.planner == "ros-service":
                # Build planner registry payload
                from .export_planner_registry import build_planner_registry_payload
                from .ros_plan_client import request_plan_from_ros_service
                planner_registry_payload = build_planner_registry_payload(args.task, registry)
                scene_facts = None
                if args.scene_facts_file is not None:
                    scene_facts = json.loads(args.scene_facts_file.read_text(encoding="utf-8"))
                # Call ROS service
                try:
                    model_response_text = request_plan_from_ros_service(
                        args.task,
                        planner_registry_payload,
                        service_name=args.plan_service_name,
                        scene_facts=scene_facts,
                        timeout_s=args.plan_service_timeout_s,
                    )
                except Exception as exc:
                    errors.append(str(exc))
                    failure_stage = experiment_log.STAGE_SERVICE
                    plan = None
                else:
                    raw_response_output_path = _raw_response_output_path(args, model_response_text or "")
                    try:
                        parsed = parse_planner_response(model_response_text)
                    except Exception as exc:  # noqa: BLE001
                        errors.append(str(exc))
                        failure_stage = experiment_log.STAGE_PARSE
                        plan = None
                    else:
                        try:
                            plan = canonicalize_plan(parsed, registry)
                        except Exception as exc:  # noqa: BLE001
                            errors.append(str(exc))
                            failure_stage = experiment_log.STAGE_VALIDATION
                            plan = None
                        else:
                            if plan["task_name"] != args.task:
                                errors.append(
                                    f"Planner response task_name {plan['task_name']!r} does not "
                                    f"match requested task_name {args.task!r}."
                                )
                                failure_stage = experiment_log.STAGE_VALIDATION
                            else:
                                validation_errors = validate_linear_plan(
                                    plan,
                                    registry,
                                    args.executor_yaml,
                                    strict_generated=True,
                                )
                                if validation_errors:
                                    errors.extend(validation_errors)
                                    failure_stage = experiment_log.STAGE_VALIDATION
        else:
            plan = None
    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))
        if failure_stage is None:
            failure_stage = experiment_log.STAGE_UNKNOWN
        plan = None

    if errors or plan is None:
        if raw_response_output_path is not None and model_response_text is not None:
            _write_text(raw_response_output_path, model_response_text)
        _print_errors(errors)
        _log_generation_event(
            args,
            trial_id=trial_id,
            planner_label=planner_label,
            condition_label=condition_label,
            success=False,
            failure_stage=failure_stage or experiment_log.STAGE_UNKNOWN,
            failure_reason="; ".join(errors) or None,
            start_time=start_time,
            out_tree=out_tree,
            out_config=out_config,
            plan_output_path=plan_output_path,
            raw_response_output_path=raw_response_output_path,
        )
        return 1

    try:
        xml_text = render_xml(plan, registry)
        yaml_text = render_bt_params_yaml(plan, registry)
        errors.extend(validate_xml_yaml_blackboard_text(xml_text, yaml_text))
    except Exception as exc:  # noqa: BLE001
        _print_errors([str(exc)])
        _log_generation_event(
            args,
            trial_id=trial_id,
            planner_label=planner_label,
            condition_label=condition_label,
            success=False,
            failure_stage=experiment_log.STAGE_STATIC_CHECK,
            failure_reason=str(exc),
            start_time=start_time,
            out_tree=out_tree,
            out_config=out_config,
            plan_output_path=plan_output_path,
            raw_response_output_path=raw_response_output_path,
        )
        return 1

    if errors:
        _print_errors(errors)
        _log_generation_event(
            args,
            trial_id=trial_id,
            planner_label=planner_label,
            condition_label=condition_label,
            success=False,
            failure_stage=experiment_log.STAGE_STATIC_CHECK,
            failure_reason="; ".join(errors) or None,
            start_time=start_time,
            out_tree=out_tree,
            out_config=out_config,
            plan_output_path=plan_output_path,
            raw_response_output_path=raw_response_output_path,
        )
        return 1

    assert out_tree is not None
    assert out_config is not None
    try:
        if plan_output_path is not None:
            _write_text(plan_output_path, json.dumps(plan, indent=2, sort_keys=True) + "\n")
        if raw_response_output_path is not None and model_response_text is not None:
            _write_text(raw_response_output_path, model_response_text)
        _write_text(out_tree, xml_text)
        _write_text(out_config, yaml_text)
        manifest_output_path = _manifest_output_path(args)
        if manifest_output_path is not None:
            manifest = build_generation_manifest(
                task_name=args.task,
                planner=args.planner,
                registry_path=args.registry,
                executor_yaml_path=args.executor_yaml,
                tree_xml_path=out_tree,
                bt_yaml_path=out_config,
                canonical_task_sequence=[dict(step) for step in TASK_TEMPLATES[args.task]],
                linear_ir_path=plan_output_path,
                raw_response_path=raw_response_output_path,
            )
            write_generation_manifest(manifest_output_path, manifest)
    except Exception as exc:  # noqa: BLE001
        _print_errors([str(exc)])
        _log_generation_event(
            args,
            trial_id=trial_id,
            planner_label=planner_label,
            condition_label=condition_label,
            success=False,
            failure_stage=experiment_log.STAGE_ARTIFACT_WRITE,
            failure_reason=str(exc),
            start_time=start_time,
            out_tree=out_tree,
            out_config=out_config,
            plan_output_path=plan_output_path,
            raw_response_output_path=raw_response_output_path,
        )
        return 1

    _log_generation_event(
        args,
        trial_id=trial_id,
        planner_label=planner_label,
        condition_label=condition_label,
        success=True,
        failure_stage=None,
        failure_reason=None,
        start_time=start_time,
        out_tree=out_tree,
        out_config=out_config,
        plan_output_path=plan_output_path,
        raw_response_output_path=raw_response_output_path,
    )

    counts = Counter(step["kind"] for step in plan["steps"])
    print(f"task_name: {plan['task_name']}")
    print(f"robot_skill: {counts.get('robot_skill', 0)}")
    print(f"human_step: {counts.get('human_step', 0)}")
    print(f"vlm_gate: {counts.get('vlm_gate', 0)}")
    if plan_output_path is not None:
        print(f"wrote plan: {plan_output_path}")
    print(f"wrote tree: {out_tree}")
    print(f"wrote config: {out_config}")
    if raw_response_output_path is not None:
        print(f"wrote raw response: {raw_response_output_path}")
    if manifest_output_path is not None:
        print(f"wrote manifest: {manifest_output_path}")
    return 0


def _resolve_tree_config_paths(args: argparse.Namespace) -> tuple[Path | None, Path | None, list[str]]:
    has_out_tree = args.out_tree is not None
    has_out_config = args.out_config is not None
    if has_out_tree != has_out_config:
        return None, None, ["--out-tree and --out-config must be provided together."]

    if has_out_tree and has_out_config:
        return args.out_tree, args.out_config, []

    if args.output_dir is not None:
        return (
            args.output_dir / "trees" / f"{args.task}.xml",
            args.output_dir / "config" / f"{args.task}_bt.yaml",
            [],
        )

    return None, None, ["Provide --out-tree and --out-config, or provide --output-dir."]


def _plan_output_path(args: argparse.Namespace) -> Path | None:
    if args.output_dir is None or args.planner not in ("model-response", "ros-service"):
        return None
    return args.output_dir / "plans" / f"{args.task}_linear_ir.json"


def _raw_response_output_path(args: argparse.Namespace, model_response_text: str) -> Path | None:
    if args.output_dir is None or args.planner not in ("model-response", "ros-service"):
        return None

    suffix = ".json" if _is_json_document(model_response_text) else ".txt"
    return args.output_dir / "raw_model_responses" / f"{args.task}_raw_response{suffix}"


def _manifest_output_path(args: argparse.Namespace) -> Path | None:
    if args.output_dir is None:
        return None
    return args.output_dir / "manifests" / f"{args.task}_manifest.json"


def _is_json_document(text: str) -> bool:
    try:
        json.loads(text)
    except json.JSONDecodeError:
        return False
    return True


def _log_generation_event(
    args: argparse.Namespace,
    *,
    trial_id: str,
    planner_label: str,
    condition_label: str,
    success: bool,
    failure_stage: str | None,
    failure_reason: str | None,
    start_time: float,
    out_tree: Path | None,
    out_config: Path | None,
    plan_output_path: Path | None,
    raw_response_output_path: Path | None,
) -> None:
    log_path = experiment_log.resolve_log_path(args.experiment_log, args.output_dir)
    if log_path is None:
        return
    manifest_path = _manifest_output_path(args)
    env = getattr(args, "_env_snapshot", None) or {}
    event = experiment_log.build_event(
        event_type=experiment_log.EVENT_GENERATION,
        trial_id=trial_id,
        task_name=args.task,
        planner=args.planner,
        planner_label=planner_label,
        condition_label=condition_label,
        success=success,
        failure_stage=failure_stage,
        failure_reason=failure_reason,
        duration_s=time.time() - start_time,
        output_dir=str(args.output_dir) if args.output_dir is not None else None,
        linear_ir_path=str(plan_output_path) if plan_output_path is not None else None,
        raw_response_path=str(raw_response_output_path)
        if raw_response_output_path is not None
        else None,
        tree_xml_path=str(out_tree) if out_tree is not None else None,
        bt_yaml_path=str(out_config) if out_config is not None else None,
        manifest_path=str(manifest_path) if manifest_path is not None else None,
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
            "python -m lerobot_bt_python.bt_generation.generate",
            *[str(part) for part in argv],
        ]
    return env_snapshot.build_environment_snapshot(repo_root, command_argv)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _print_errors(errors: list[str]) -> None:
    print("BT generation failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
