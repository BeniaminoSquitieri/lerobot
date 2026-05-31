"""Constrained model-response planner for Linear IR BT generation."""

from __future__ import annotations

import json
import re
from typing import Any

from .planner import TASK_TEMPLATES
from .registry import HUMAN_STEP, ROBOT_SKILL, VLM_GATE, Registry

XML_TAG_RE = re.compile(r"</?\s*[A-Za-z][A-Za-z0-9_:.-]*(?:\s[^<>]*)?/?>")
FENCED_JSON_RE = re.compile(r"^```([A-Za-z0-9_-]*)[ \t]*\n(.*)\n```[ \t]*$", re.DOTALL)


def build_planner_prompt(
    task_name: str,
    registry: Registry,
    scene_facts: dict[str, Any] | None = None,
) -> str:
    """Build a constrained prompt for a model that may only propose Linear IR JSON."""

    lines = [
        "You are proposing a Behavior Tree plan candidate as Linear IR JSON.",
        f"task_name: {task_name}",
        "",
        "Available robot_skills:",
        *_format_names(registry.robot_skills),
        "",
        "Available human_steps:",
        *_format_names(registry.human_steps),
        "",
        "Available vlm_gates:",
        *_format_names(registry.vlm_gates),
    ]
    if task_name in TASK_TEMPLATES:
        canonical_task_sequence = [dict(step) for step in TASK_TEMPLATES[task_name]]
        ordering_constraints = [
            {"before": current["name"], "after": following["name"]}
            for current, following in zip(canonical_task_sequence, canonical_task_sequence[1:])
        ]
        lines.extend(
            [
                "",
                "canonical_task_sequence JSON:",
                json.dumps(canonical_task_sequence, indent=2),
                "",
                "ordering_constraints JSON:",
                json.dumps(ordering_constraints, indent=2),
                "",
                "Ordering rules:",
                "Follow canonical_task_sequence exactly.",
                "Do not reorder steps.",
                "Do not remove steps.",
                "Do not add steps.",
                "Do not infer order from object names.",
                "Use only kind/name pairs from canonical_task_sequence.",
                (
                    "The returned steps must match canonical_task_sequence exactly unless "
                    "future allowed_variants are explicitly provided."
                ),
            ]
        )
    if scene_facts is not None:
        lines.extend(
            [
                "",
                "scene_facts JSON:",
                json.dumps(scene_facts, indent=2, sort_keys=True),
            ]
        )
    if task_name == "make_sandwich":
        lines.extend(
            [
                "",
                "For make_sandwich, these registered roles are fixed:",
                "- place_first_toast = robot_skill",
                "- place_second_toast = robot_skill",
                "- pour_ingredient = human_step",
                "- ingredient_poured = vlm_gate",
                "- second_toast_ready = vlm_gate",
                "- make_sandwich.task_complete = vlm_gate",
            ]
        )
    lines.extend(
        [
            "",
            "Return JSON only.",
            "Do not return XML.",
            "Do not include explanations.",
            "Do not invent skills.",
            "Use only registered names.",
            "Do not change step kinds.",
            "Use robot_skill only for entries listed under robot_skills.",
            "Use human_step only for entries listed under human_steps.",
            "Use vlm_gate only for entries listed under vlm_gates.",
            "The output must be a JSON object with task_name and steps.",
            "Each step must have kind and name.",
            "Return Linear IR JSON only.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_planner_response(text: str) -> dict[str, Any]:
    """Parse a model response, accepting only a JSON object plan candidate."""

    if not isinstance(text, str):
        raise ValueError("Planner response must be text.")
    stripped = text.strip()
    if not stripped:
        raise ValueError("Planner response is empty.")
    if _contains_xml(stripped):
        raise ValueError("Planner response must be JSON only; XML-like content is not allowed.")

    candidate = _extract_safe_fenced_json(stripped) if stripped.startswith("```") else stripped
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Planner response is not valid JSON: {exc.msg}.") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Planner response JSON must be an object.")
    missing = sorted({"task_name", "steps"} - set(parsed))
    if missing:
        raise ValueError(f"Planner response JSON is missing required field(s): {missing}.")
    return parsed


def canonicalize_plan(
    plan: dict[str, Any],
    registry: Registry,
) -> dict[str, Any]:
    """Trim safe whitespace and canonicalize registered object aliases."""

    if not isinstance(plan, dict):
        raise ValueError("plan must be a dictionary.")

    task_name = plan.get("task_name")
    if not isinstance(task_name, str) or not task_name.strip():
        raise ValueError("plan.task_name must be a non-empty string.")

    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("plan.steps must be a non-empty list.")

    canonical_plan = dict(plan)
    canonical_plan["task_name"] = task_name.strip()
    canonical_steps: list[dict[str, Any]] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"plan.steps[{index}] must be a dictionary.")

        canonical_step = dict(step)
        kind = _required_trimmed_string(canonical_step.get("kind"), f"plan.steps[{index}].kind")
        name = _required_trimmed_string(canonical_step.get("name"), f"plan.steps[{index}].name")
        canonical_step["kind"] = kind
        canonical_step["name"] = name

        actual_kind = registry.kind_for_name(name)
        if actual_kind is None:
            raise ValueError(f"{kind} step {name!r} is not present in the registry.")
        if actual_kind == "ambiguous":
            raise ValueError(f"step {name!r} is ambiguous in the registry.")
        if actual_kind != kind:
            raise ValueError(f"step {name!r} is {actual_kind!r} in the registry, not {kind!r}.")

        if "object" in canonical_step:
            canonical_step["object"] = canonicalize_object_name(canonical_step["object"], registry)
        if "objects" in canonical_step:
            objects = canonical_step["objects"]
            if not isinstance(objects, list):
                raise ValueError(f"plan.steps[{index}].objects must be a list.")
            canonical_step["objects"] = [canonicalize_object_name(obj, registry) for obj in objects]

        object_errors = validate_step_object(canonical_step, registry)
        if object_errors:
            raise ValueError("; ".join(object_errors))
        canonical_steps.append(canonical_step)

    canonical_plan["steps"] = canonical_steps
    return canonical_plan


