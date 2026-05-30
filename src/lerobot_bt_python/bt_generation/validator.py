"""Validation for generated Linear IR plans."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .registry import ALLOWED_KINDS, HUMAN_STEP, ROBOT_SKILL, VLM_GATE, Registry, RegistryEntry

FORBIDDEN_STEP_KINDS = {
    "skill",
    "fallback",
    "parallel",
    "human_fallback",
    "raw_xml",
    "condition",
}
FORBIDDEN_STEP_FIELDS = {"fallback", "parallel", "human_fallback", "raw_xml", "condition"}


def validate_linear_plan(
    plan: dict,
    registry: Registry,
    executor_yaml_path: Path | None = None,
) -> list[str]:
    """Return all plan validation errors; an empty list means valid."""

    errors: list[str] = []
    executor_context = _load_executor_context(executor_yaml_path) if executor_yaml_path else None

    if not isinstance(plan, dict):
        return ["plan must be a dictionary."]
    if not plan.get("task_name"):
        errors.append("plan.task_name must be present and non-empty.")

    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("plan.steps must be a non-empty list.")
        return errors

    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"plan.steps[{index}] must be a dictionary.")
            continue
        forbidden_fields = sorted(FORBIDDEN_STEP_FIELDS.intersection(step))
        if forbidden_fields:
            errors.append(f"plan.steps[{index}] contains forbidden fields {forbidden_fields}.")

        kind = step.get("kind")
        name = step.get("name")
        if kind in FORBIDDEN_STEP_KINDS:
            errors.append(f"plan.steps[{index}] uses forbidden kind {kind!r}.")
        if kind not in ALLOWED_KINDS:
            errors.append(f"plan.steps[{index}].kind {kind!r} is not allowed.")
            continue
        if not isinstance(name, str) or not name:
            errors.append(f"plan.steps[{index}].name must be a non-empty string.")
            continue

        actual_kind = registry.kind_for_name(name)
        if actual_kind is None:
            errors.append(f"{kind} step {name!r} is not present in the registry.")
            continue
        if actual_kind == "ambiguous":
            errors.append(f"step {name!r} is ambiguous in the registry.")
            continue
        if actual_kind != kind:
            errors.append(f"step {name!r} is {actual_kind!r} in the registry, not {kind!r}.")
            continue

        entry = registry.get(kind, name)
        if kind == ROBOT_SKILL:
            errors.extend(_validate_robot_skill(entry, executor_context))
        elif kind == HUMAN_STEP:
            errors.extend(_validate_human_step(entry, executor_context))
        elif kind == VLM_GATE:
            errors.extend(_validate_vlm_gate(entry, executor_context))

    errors.extend(_validate_verify_after_adjacency(steps, registry))
    return errors


def _load_executor_context(executor_yaml_path: Path | None) -> dict[str, Any] | None:
    if executor_yaml_path is None:
        return None
    data = yaml.safe_load(Path(executor_yaml_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{executor_yaml_path} must contain a YAML mapping.")

    skill_names = {
        str(skill.get("name", ""))
        for skill in data.get("skills", [])
        if isinstance(skill, dict)
    }
    expected_skill_names = {str(name) for name in data.get("expected_skill_names", [])}
    has_vlm_gate_tasks = "vlm_gate_tasks" in data
    vlm_gate_tasks = data.get("vlm_gate_tasks", {}) or {}
    if not isinstance(vlm_gate_tasks, dict):
        raise ValueError(f"{executor_yaml_path}:vlm_gate_tasks must be a mapping when present.")

    return {
        "skill_names": skill_names,
        "expected_skill_names": expected_skill_names,
        "has_vlm_gate_tasks": has_vlm_gate_tasks,
        "vlm_gate_tasks": {str(name): str(task) for name, task in vlm_gate_tasks.items()},
    }


def _validate_robot_skill(entry: RegistryEntry, executor_context: dict[str, Any] | None) -> list[str]:
    errors = _validate_runtime_bounds(entry)
    if executor_context is not None:
        real_skill_names = executor_context["skill_names"] | executor_context["expected_skill_names"]
        if entry.name not in real_skill_names:
            errors.append(
                f"robot_skill {entry.name!r} is not listed in executor YAML skills or "
                "expected_skill_names."
            )
        if entry.name in executor_context["vlm_gate_tasks"] and entry.name not in executor_context["skill_names"]:
            errors.append(f"robot_skill {entry.name!r} appears only as a VLM gate/manual task.")
    return errors


def _validate_human_step(entry: RegistryEntry, executor_context: dict[str, Any] | None) -> list[str]:
    errors = _validate_runtime_bounds(entry)
    if not entry.instruction.strip():
        errors.append(f"human_step {entry.name!r} must have a non-empty instruction.")
    if entry.verify_after is not None and not entry.verify_after.strip():
        errors.append(f"human_step {entry.name!r} verify_after must be null or a non-empty string.")
    if executor_context is not None and executor_context["has_vlm_gate_tasks"]:
        if entry.name not in executor_context["vlm_gate_tasks"]:
            errors.append(
                f"human_step {entry.name!r} is rendered with AwaitScene but is missing from "
                "executor YAML vlm_gate_tasks."
            )
    return errors


def _validate_vlm_gate(entry: RegistryEntry, executor_context: dict[str, Any] | None) -> list[str]:
    errors = _validate_runtime_bounds(entry)
    if not entry.task.strip():
        errors.append(f"vlm_gate {entry.name!r} must have a non-empty task.")
    if executor_context is not None and executor_context["has_vlm_gate_tasks"]:
        if entry.name not in executor_context["vlm_gate_tasks"]:
            errors.append(f"vlm_gate {entry.name!r} is missing from executor YAML vlm_gate_tasks.")
    return errors


def _validate_runtime_bounds(entry: RegistryEntry) -> list[str]:
    errors: list[str] = []
    if entry.timeout_s <= 0.0:
        errors.append(f"{entry.kind} {entry.name!r} timeout_s must be > 0.")
    if not 1 <= entry.max_attempts <= 5:
        errors.append(f"{entry.kind} {entry.name!r} max_attempts must be within [1, 5].")
    return errors


def _validate_verify_after_adjacency(steps: list[Any], registry: Registry) -> list[str]:
    errors: list[str] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        kind = step.get("kind")
        name = step.get("name")
        if kind != HUMAN_STEP or not isinstance(name, str):
            continue
        if registry.kind_for_name(name) != kind:
            continue
        verify_after = registry.get(kind, name).verify_after
        if verify_after is None:
            continue
        next_step = steps[index + 1] if index + 1 < len(steps) else None
        if next_step != {"kind": VLM_GATE, "name": verify_after}:
            errors.append(
                f"{kind} {name!r} must be followed immediately by verify_after gate "
                f"{verify_after!r}."
            )
    return errors
