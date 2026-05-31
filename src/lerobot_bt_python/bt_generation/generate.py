"""CLI for deterministic runtime BT generation."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from .planner import build_linear_plan
from .registry import load_registry, validate_registry
from .renderer import render_bt_params_yaml, render_xml
from .static_checks import validate_xml_yaml_blackboard_text
from .validator import validate_linear_plan
from .vlm_planner import generate_plan_from_model_response


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic BT XML/YAML pair.")
    parser.add_argument("--task", required=True, help="Known deterministic task name.")
    parser.add_argument(
        "--planner",
        choices=("template", "model-response"),
        default="template",
        help="Planner source. template is deterministic; model-response reads Linear IR JSON.",
    )
    parser.add_argument(
        "--model-response-file",
        type=Path,
        help="Path to a pre-generated model Linear IR JSON response.",
    )
    parser.add_argument("--registry", required=True, type=Path, help="skills_registry.yaml path.")
    parser.add_argument("--executor-yaml", type=Path, help="Executor YAML used for consistency checks.")
    parser.add_argument("--out-tree", required=True, type=Path, help="Output BehaviorTree.CPP XML path.")
    parser.add_argument("--out-config", required=True, type=Path, help="Output BT params YAML path.")
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
    try:
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
                    plan = generate_plan_from_model_response(
                        args.task,
                        registry,
                        model_response_text,
                    )
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

    args.out_tree.parent.mkdir(parents=True, exist_ok=True)
    args.out_config.parent.mkdir(parents=True, exist_ok=True)
    args.out_tree.write_text(xml_text, encoding="utf-8")
    args.out_config.write_text(yaml_text, encoding="utf-8")

    counts = Counter(step["kind"] for step in plan["steps"])
    print(f"task_name: {plan['task_name']}")
    print(f"robot_skill: {counts.get('robot_skill', 0)}")
    print(f"human_step: {counts.get('human_step', 0)}")
    print(f"vlm_gate: {counts.get('vlm_gate', 0)}")
    print(f"wrote tree: {args.out_tree}")
    print(f"wrote config: {args.out_config}")
    return 0


def _print_errors(errors: list[str]) -> None:
    print("BT generation failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
