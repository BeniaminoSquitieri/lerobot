"""Validation for generated Linear IR plans."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .registry import (
    ALLOWED_KINDS,
    HUMAN_STEP,
    INFINITE_RETRY_ATTEMPTS,
    ROBOT_SKILL,
    VLM_GATE,
    Registry,
    RegistryEntry,
    is_valid_max_attempts,
)
from .task_contracts import TASK_ALLOWED_VARIANTS, TASK_TEMPLATES

FORBIDDEN_STEP_KINDS = {
    "skill",
    "fallback",
    "parallel",
    "human_fallback",
    "raw_xml",
    "condition",
}
FORBIDDEN_STEP_FIELDS = {
    "action",
    "condition",
    "explanation",
    "fallback",
    "free_text",
    "human_fallback",
    "parallel",
    "raw_xml",
    "xml",
}
STRICT_ALLOWED_PLAN_FIELDS = {"task_name", "steps"}
STRICT_ALLOWED_STEP_FIELDS = {"kind", "name", "object", "objects"}


def validate_linear_plan(
    plan: dict,
    registry: Registry,
    executor_yaml_path: Path | None = None,
    *,
    strict_generated: bool = False,
) -> list[str]:
    """Return all plan validation errors; an empty list means valid."""

    errors: list[str] = []
    executor_context = _load_executor_context(executor_yaml_path) if executor_yaml_path else None

    if not isinstance(plan, dict):
        return ["plan must be a dictionary."]
    if strict_generated:
        unexpected_plan_fields = sorted(set(plan) - STRICT_ALLOWED_PLAN_FIELDS)
        if unexpected_plan_fields:
            errors.append(f"plan contains unsupported strict fields {unexpected_plan_fields}.")
    if not plan.get("task_name"):
        errors.append("plan.task_name must be present and non-empty.")
    elif strict_generated and not isinstance(plan.get("task_name"), str):
        errors.append("plan.task_name must be a string.")

    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("plan.steps must be a non-empty list.")
        return errors

    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"plan.steps[{index}] must be a dictionary.")
            continue
        if strict_generated:
            unexpected_fields = sorted(set(step) - STRICT_ALLOWED_STEP_FIELDS)
            if unexpected_fields:
                errors.append(
                    f"plan.steps[{index}] contains unsupported strict fields "
                    f"{unexpected_fields}."
                )
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
        if strict_generated:
            errors.extend(_validate_step_object(step, registry, index))

    if not strict_generated:
        errors.extend(_validate_verify_after_adjacency(steps, registry))
    if strict_generated:
        errors.extend(_validate_canonical_task_sequence(plan, steps))
        errors.extend(_validate_make_sandwich_strict_rules(plan, steps))
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
        if (
            entry.name in executor_context["vlm_gate_tasks"]
            and entry.name not in executor_context["skill_names"]
        ):
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
    if not is_valid_max_attempts(entry.max_attempts):
        errors.append(
            f"{entry.kind} {entry.name!r} max_attempts must be "
            f"{INFINITE_RETRY_ATTEMPTS} for infinite retries or a positive integer."
        )
    return errors


def _validate_step_object(step: dict[str, Any], registry: Registry, index: int) -> list[str]:
    errors: list[str] = []
    name = step.get("name")
    object_values: list[Any] = []

    if "object" in step:
        object_value = step["object"]
        if not isinstance(object_value, str) or not object_value.strip():
            errors.append(f"plan.steps[{index}].object must be a non-empty string.")
        else:
            object_values.append(object_value)

    if "objects" in step:
        objects_value = step["objects"]
        if not isinstance(objects_value, list) or not objects_value:
            errors.append(f"plan.steps[{index}].objects must be a non-empty list.")
        else:
            for obj in objects_value:
                if not isinstance(obj, str) or not obj.strip():
                    errors.append(f"plan.steps[{index}].objects entries must be non-empty strings.")
                else:
                    object_values.append(obj)

    for raw_object in object_values:
        canonical_name = raw_object.strip()
        obj = registry.objects.get(canonical_name)
        if obj is None:
            errors.append(f"plan.steps[{index}] object {canonical_name!r} is not registered.")
            continue
        if isinstance(name, str) and obj.allowed_for and name not in obj.allowed_for:
            errors.append(
                f"plan.steps[{index}] object {canonical_name!r} is not allowed for step "
                f"{name!r}."
            )

    return errors


def _validate_canonical_task_sequence(plan: dict, steps: list[Any]) -> list[str]:
    task_name = plan.get("task_name")
    if not isinstance(task_name, str) or task_name not in TASK_TEMPLATES:
        return []

    allowed_sequences = _allowed_task_sequence_signatures(task_name)
    got = _task_sequence_signature(steps)

    if got in allowed_sequences:
        return []
    expected = allowed_sequences[0]
    return [
        f"Generated plan does not match canonical task sequence for '{task_name}'. "
        f"Expected: {expected}. Got: {got}."
    ]


def _allowed_task_sequence_signatures(task_name: str) -> list[list[tuple[Any, Any]]]:
    signatures = [_task_sequence_signature(TASK_TEMPLATES[task_name])]
    for variant in TASK_ALLOWED_VARIANTS.get(task_name, []):
        variant_steps = _explicit_variant_steps(variant)
        if variant_steps is not None:
            signatures.append(_task_sequence_signature(variant_steps))
    return signatures


def _explicit_variant_steps(variant: dict) -> list[Any] | None:
    steps = variant.get("steps")
    if isinstance(steps, list) and steps:
        return steps
    return None


def _task_sequence_signature(steps: list[Any]) -> list[tuple[Any, Any]]:
    signature: list[tuple[Any, Any]] = []
    for step in steps:
        if isinstance(step, dict):
            signature.append((step.get("kind"), step.get("name")))
        else:
            signature.append(("<invalid>", "<invalid>"))
    return signature


def _validate_make_sandwich_strict_rules(plan: dict, steps: list[Any]) -> list[str]:
    if plan.get("task_name") != "make_sandwich":
        return []

    errors: list[str] = []
    initial_step = {"kind": VLM_GATE, "name": "initial_scene_ready"}
    final_step = {"kind": VLM_GATE, "name": "make_sandwich.task_complete"}
    if steps[0] != initial_step:
        errors.append("make_sandwich must start with vlm_gate 'initial_scene_ready'.")
    if steps[-1] != final_step:
        errors.append("make_sandwich must finish with vlm_gate 'make_sandwich.task_complete'.")

    normalized_steps = [
        step
        for step in steps
        if isinstance(step, dict)
        and step.get("kind") in ALLOWED_KINDS
        and isinstance(step.get("name"), str)
    ]
    for index, step in enumerate(normalized_steps):
        kind = step["kind"]
        name = step["name"]
        if name == "pour_ingredient" and kind != HUMAN_STEP:
            errors.append("make_sandwich step 'pour_ingredient' must be a human_step.")
        if name == "place_first_toast" and kind != ROBOT_SKILL:
            errors.append("make_sandwich step 'place_first_toast' must be a robot_skill.")
        if name == "place_second_toast" and kind != ROBOT_SKILL:
            errors.append("make_sandwich step 'place_second_toast' must be a robot_skill.")
        if name == "place_second_toast" and not _has_prior_gate(
            normalized_steps,
            index,
            "second_toast_ready",
        ):
            errors.append(
                "make_sandwich robot_skill 'place_second_toast' must be preceded by "
                "vlm_gate 'second_toast_ready'."
            )
        if name == "pour_ingredient" and not _has_later_gate_before_task_end(
            normalized_steps,
            index,
            "ingredient_poured",
        ):
            errors.append(
                "make_sandwich human_step 'pour_ingredient' must be followed later by "
                "vlm_gate 'ingredient_poured' before task completion."
            )

    return errors


def _has_prior_gate(steps: list[dict[str, Any]], before_index: int, name: str) -> bool:
    return any(
        step.get("kind") == VLM_GATE and step.get("name") == name
        for step in steps[:before_index]
    )


def _has_later_gate_before_task_end(steps: list[dict[str, Any]], after_index: int, name: str) -> bool:
    for step in steps[after_index + 1 :]:
        if step.get("kind") == VLM_GATE and step.get("name") == "make_sandwich.task_complete":
            return False
        if step.get("kind") == VLM_GATE and step.get("name") == name:
            return True
    return False


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
