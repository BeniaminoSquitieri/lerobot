#!/usr/bin/env python

"""Tests for generated XML/YAML blackboard key consistency checks."""

from __future__ import annotations

from pathlib import Path

import yaml

from lerobot_bt_python.bt_generation.planner import build_linear_plan
from lerobot_bt_python.bt_generation.registry import load_registry
from lerobot_bt_python.bt_generation.renderer import render_bt_params_yaml, render_xml
from lerobot_bt_python.bt_generation.static_checks import validate_xml_yaml_blackboard_keys


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/skills_registry.yaml"


def test_generated_make_sandwich_xml_yaml_blackboard_keys_pass(tmp_path: Path) -> None:
    xml_path, yaml_path = _write_generated_pair(tmp_path, "make_sandwich")

    assert validate_xml_yaml_blackboard_keys(xml_path, yaml_path) == []


def test_generated_set_breakfast_table_xml_yaml_blackboard_keys_pass(tmp_path: Path) -> None:
    xml_path, yaml_path = _write_generated_pair(tmp_path, "set_breakfast_table")

    assert validate_xml_yaml_blackboard_keys(xml_path, yaml_path) == []


def test_xml_missing_blackboard_key_fails(tmp_path: Path) -> None:
    xml_path = tmp_path / "bad.xml"
    yaml_path = tmp_path / "bad.yaml"
    xml_path.write_text(
        """
<root BTCPP_format="4" main_tree_to_execute="MainTree">
  <BehaviorTree ID="MainTree">
    <Sequence>
      <DoSkill skill_name="{missing_key}" timeout_s="{known_timeout_s}" />
    </Sequence>
  </BehaviorTree>
</root>
""".strip(),
        encoding="utf-8",
    )
    yaml_path.write_text(
        yaml.safe_dump(
            {
                "lerobot_bt_runner": {
                    "ros__parameters": {
                        "bt": {
                            "known_timeout_s": 1.0,
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    errors = validate_xml_yaml_blackboard_keys(xml_path, yaml_path)

    assert any("missing_key" in error for error in errors)


def test_wrong_yaml_structure_fails(tmp_path: Path) -> None:
    xml_path = tmp_path / "tree.xml"
    yaml_path = tmp_path / "wrong.yaml"
    xml_path.write_text("<root><BehaviorTree><Sequence /></BehaviorTree></root>", encoding="utf-8")
    yaml_path.write_text("not_lerobot_bt_runner: {}\n", encoding="utf-8")

    errors = validate_xml_yaml_blackboard_keys(xml_path, yaml_path)

    assert errors == ["YAML must contain lerobot_bt_runner.ros__parameters.bt."]


def _write_generated_pair(tmp_path: Path, task_name: str) -> tuple[Path, Path]:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan(task_name, registry)
    xml_path = tmp_path / f"{task_name}.xml"
    yaml_path = tmp_path / f"{task_name}.yaml"

    xml_path.write_text(render_xml(plan, registry), encoding="utf-8")
    yaml_path.write_text(render_bt_params_yaml(plan, registry), encoding="utf-8")
    return xml_path, yaml_path
