"""BehaviorTree.CPP XML and ROS2 BT parameter renderers."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import yaml

from .registry import HUMAN_STEP, ROBOT_SKILL, VLM_GATE, Registry
from .validator import validate_linear_plan


def render_xml(plan: dict, registry: Registry) -> str:
    """Render a validated Linear IR plan as BehaviorTree.CPP XML."""

    errors = validate_linear_plan(plan, registry)
    if errors:
        raise ValueError("Cannot render invalid plan:\n" + "\n".join(f"- {error}" for error in errors))

    root = ET.Element("root", {"BTCPP_format": "4", "main_tree_to_execute": "MainTree"})
    behavior_tree = ET.SubElement(root, "BehaviorTree", {"ID": "MainTree"})
    sequence = ET.SubElement(
        behavior_tree,
        "Sequence",
        {"name": _human_label(str(plan["task_name"]))},
    )

    for step in plan["steps"]:
        _append_step_xml(sequence, step, registry)

    nodes_model = ET.SubElement(root, "TreeNodesModel")
    await_scene = ET.SubElement(nodes_model, "Action", {"ID": "AwaitScene"})
    ET.SubElement(await_scene, "input_port", {"name": "scene_name"})
    do_skill = ET.SubElement(nodes_model, "Action", {"ID": "DoSkill"})
    ET.SubElement(do_skill, "input_port", {"name": "skill_name"})
    ET.SubElement(do_skill, "input_port", {"name": "timeout_s"})

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode") + "\n"


def render_bt_params_yaml(plan: dict, registry: Registry) -> str:
    """Render ROS2 parameters consumed by the existing C++ BT blackboard loader."""

    errors = validate_linear_plan(plan, registry)
    if errors:
        raise ValueError("Cannot render invalid plan:\n" + "\n".join(f"- {error}" for error in errors))

    bt_params: dict[str, object] = {}
    for step in plan["steps"]:
        kind = step["kind"]
        name = step["name"]
        key = param_key(name)
        entry = registry.get(kind, name)

        if kind == ROBOT_SKILL:
            bt_params[f"{key}_skill"] = name
            bt_params[f"{key}_timeout_s"] = float(entry.timeout_s)
            bt_params[f"{key}_max_attempts"] = int(entry.max_attempts)
        elif kind == HUMAN_STEP:
            bt_params[f"{key}_gate"] = name
            bt_params[f"{key}_instruction"] = entry.instruction
            bt_params[f"{key}_timeout_s"] = float(entry.timeout_s)
            bt_params[f"{key}_max_attempts"] = int(entry.max_attempts)
        elif kind == VLM_GATE:
            bt_params[f"{key}_gate"] = name
            bt_params[f"{key}_task"] = entry.task
            bt_params[f"{key}_timeout_s"] = float(entry.timeout_s)
            bt_params[f"{key}_max_attempts"] = int(entry.max_attempts)

    config = {
        "lerobot_bt_runner": {
            "ros__parameters": {
                "bt": bt_params,
            },
        },
    }
    return yaml.safe_dump(config, sort_keys=False)


def param_key(name: str) -> str:
    """Return a stable BT blackboard key stem for a registry name."""

    key = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_")
    if not key:
        raise ValueError("Cannot build a parameter key from an empty name.")
    if key[0].isdigit():
        key = f"step_{key}"
    return key


def _append_step_xml(parent: ET.Element, step: dict[str, str], registry: Registry) -> None:
    kind = step["kind"]
    name = step["name"]
    key = param_key(name)
    entry = registry.get(kind, name)

    retry = ET.SubElement(
        parent,
        "RetryUntilSuccessful",
        {
            "name": _retry_label(kind, name),
            "num_attempts": str(_retry_num_attempts_literal(kind, entry)),
        },
    )
    if kind == ROBOT_SKILL:
        ET.SubElement(
            retry,
            "DoSkill",
            {
                "name": _human_label(name),
                "skill_name": f"{{{key}_skill}}",
                "timeout_s": f"{{{key}_timeout_s}}",
            },
        )
    elif kind == HUMAN_STEP:
        ET.SubElement(
            retry,
            "AwaitScene",
            {
                "name": f"Human step: {_human_label(name)}",
                "scene_name": f"{{{key}_gate}}",
            },
        )
    elif kind == VLM_GATE:
        ET.SubElement(
            retry,
            "AwaitScene",
            {
                "name": _human_label(name),
                "scene_name": f"{{{key}_gate}}",
            },
        )


def _retry_num_attempts_literal(kind: str, entry: object) -> int:
    if kind == ROBOT_SKILL:
        raw_value = getattr(entry, "max_attempts", None)
    elif kind == HUMAN_STEP:
        raw_value = getattr(entry, "max_attempts", None)
    elif kind == VLM_GATE:
        raw_value = getattr(entry, "max_attempts", None)
    else:
        raw_value = None

    try:
        attempts = int(raw_value) if raw_value is not None else 1
    except (TypeError, ValueError):
        return 1

    return attempts if attempts > 0 else 1


def _retry_label(kind: str, name: str) -> str:
    if kind == ROBOT_SKILL:
        prefix = "Robot skill"
    elif kind == HUMAN_STEP:
        prefix = "Human step"
    else:
        prefix = "VLM gate"
    return f"{prefix}: {_human_label(name)}"


def _human_label(value: str) -> str:
    return value.replace(".", " ").replace("_", " ").strip().capitalize()
