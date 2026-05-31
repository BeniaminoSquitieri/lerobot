"""Export a filtered planner registry payload for a given task."""
import argparse
import json
import sys
from pathlib import Path

from .planner import TASK_TEMPLATES
from .registry import load_registry, HUMAN_STEP, ROBOT_SKILL, VLM_GATE

def build_planner_registry_payload(task_name: str, registry) -> dict:
    if task_name not in TASK_TEMPLATES:
        raise ValueError(f"Unknown task: {task_name}")
    steps = TASK_TEMPLATES[task_name]
    robot_skills = []
    human_steps = []
    vlm_gates = []
    for step in steps:
        kind = step["kind"]
        name = step["name"]
        actual_kind = registry.kind_for_name(name)
        if actual_kind is None:
            raise ValueError(f"{name!r} is not present in registry")
        if actual_kind != kind:
            raise ValueError(f"{name!r} kind mismatch: template={kind}, registry={actual_kind}")
        if kind == ROBOT_SKILL:
            entry = registry.robot_skills[name]
            robot_skills.append({
                "name": entry.name,
                "kind": entry.kind,
                "timeout_s": getattr(entry, "timeout_s", None),
                "max_attempts": getattr(entry, "max_attempts", None),
            })
        elif kind == HUMAN_STEP:
            entry = registry.human_steps[name]
            human_steps.append({
                "name": entry.name,
                "kind": entry.kind,
                "instruction": getattr(entry, "instruction", ""),
            })
        elif kind == VLM_GATE:
            entry = registry.vlm_gates[name]
            vlm_gates.append({
                "name": entry.name,
                "kind": entry.kind,
                "task": getattr(entry, "task", None),
            })
    payload = {
        "task_name": task_name,
        "robot_skills": robot_skills,
        "human_steps": human_steps,
        "vlm_gates": vlm_gates,
        "rules": {
            "return_json_only": True,
            "no_xml": True,
            "registered_names_only": True,
            "do_not_change_step_kinds": True,
        },
    }
    # Optionally include objects/aliases if present
    if hasattr(registry, "objects") and registry.objects:
        payload["objects"] = [
            {
                "canonical_name": obj.canonical_name,
                "aliases": list(obj.aliases),
                "allowed_for": list(obj.allowed_for),
            }
            for obj in registry.objects.values()
        ]
    return payload

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    registry = load_registry(args.registry)
    payload = build_planner_registry_payload(args.task, registry)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Exported planner registry for {args.task} to {args.out}")

if __name__ == "__main__":
    main()
