"""Deterministic Linear IR builder for canonical runtime tasks.

This module is used in the safe generation path when planner mode is template.
It converts a known task name plus the validated registry into repo-owned
Linear IR JSON, including required verification gates from the task contract.
The output is a plan candidate for validator.py, not executable BT XML. Do not
treat this file as the source of truth for task ordering; task_contracts.py is.
"""

from __future__ import annotations

from .registry import HUMAN_STEP, ROBOT_SKILL, VLM_GATE, Registry
from .task_contracts import TASK_ALLOWED_VARIANTS, TASK_TEMPLATES


def build_linear_plan(
    task_name: str,
    registry: Registry,
    *,
    explicit_robot_postcondition_gates: bool = False,
) -> dict:
    """Build a deterministic Linear IR plan for a known task name."""

    if task_name not in TASK_TEMPLATES:
        known = ", ".join(sorted(TASK_TEMPLATES))
        raise ValueError(f"Unknown task_name {task_name!r}. Known tasks: {known}.")

    template = TASK_TEMPLATES[task_name]
    steps: list[dict[str, str]] = []
    for index, step in enumerate(template):
        kind = step["kind"]
        name = step["name"]
        _require_registry_match(registry, kind, name)
        steps.append({"kind": kind, "name": name})

        if kind not in {ROBOT_SKILL, HUMAN_STEP}:
            continue
        if kind == ROBOT_SKILL and not explicit_robot_postcondition_gates:
            _validate_verify_after_target(registry, kind, name)
            continue

        verify_after = registry.get(kind, name).verify_after
        if not verify_after:
            continue
        _require_registry_match(registry, VLM_GATE, verify_after)

        next_step = template[index + 1] if index + 1 < len(template) else None
        if next_step == {"kind": VLM_GATE, "name": verify_after}:
            continue
        steps.append({"kind": VLM_GATE, "name": verify_after})

    return {"task_name": task_name, "steps": steps}


def _validate_verify_after_target(registry: Registry, kind: str, name: str) -> None:
    verify_after = registry.get(kind, name).verify_after
    if verify_after:
        _require_registry_match(registry, VLM_GATE, verify_after)


def _require_registry_match(registry: Registry, kind: str, name: str) -> None:
    actual_kind = registry.kind_for_name(name)
    if actual_kind is None:
        raise ValueError(f"{name!r} is not present in the BT generation registry.")
    if actual_kind == "ambiguous":
        raise ValueError(f"{name!r} is ambiguous in the BT generation registry.")
    if actual_kind != kind:
        raise ValueError(
            f"Template classifies {name!r} as {kind!r}, but the registry classifies it "
            f"as {actual_kind!r}."
        )
