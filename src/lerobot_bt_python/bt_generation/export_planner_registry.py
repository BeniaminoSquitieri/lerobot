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
        if kind == ROBOT_SKILL and name in registry.robot_skills:
            entry = registry.robot_skills[name]
            robot_skills.append({
                "name": entry.name,
                "kind": entry.kind,
                "timeout_s": getattr(entry, "timeout_s", None),
                "max_attempts": getattr(entry, "max_attempts", None),
            })
        elif kind == HUMAN_STEP and name in registry.human_steps:
            entry = registry.human_steps[name]
            human_steps.append({
                "name": entry.name,
                "kind": entry.kind,
                "instruction": getattr(entry, "instruction", ""),
            })
        elif kind == VLM_GATE and name in registry.vlm_gates:
            entry = registry.vlm_gates[name]
            vlm_gates.append({
                "name": entry.name,
                "kind": entry.kind,
                "task": getattr(entry, "task", None),
            })
        else:
            # fallback for gates not in registry
            if kind == VLM_GATE:
                vlm_gates.append({"name": name, "kind": kind})
            elif kind == HUMAN_STEP:
                human_steps.append({"name": name, "kind": kind, "instruction": ""})
            elif kind == ROBOT_SKILL:
                robot_skills.append({"name": name, "kind": kind})
    payload = {
        "task_name": task_name,
        "robot_skills": robot_skills,
        "human_steps": human_steps,
        "vlm_gates": vlm_gates,
        "rules": [
            "return_json_only",
            "no_xml",
            "registered_names_only",
            "do_not_change_step_kinds",
        ],
    }
    # Optionally include objects/aliases if present
    if hasattr(registry, "objects"):
        payload["objects"] = registry.objects
    if hasattr(registry, "aliases"):
        payload["aliases"] = registry.aliases
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
