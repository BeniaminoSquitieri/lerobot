"""Export a filtered planner registry payload for a given task."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .manifest import sha256_text
from .registry import HUMAN_STEP, ROBOT_SKILL, VLM_GATE, Registry, RegistryEntry, load_registry
from .task_contracts import TASK_ALLOWED_VARIANTS, TASK_TEMPLATES


DERIVED_CONTRACT_FIELDS = frozenset(
    (
        "registry_contract_hash",
        "task_template_hash",
    )
)


def build_planner_registry_payload(task_name: str, registry: Registry) -> dict:
    """Build the constrained payload sent to a planner/VLM service."""

    if task_name not in TASK_TEMPLATES:
        raise ValueError(f"Unknown task: {task_name}")

    canonical_task_sequence = [dict(step) for step in TASK_TEMPLATES[task_name]]
    robot_skills: list[dict] = []
    human_steps: list[dict] = []
    vlm_gates: list[dict] = []

    for step in canonical_task_sequence:
        kind = step["kind"]
        name = step["name"]
        actual_kind = registry.kind_for_name(name)
        if actual_kind is None:
            raise ValueError(f"{name!r} is not present in registry")
        if actual_kind != kind:
            raise ValueError(f"{name!r} kind mismatch: template={kind}, registry={actual_kind}")
        if kind == ROBOT_SKILL:
            entry = registry.robot_skills[name]
            robot_skills.append(_robot_skill_payload(entry))
        elif kind == HUMAN_STEP:
            entry = registry.human_steps[name]
            human_steps.append(_human_step_payload(entry))
        elif kind == VLM_GATE:
            entry = registry.vlm_gates[name]
            vlm_gates.append(_vlm_gate_payload(entry))

    payload = {
        "task_name": task_name,
        "canonical_task_sequence": canonical_task_sequence,
        "ordering_constraints": _ordering_constraints(canonical_task_sequence),
        "robot_skills": robot_skills,
        "human_steps": human_steps,
        "vlm_gates": vlm_gates,
        "rules": {
            "return_json_only": True,
            "no_xml": True,
            "registered_names_only": True,
            "do_not_change_step_kinds": True,
            "follow_canonical_task_sequence": True,
            "do_not_reorder_steps": True,
            "do_not_add_steps": True,
            "do_not_remove_steps": True,
        },
    }

    step_names = {step["name"] for step in canonical_task_sequence}
    task_objects = [
        obj
        for obj in registry.objects.values()
        if any(name in step_names for name in obj.allowed_for)
    ]
    if task_objects:
        payload["objects"] = [
            {
                "canonical_name": obj.canonical_name,
                "aliases": list(obj.aliases),
                "allowed_for": list(obj.allowed_for),
            }
            for obj in task_objects
        ]
    allowed_variants = TASK_ALLOWED_VARIANTS.get(task_name, [])
    if allowed_variants:
        payload["allowed_variants"] = allowed_variants
    payload["contract_schema_version"] = 1
    payload["task_template_hash"] = _stable_json_sha256(canonical_task_sequence)
    payload["registry_contract_hash"] = _stable_json_sha256(_registry_contract_payload(payload))
    return payload


def _robot_skill_payload(entry: RegistryEntry) -> dict:
    return {
        "name": entry.name,
        "kind": entry.kind,
        "timeout_s": entry.timeout_s,
        "max_attempts": entry.max_attempts,
    }


def _human_step_payload(entry: RegistryEntry) -> dict:
    return {
        "name": entry.name,
        "kind": entry.kind,
        "instruction": entry.instruction,
    }


def _vlm_gate_payload(entry: RegistryEntry) -> dict:
    return {
        "name": entry.name,
        "kind": entry.kind,
        "task": entry.task,
    }


def _ordering_constraints(steps: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {"before": current["name"], "after": following["name"]}
        for current, following in zip(steps, steps[1:])
    ]


def _stable_json_sha256(value: object) -> str:
    return sha256_text(json.dumps(value, sort_keys=True))


def _registry_contract_payload(payload: dict) -> dict:
    return {key: value for key, value in payload.items() if key not in DERIVED_CONTRACT_FIELDS}


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a constrained planner registry payload.")
    parser.add_argument("--task", required=True, help="Known task name.")
    parser.add_argument("--registry", required=True, type=Path, help="skills_registry.yaml path.")
    parser.add_argument("--out", required=True, type=Path, help="Output JSON path.")
    args = parser.parse_args()
    registry = load_registry(args.registry)
    payload = build_planner_registry_payload(args.task, registry)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Exported planner registry for {args.task} to {args.out}")


if __name__ == "__main__":
    main()
