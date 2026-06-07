#!/usr/bin/env python

"""Tests for deterministic task template planning."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from lerobot_bt_python.bt_generation.planner import build_linear_plan
from lerobot_bt_python.bt_generation.registry import HUMAN_STEP, ROBOT_SKILL, VLM_GATE, load_registry


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/skills_registry.yaml"
SANDWICH_EXECUTOR = REPO_ROOT / "src/lerobot_bt_python/make_sandwich_executor.yaml"


def test_make_sandwich_produces_linear_ir() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan("make_sandwich", registry)

    assert plan["task_name"] == "make_sandwich"
    assert plan["steps"]
    assert all(step["kind"] in {ROBOT_SKILL, HUMAN_STEP, VLM_GATE} for step in plan["steps"])


def test_set_breakfast_table_produces_linear_ir() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan("set_breakfast_table", registry)

    assert plan["task_name"] == "set_breakfast_table"
    assert plan["steps"]
    assert all(step["kind"] in {ROBOT_SKILL, HUMAN_STEP, VLM_GATE} for step in plan["steps"])


def test_pour_ingredient_is_human_step_from_repo_audit() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan("make_sandwich", registry)
    executor = yaml.safe_load(SANDWICH_EXECUTOR.read_text(encoding="utf-8"))
    skill_names = {skill["name"] for skill in executor["skills"]}
    pour_entry = registry.get(HUMAN_STEP, "pour_ingredient")

    assert "pour_ingredient" not in skill_names
    assert "pour_ingredient" not in set(executor["expected_skill_names"])
    assert pour_entry.verify_after == "ingredient_poured"
    assert {"kind": HUMAN_STEP, "name": "pour_ingredient"} in plan["steps"]


def test_place_first_toast_is_robot_skill_from_repo_audit() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan("make_sandwich", registry)
    executor = yaml.safe_load(SANDWICH_EXECUTOR.read_text(encoding="utf-8"))
    skill_names = {skill["name"] for skill in executor["skills"]}

    assert "place_first_toast" in skill_names
    assert "place_first_toast" in set(executor["expected_skill_names"])
    assert {"kind": ROBOT_SKILL, "name": "place_first_toast"} in plan["steps"]


def test_human_steps_are_followed_by_verify_after() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan("make_sandwich", registry)

    for index, step in enumerate(plan["steps"]):
        if step["kind"] != HUMAN_STEP:
            continue
        verify_after = registry.get(step["kind"], step["name"]).verify_after
        if verify_after is None:
            continue
        assert plan["steps"][index + 1] == {"kind": VLM_GATE, "name": verify_after}


def test_robot_postcondition_gates_are_not_default_because_do_skill_verifies() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan("make_sandwich", registry)

    assert {"kind": VLM_GATE, "name": "first_toast_placed"} not in plan["steps"]
    assert {"kind": VLM_GATE, "name": "second_toast_placed"} in plan["steps"]


def test_robot_postcondition_gates_can_be_requested_explicitly() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan(
        "make_sandwich",
        registry,
        explicit_robot_postcondition_gates=True,
    )

    assert {"kind": VLM_GATE, "name": "first_toast_placed"} in plan["steps"]
    assert {"kind": VLM_GATE, "name": "second_toast_placed"} in plan["steps"]


def test_unknown_task_fails() -> None:
    registry = load_registry(REGISTRY_PATH)

    with pytest.raises(ValueError, match="Unknown task_name"):
        build_linear_plan("invented_task", registry)
