#!/usr/bin/env python

"""Tests for constrained model-response BT planning."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest
import yaml

from lerobot_bt_python.bt_generation.planner import TASK_TEMPLATES, build_linear_plan
from lerobot_bt_python.bt_generation.registry import load_registry
from lerobot_bt_python.bt_generation.renderer import render_bt_params_yaml, render_xml
from lerobot_bt_python.bt_generation.static_checks import validate_xml_yaml_blackboard_text
from lerobot_bt_python.bt_generation.validator import validate_linear_plan
from lerobot_bt_python.bt_generation.vlm_planner import (
    build_planner_prompt,
    canonicalize_plan,
    generate_plan_from_model_response,
    parse_planner_response,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/skills_registry.yaml"
SANDWICH_EXECUTOR = REPO_ROOT / "src/lerobot_bt_python/make_sandwich_executor.yaml"
EXECUTOR_PATHS = {
    "make_sandwich": SANDWICH_EXECUTOR,
    "set_breakfast_table": REPO_ROOT / "src/lerobot_bt_python/set_breakfast_table_executor.yaml",
    "make_coffee": REPO_ROOT / "src/lerobot_bt_python/make_coffee_executor.yaml",
    "prepare_picnic_bag": REPO_ROOT / "src/lerobot_bt_python/prepare_picnic_bag_executor.yaml",
    "items_in_drawer": REPO_ROOT / "src/lerobot_bt_python/items_in_drawer_executor.yaml",
}
ASSET_DIR = REPO_ROOT / "tests/assets/vlm_planner"


def test_build_planner_prompt_lists_available_step_kinds() -> None:
    registry = load_registry(REGISTRY_PATH)

    prompt = build_planner_prompt(
        "make_sandwich",
        registry,
        scene_facts={"ingredient_visible": True},
    )

    assert "task_name: make_sandwich" in prompt
    assert "Available robot_skills:" in prompt
    assert "- place_first_toast" in prompt
    assert "- place_second_toast" in prompt
    assert "Available human_steps:" in prompt
    assert "- pour_ingredient" in prompt
    assert "Available vlm_gates:" in prompt
    assert "- ingredient_poured" in prompt
    assert "- second_toast_ready" in prompt
    assert "- make_sandwich.task_complete" in prompt
    assert "place_first_toast = robot_skill" in prompt
    assert "pour_ingredient = human_step" in prompt
    assert "ingredient_poured = vlm_gate" in prompt
    assert "Return JSON only." in prompt
    assert "Do not return XML." in prompt
    assert "canonical_task_sequence JSON:" in prompt
    assert '"name": "ingredient_poured"' in prompt
    assert "ordering_constraints JSON:" in prompt
    assert '"before": "pour_ingredient"' in prompt
    assert '"after": "ingredient_poured"' in prompt
    assert "Follow canonical_task_sequence exactly." in prompt
    assert "Do not reorder steps." in prompt
    assert "The returned steps must match canonical_task_sequence exactly" in prompt
    assert '"ingredient_visible": true' in prompt


def test_valid_make_sandwich_model_response_parses() -> None:
    plan = parse_planner_response(_read_asset("make_sandwich_valid.json"))

    assert plan["task_name"] == "make_sandwich"
    assert plan["steps"][0] == {"kind": "vlm_gate", "name": "initial_scene_ready"}


def test_safe_json_markdown_fence_parses() -> None:
    plan = parse_planner_response(f"```json\n{_read_asset('make_sandwich_valid.json')}\n```")

    assert plan["task_name"] == "make_sandwich"


def test_prose_wrapped_json_fails() -> None:
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_planner_response(f"Here is the plan:\n{_read_asset('make_sandwich_valid.json')}")


def test_valid_make_sandwich_model_response_passes_strict_validation() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = generate_plan_from_model_response(
        "make_sandwich",
        registry,
        _read_asset("make_sandwich_valid.json"),
    )

    assert validate_linear_plan(plan, registry, SANDWICH_EXECUTOR, strict_generated=True) == []


def test_cli_model_response_mode_generates_xml_yaml(tmp_path: Path) -> None:
    tree = tmp_path / "generated_make_sandwich.xml"
    config = tmp_path / "generated_make_sandwich_bt.yaml"

    result = _run_cli(
        [
            "--task",
            "make_sandwich",
            "--planner",
            "model-response",
            "--model-response-file",
            str(ASSET_DIR / "make_sandwich_valid.json"),
            "--out-tree",
            str(tree),
            "--out-config",
            str(config),
        ]
    )

    assert result.returncode == 0, result.stderr
    ET.parse(tree)
    cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
    bt_params = cfg["lerobot_bt_runner"]["ros__parameters"]["bt"]
    assert bt_params["place_first_toast_skill"] == "place_first_toast"
    assert bt_params["pour_ingredient_gate"] == "pour_ingredient"
    assert bt_params["ingredient_poured_gate"] == "ingredient_poured"


def test_cli_model_response_requires_file(tmp_path: Path) -> None:
    result = _run_cli(
        [
            "--task",
            "make_sandwich",
            "--planner",
            "model-response",
            "--out-tree",
            str(tmp_path / "bad.xml"),
            "--out-config",
            str(tmp_path / "bad.yaml"),
        ]
    )

    assert result.returncode != 0
    assert "--planner model-response requires --model-response-file" in result.stderr


def test_generated_xml_yaml_pass_static_blackboard_check() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = generate_plan_from_model_response(
        "make_sandwich",
        registry,
        _read_asset("make_sandwich_valid.json"),
    )

    assert validate_xml_yaml_blackboard_text(
        render_xml(plan, registry),
        render_bt_params_yaml(plan, registry),
    ) == []


def test_xml_response_fails() -> None:
    with pytest.raises(ValueError, match="XML-like"):
        parse_planner_response(_read_asset("make_sandwich_bad_xml_response.txt"))


def test_invented_skill_fails_strict_validation() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = parse_planner_response(_read_asset("make_sandwich_bad_invented_skill.json"))

    errors = validate_linear_plan(plan, registry, SANDWICH_EXECUTOR, strict_generated=True)

    assert any("not present in the registry" in error for error in errors)


def test_pour_ingredient_as_robot_skill_fails() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = parse_planner_response(_read_asset("make_sandwich_bad_wrong_executor.json"))

    errors = validate_linear_plan(plan, registry, SANDWICH_EXECUTOR, strict_generated=True)

    assert any("'human_step' in the registry, not 'robot_skill'" in error for error in errors)


def test_place_first_toast_as_human_step_fails() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = parse_planner_response(_read_asset("make_sandwich_bad_wrong_human_kind.json"))

    errors = validate_linear_plan(plan, registry, SANDWICH_EXECUTOR, strict_generated=True)

    assert any("'robot_skill' in the registry, not 'human_step'" in error for error in errors)


def test_missing_initial_scene_ready_fails() -> None:
    errors = _strict_errors_for_asset("make_sandwich_bad_missing_initial_gate.json")

    assert any("must start with vlm_gate 'initial_scene_ready'" in error for error in errors)


def test_missing_make_sandwich_task_complete_fails() -> None:
    errors = _strict_errors_for_asset("make_sandwich_bad_missing_final_gate.json")

    assert any("must finish with vlm_gate 'make_sandwich.task_complete'" in error for error in errors)


def test_place_second_toast_without_second_toast_ready_fails() -> None:
    errors = _strict_errors_for_asset("make_sandwich_bad_missing_second_toast_ready.json")

    assert any("must be preceded by vlm_gate 'second_toast_ready'" in error for error in errors)


def test_swapped_make_sandwich_order_fails_strict_validation() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = {
        "task_name": "make_sandwich",
        "steps": [
            {"kind": "vlm_gate", "name": "initial_scene_ready"},
            {"kind": "robot_skill", "name": "place_first_toast"},
            {"kind": "human_step", "name": "pour_ingredient"},
            {"kind": "vlm_gate", "name": "second_toast_ready"},
            {"kind": "vlm_gate", "name": "ingredient_poured"},
            {"kind": "robot_skill", "name": "place_second_toast"},
            {"kind": "vlm_gate", "name": "make_sandwich.task_complete"},
        ],
    }

    errors = validate_linear_plan(plan, registry, SANDWICH_EXECUTOR, strict_generated=True)

    assert any("does not match canonical task sequence" in error for error in errors)


def test_missing_ingredient_poured_fails_strict_validation() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = {
        "task_name": "make_sandwich",
        "steps": [
            {"kind": "vlm_gate", "name": "initial_scene_ready"},
            {"kind": "robot_skill", "name": "place_first_toast"},
            {"kind": "human_step", "name": "pour_ingredient"},
            {"kind": "vlm_gate", "name": "second_toast_ready"},
            {"kind": "robot_skill", "name": "place_second_toast"},
            {"kind": "vlm_gate", "name": "make_sandwich.task_complete"},
        ],
    }

    errors = validate_linear_plan(plan, registry, SANDWICH_EXECUTOR, strict_generated=True)

    assert any("does not match canonical task sequence" in error for error in errors)


def test_make_coffee_wrong_order_fails_strict_validation() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = {
        "task_name": "make_coffee",
        "steps": [
            {"kind": "vlm_gate", "name": "make_coffee.scene_0_ready"},
            {"kind": "robot_skill", "name": "pick_and_insert_capsule"},
            {"kind": "human_step", "name": "make_coffee.cup_under_dispenser"},
            {"kind": "robot_skill", "name": "close_coffee_machine"},
            {"kind": "human_step", "name": "make_coffee.human_press_start_button"},
        ],
    }

    errors = validate_linear_plan(
        plan,
        registry,
        EXECUTOR_PATHS["make_coffee"],
        strict_generated=True,
    )

    assert any("does not match canonical task sequence for 'make_coffee'" in error for error in errors)


def test_extra_step_fails_strict_validation() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = {
        "task_name": "make_sandwich",
        "steps": [
            *TASK_TEMPLATES["make_sandwich"],
            {"kind": "vlm_gate", "name": "first_toast_placed"},
        ],
    }

    errors = validate_linear_plan(plan, registry, SANDWICH_EXECUTOR, strict_generated=True)

    assert any("does not match canonical task sequence" in error for error in errors)


def test_missing_step_fails_strict_validation() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = {
        "task_name": "make_sandwich",
        "steps": TASK_TEMPLATES["make_sandwich"][:-1],
    }

    errors = validate_linear_plan(plan, registry, SANDWICH_EXECUTOR, strict_generated=True)

    assert any("does not match canonical task sequence" in error for error in errors)


def test_known_object_alias_canonicalizes() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = generate_plan_from_model_response(
        "make_sandwich",
        registry,
        _read_asset("make_sandwich_valid_with_alias.json"),
    )

    assert plan["steps"][1]["object"] == "first_toast"
    assert plan["steps"][2]["object"] == "ingredient"
    assert plan["steps"][5]["object"] == "second_toast"
    assert validate_linear_plan(plan, registry, SANDWICH_EXECUTOR, strict_generated=True) == []


def test_unknown_object_alias_fails() -> None:
    registry = load_registry(REGISTRY_PATH)

    with pytest.raises(ValueError, match="object 'cup' is not registered"):
        generate_plan_from_model_response(
            "make_sandwich",
            registry,
            _read_asset("make_sandwich_bad_unknown_object.json"),
        )


def test_template_planner_mode_still_works(tmp_path: Path) -> None:
    tree = tmp_path / "generated_make_sandwich_template.xml"
    config = tmp_path / "generated_make_sandwich_template_bt.yaml"

    result = _run_cli(
        [
            "--task",
            "make_sandwich",
            "--planner",
            "template",
            "--out-tree",
            str(tree),
            "--out-config",
            str(config),
        ]
    )

    assert result.returncode == 0, result.stderr
    ET.parse(tree)
    yaml.safe_load(config.read_text(encoding="utf-8"))


def test_template_plan_remains_valid() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan("make_sandwich", registry)

    assert validate_linear_plan(plan, registry, SANDWICH_EXECUTOR) == []


def test_template_plans_for_all_tasks_pass_strict_canonical_validation() -> None:
    registry = load_registry(REGISTRY_PATH)

    for task_name, executor_path in EXECUTOR_PATHS.items():
        plan = build_linear_plan(task_name, registry)

        assert validate_linear_plan(plan, registry, executor_path, strict_generated=True) == []


def _strict_errors_for_asset(asset_name: str) -> list[str]:
    registry = load_registry(REGISTRY_PATH)
    plan = canonicalize_plan(parse_planner_response(_read_asset(asset_name)), registry)
    return validate_linear_plan(plan, registry, SANDWICH_EXECUTOR, strict_generated=True)


def _read_asset(asset_name: str) -> str:
    return (ASSET_DIR / asset_name).read_text(encoding="utf-8")


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "lerobot_bt_python.bt_generation.generate",
            "--registry",
            str(REGISTRY_PATH),
            "--executor-yaml",
            str(SANDWICH_EXECUTOR),
            *args,
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
