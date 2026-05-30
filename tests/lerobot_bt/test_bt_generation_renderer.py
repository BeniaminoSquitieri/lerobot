#!/usr/bin/env python

"""Tests for generated BehaviorTree.CPP XML and BT params YAML."""

from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

import yaml

from lerobot_bt_python.bt_generation.planner import build_linear_plan
from lerobot_bt_python.bt_generation.registry import load_registry
from lerobot_bt_python.bt_generation.renderer import render_bt_params_yaml, render_xml


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/skills_registry.yaml"


def _sandwich_outputs() -> tuple[str, str]:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan("make_sandwich", registry)
    return render_xml(plan, registry), render_bt_params_yaml(plan, registry)


def test_xml_is_parseable_with_sequence_root() -> None:
    xml_text, _ = _sandwich_outputs()
    root = ET.fromstring(xml_text)
    behavior_tree = root.find("BehaviorTree")

    assert behavior_tree is not None
    assert behavior_tree.find("Sequence") is not None


def test_xml_does_not_generate_parallel_or_fallback() -> None:
    xml_text, _ = _sandwich_outputs()
    root = ET.fromstring(xml_text)
    tags = {element.tag for element in root.iter()}

    assert "Parallel" not in tags
    assert "Fallback" not in tags


def test_xml_represents_human_step_explicitly() -> None:
    xml_text, _ = _sandwich_outputs()
    root = ET.fromstring(xml_text)
    await_scenes = root.findall(".//AwaitScene")

    assert any(
        node.attrib.get("name") == "Human step: Pour ingredient"
        and node.attrib.get("scene_name") == "{pour_ingredient_gate}"
        for node in await_scenes
    )


def test_yaml_is_parseable_and_contains_all_step_params() -> None:
    _, yaml_text = _sandwich_outputs()
    cfg = yaml.safe_load(yaml_text)
    bt_params = cfg["lerobot_bt_runner"]["ros__parameters"]["bt"]

    assert bt_params["place_first_toast_skill"] == "place_first_toast"
    assert bt_params["pour_ingredient_gate"] == "pour_ingredient"
    assert bt_params["pour_ingredient_instruction"]
    assert bt_params["initial_scene_ready_gate"] == "initial_scene_ready"
    assert bt_params["first_toast_placed_gate"] == "first_toast_placed"
