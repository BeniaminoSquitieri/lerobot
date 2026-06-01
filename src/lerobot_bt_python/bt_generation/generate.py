"""CLI for runtime BT generation."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

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
    args = parser.parse_args(argv)

    errors: list[str] = []
    out_tree, out_config, output_errors = _resolve_tree_config_paths(args)
    errors.extend(output_errors)
    plan_output_path = _plan_output_path(args)
    raw_response_output_path: Path | None = None
    model_response_text: str | None = None

    try:
        if not errors:
            registry = load_registry(args.registry)
            errors.extend(validate_registry(registry))

        if not errors:
            if args.planner == "template":
                plan = build_linear_plan(
                    args.task,
                    registry,
                    explicit_robot_postcondition_gates=args.explicit_postcondition_gates,
                )
                errors.extend(validate_linear_plan(plan, registry, args.executor_yaml))
            elif args.planner == "model-response":
                if args.model_response_file is None:
                    errors.append("--planner model-response requires --model-response-file.")
                    plan = None
                else:
                    model_response_text = args.model_response_file.read_text(encoding="utf-8")
                    raw_response_output_path = _raw_response_output_path(args, model_response_text)
                    plan = canonicalize_plan(parse_planner_response(model_response_text), registry)
                    if plan["task_name"] != args.task:
                        errors.append(
                            f"Planner response task_name {plan['task_name']!r} does not match requested "
                            f"task_name {args.task!r}."
                        )
                    else:
                        errors.extend(
                            validate_linear_plan(
                                plan,
                                registry,
                                args.executor_yaml,
                                strict_generated=True,
                            )
                        )
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
                    plan = None
                else:
                    raw_response_output_path = _raw_response_output_path(args, model_response_text or "")
                    plan = canonicalize_plan(parse_planner_response(model_response_text), registry)
                    if plan["task_name"] != args.task:
                        errors.append(
                            f"Planner response task_name {plan['task_name']!r} does not match requested "
                            f"task_name {args.task!r}."
                        )
                    else:
                        errors.extend(
                            validate_linear_plan(
                                plan,
                                registry,
                                args.executor_yaml,
                                strict_generated=True,
                            )
                        )
        else:
            plan = None
    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))
        plan = None

    if errors or plan is None:
        if raw_response_output_path is not None and model_response_text is not None:
            _write_text(raw_response_output_path, model_response_text)
        _print_errors(errors)
        return 1

    try:
        xml_text = render_xml(plan, registry)
        yaml_text = render_bt_params_yaml(plan, registry)
        errors.extend(validate_xml_yaml_blackboard_text(xml_text, yaml_text))
    except Exception as exc:  # noqa: BLE001
        _print_errors([str(exc)])
        return 1

    if errors:
        _print_errors(errors)
        return 1

    assert out_tree is not None
    assert out_config is not None
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


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _print_errors(errors: list[str]) -> None:
    print("BT generation failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
