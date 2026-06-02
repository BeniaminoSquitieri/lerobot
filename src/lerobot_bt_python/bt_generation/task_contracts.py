"""Load canonical task-order contracts for runtime BT generation.

This module is part of the real robot generation boundary and is read before
planning and validation. Its main input is task_templates.yaml; its outputs are
normalized canonical task sequences and approved variants used across planner,
validator, and planner-registry export. Do not weaken the schema or reorder the
canonical sequence implicitly, because downstream strict validation depends on
these contracts being stable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .registry import ALLOWED_KINDS

TASK_CONTRACTS_PATH = Path(__file__).with_name("task_templates.yaml")
_ALLOWED_STEP_FIELDS = frozenset(("kind", "name"))


def load_task_contracts(
    path: Path | str | None = None,
) -> tuple[dict[str, list[dict[str, str]]], dict[str, list[dict[str, Any]]]]:
    """Load canonical task templates and approved variants from YAML."""

    contract_path = Path(path) if path is not None else TASK_CONTRACTS_PATH
    data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{contract_path} must contain a YAML mapping.")

    raw_templates = data.get("task_templates")
    if not isinstance(raw_templates, dict) or not raw_templates:
        raise ValueError(f"{contract_path}:task_templates must be a non-empty mapping.")

    task_templates: dict[str, list[dict[str, str]]] = {}
    for raw_task_name, raw_steps in raw_templates.items():
        task_name = _normalize_task_name(raw_task_name, contract_path, "task_templates")
        task_templates[task_name] = _normalize_steps(
            raw_steps,
            contract_path,
            f"task_templates.{task_name}",
        )

    raw_allowed_variants = data.get("allowed_variants", {}) or {}
    if not isinstance(raw_allowed_variants, dict):
        raise ValueError(f"{contract_path}:allowed_variants must be a mapping when present.")

    allowed_variants: dict[str, list[dict[str, Any]]] = {}
    for raw_task_name, raw_variants in raw_allowed_variants.items():
        task_name = _normalize_task_name(raw_task_name, contract_path, "allowed_variants")
        if not isinstance(raw_variants, list):
            raise ValueError(f"{contract_path}:allowed_variants.{task_name} must be a list.")

        normalized_variants: list[dict[str, Any]] = []
        for index, raw_variant in enumerate(raw_variants):
            if not isinstance(raw_variant, dict):
                raise ValueError(
                    f"{contract_path}:allowed_variants.{task_name}[{index}] must be a mapping."
                )

            variant = dict(raw_variant)
            if "steps" in variant:
                variant["steps"] = _normalize_steps(
                    variant["steps"],
                    contract_path,
                    f"allowed_variants.{task_name}[{index}].steps",
                )
            normalized_variants.append(variant)

        allowed_variants[task_name] = normalized_variants

    return task_templates, allowed_variants


def _normalize_task_name(raw_value: object, contract_path: Path, field_name: str) -> str:
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise ValueError(f"{contract_path}:{field_name} keys must be non-empty strings.")
    return raw_value.strip()


def _normalize_steps(
    raw_steps: object,
    contract_path: Path,
    field_name: str,
) -> list[dict[str, str]]:
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ValueError(f"{contract_path}:{field_name} must be a non-empty list.")

    steps: list[dict[str, str]] = []
    for index, raw_step in enumerate(raw_steps):
        if not isinstance(raw_step, dict):
            raise ValueError(f"{contract_path}:{field_name}[{index}] must be a mapping.")

        extra_fields = sorted(set(raw_step) - _ALLOWED_STEP_FIELDS)
        if extra_fields:
            raise ValueError(
                f"{contract_path}:{field_name}[{index}] contains unsupported fields "
                f"{extra_fields}."
            )

        kind = raw_step.get("kind")
        name = raw_step.get("name")
        if kind not in ALLOWED_KINDS:
            raise ValueError(f"{contract_path}:{field_name}[{index}].kind {kind!r} is not allowed.")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"{contract_path}:{field_name}[{index}].name must be a non-empty string."
            )

        steps.append({"kind": kind, "name": name.strip()})

    return steps


TASK_TEMPLATES, TASK_ALLOWED_VARIANTS = load_task_contracts()