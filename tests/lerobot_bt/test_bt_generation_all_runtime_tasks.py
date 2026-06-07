#!/usr/bin/env python

"""Coverage for generating every runtime BT task from the template planner."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest
import yaml

from lerobot_bt_python.bt_generation.planner import build_linear_plan
from lerobot_bt_python.bt_generation.registry import HUMAN_STEP, ROBOT_SKILL, VLM_GATE, load_registry
from lerobot_bt_python.bt_generation.renderer import param_key, render_bt_params_yaml, render_xml
from lerobot_bt_python.bt_generation.static_checks import validate_xml_yaml_blackboard_keys


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/skills_registry.yaml"
EXECUTOR_PATHS = {
    "make_sandwich": REPO_ROOT / "src/lerobot_bt_python/make_sandwich_executor.yaml",
    "set_breakfast_table": REPO_ROOT / "src/lerobot_bt_python/set_breakfast_table_executor.yaml",
    "make_coffee": REPO_ROOT / "src/lerobot_bt_python/make_coffee_executor.yaml",
    "prepare_picnic_bag": REPO_ROOT / "src/lerobot_bt_python/prepare_picnic_bag_executor.yaml",
    "items_in_drawer": REPO_ROOT / "src/lerobot_bt_python/items_in_drawer_executor.yaml",
}
EXPECTED_STEPS = {
    "make_sandwich": [
        {"kind": VLM_GATE, "name": "initial_scene_ready"},
        {"kind": ROBOT_SKILL, "name": "place_first_toast"},
        {"kind": HUMAN_STEP, "name": "pour_ingredient"},
        {"kind": VLM_GATE, "name": "ingredient_poured"},
        {"kind": ROBOT_SKILL, "name": "place_second_toast"},
        {"kind": VLM_GATE, "name": "second_toast_placed"},
        {"kind": VLM_GATE, "name": "make_sandwich.task_complete"},
    ],
    "set_breakfast_table": [
        {"kind": HUMAN_STEP, "name": "breakfast_table.tablecloth_ready"},
        {"kind": ROBOT_SKILL, "name": "place_cereal_box"},
        {"kind": HUMAN_STEP, "name": "breakfast_table.tea_box_ready"},
        {"kind": ROBOT_SKILL, "name": "place_bottle"},
        {"kind": ROBOT_SKILL, "name": "place_cup"},
        {"kind": HUMAN_STEP, "name": "breakfast_table.spoon_ready"},
        {"kind": ROBOT_SKILL, "name": "place_bowl"},
        {"kind": VLM_GATE, "name": "breakfast_table.task_complete"},
    ],
    "make_coffee": [
        {"kind": VLM_GATE, "name": "make_coffee.scene_0_ready"},
        {"kind": HUMAN_STEP, "name": "make_coffee.cup_under_dispenser"},
        {"kind": ROBOT_SKILL, "name": "pick_and_insert_capsule"},
        {"kind": ROBOT_SKILL, "name": "close_coffee_machine"},
        {"kind": HUMAN_STEP, "name": "make_coffee.human_press_start_button"},
    ],
    "prepare_picnic_bag": [
        {"kind": VLM_GATE, "name": "prepare_picnic_bag.scene_0_ready"},
        {"kind": HUMAN_STEP, "name": "prepare_picnic_bag.human_open_bag"},
        {"kind": HUMAN_STEP, "name": "prepare_picnic_bag.human_insert_monster"},
        {"kind": ROBOT_SKILL, "name": "bag_bread"},
        {"kind": HUMAN_STEP, "name": "prepare_picnic_bag.human_insert_mustard"},
        {"kind": ROBOT_SKILL, "name": "bag_pear"},
    ],
    "items_in_drawer": [
        {"kind": VLM_GATE, "name": "items_in_drawer.scene_0_ready"},
        {"kind": HUMAN_STEP, "name": "items_in_drawer.drawer_open_ready"},
        {"kind": ROBOT_SKILL, "name": "insert_next_drawer_item"},
        {"kind": HUMAN_STEP, "name": "items_in_drawer.drawer_closed"},
        {"kind": VLM_GATE, "name": "items_in_drawer.task_complete"},
    ],
}


@pytest.mark.parametrize("task_name", EXPECTED_STEPS)
def test_build_linear_plan_matches_runtime_task_order(task_name: str) -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan(task_name, registry)

    assert plan == {"task_name": task_name, "steps": EXPECTED_STEPS[task_name]}


@pytest.mark.parametrize("task_name", EXPECTED_STEPS)
def test_cli_generates_parseable_xml_yaml_for_runtime_task(task_name: str, tmp_path: Path) -> None:
    tree = tmp_path / f"{task_name}.xml"
    config = tmp_path / f"{task_name}_bt.yaml"

    result = _run_cli(task_name, tree, config)

    assert result.returncode == 0, result.stderr
    ET.parse(tree)
    yaml.safe_load(config.read_text(encoding="utf-8"))
    assert validate_xml_yaml_blackboard_keys(tree, config) == []


@pytest.mark.parametrize("task_name", EXPECTED_STEPS)
def test_generated_xml_has_no_parallel_or_fallback(task_name: str) -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan(task_name, registry)
    root = ET.fromstring(render_xml(plan, registry))
    tags = {element.tag for element in root.iter()}

    assert "Parallel" not in tags
    assert "Fallback" not in tags


@pytest.mark.parametrize("task_name", EXPECTED_STEPS)
def test_step_kinds_render_to_expected_leaf_types(task_name: str) -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan(task_name, registry)
    root = ET.fromstring(render_xml(plan, registry))
    do_skill_keys = {node.attrib.get("skill_name") for node in root.findall(".//DoSkill")}
    await_scene_keys = {node.attrib.get("scene_name") for node in root.findall(".//AwaitScene")}

    for step in plan["steps"]:
        key = param_key(step["name"])
        if step["kind"] == ROBOT_SKILL:
            assert f"{{{key}_skill}}" in do_skill_keys
            assert f"{{{key}_gate}}" not in await_scene_keys
        elif step["kind"] in {HUMAN_STEP, VLM_GATE}:
            assert f"{{{key}_gate}}" in await_scene_keys
            assert f"{{{key}_skill}}" not in do_skill_keys


@pytest.mark.parametrize("task_name", EXPECTED_STEPS)
def test_rendered_yaml_is_parseable_for_runtime_task(task_name: str) -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan(task_name, registry)

    yaml.safe_load(render_bt_params_yaml(plan, registry))


def _run_cli(task_name: str, out_tree: Path, out_config: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "lerobot_bt_python.bt_generation.generate",
            "--task",
            task_name,
            "--registry",
            str(REGISTRY_PATH),
            "--executor-yaml",
            str(EXECUTOR_PATHS[task_name]),
            "--out-tree",
            str(out_tree),
            "--out-config",
            str(out_config),
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