def generate_plan_from_model_response(
    task_name: str,
    registry: Registry,
    model_response_text: str,
    scene_facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert a pre-generated model response into a canonical Linear IR candidate."""

    _ = scene_facts
    plan = canonicalize_plan(parse_planner_response(model_response_text), registry)
    if plan["task_name"] != task_name:
        raise ValueError(
            f"Planner response task_name {plan['task_name']!r} does not match requested "
            f"task_name {task_name!r}."
        )
    return plan


def canonicalize_object_name(raw: str, registry: Registry) -> str:
    """Return the registered canonical object name for a raw alias."""

    if not isinstance(raw, str):
        raise ValueError("object name must be a string.")
    raw_name = raw.strip()
    if not raw_name:
        raise ValueError("object name must be non-empty.")
    canonical = registry.all_object_aliases.get(raw_name)
    if canonical is None:
        raise ValueError(f"object {raw_name!r} is not registered.")
    return canonical


def validate_step_object(step: dict[str, Any], registry: Registry) -> list[str]:
    """Validate canonical object fields on one model-generated step."""

    errors: list[str] = []
    name = step.get("name")
    object_names: list[str] = []
    if "object" in step:
        obj = step["object"]
        if isinstance(obj, str) and obj.strip():
            object_names.append(obj.strip())
        else:
            errors.append("step.object must be a non-empty string.")
    if "objects" in step:
        objects = step["objects"]
        if not isinstance(objects, list) or not objects:
            errors.append("step.objects must be a non-empty list.")
        else:
            for obj in objects:
                if isinstance(obj, str) and obj.strip():
                    object_names.append(obj.strip())
                else:
                    errors.append("step.objects entries must be non-empty strings.")

    for object_name in object_names:
        obj = registry.objects.get(object_name)
        if obj is None:
            errors.append(f"object {object_name!r} is not registered.")
            continue
        if isinstance(name, str) and obj.allowed_for and name not in obj.allowed_for:
            errors.append(f"object {object_name!r} is not allowed for step {name!r}.")
    return errors


def _format_names(entries: dict[str, Any]) -> list[str]:
    return [f"- {name}" for name in sorted(entries)]


def _contains_xml(text: str) -> bool:
    return bool(XML_TAG_RE.search(text))


def _extract_safe_fenced_json(text: str) -> str:
    match = FENCED_JSON_RE.match(text)
    if match is None:
        raise ValueError("Markdown code fence must contain only a single JSON block.")
    language, body = match.groups()
    if language and language.lower() != "json":
        raise ValueError("Markdown code fence must be marked as json or have no language.")
    body = body.strip()
    if not body:
        raise ValueError("Markdown code fence JSON block is empty.")
    return body


def _required_trimmed_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()
