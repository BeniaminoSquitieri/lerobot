#!/usr/bin/env python

"""Tests for Linear IR validation before XML/YAML rendering."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from lerobot_bt_python.bt_generation.planner import build_linear_plan
from lerobot_bt_python.bt_generation.registry import (
    HUMAN_STEP,
    INFINITE_RETRY_ATTEMPTS,
    ROBOT_SKILL,
    VLM_GATE,
    Registry,
    load_registry,
)
from lerobot_bt_python.bt_generation.validator import validate_linear_plan


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/skills_registry.yaml"
SANDWICH_EXECUTOR = REPO_ROOT / "src/lerobot_bt_python/make_sandwich_executor.yaml"
BREAKFAST_EXECUTOR = REPO_ROOT / "src/lerobot_bt_python/set_breakfast_table_executor.yaml"


def test_valid_plan_passes() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = build_linear_plan("make_sandwich", registry)

    assert validate_linear_plan(plan, registry, SANDWICH_EXECUTOR) == []


def test_validator_accepts_infinite_robot_skill_retries() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = {
        "task_name": "make_sandwich",
        "steps": [{"kind": ROBOT_SKILL, "name": "place_first_toast"}],
    }

    assert registry.robot_skills["place_first_toast"].max_attempts == INFINITE_RETRY_ATTEMPTS
    assert validate_linear_plan(plan, registry, SANDWICH_EXECUTOR) == []


def test_infinite_retry_still_requires_positive_timeout() -> None:
    registry = load_registry(REGISTRY_PATH)
    bad_skill = replace(
        registry.robot_skills["place_first_toast"],
        max_attempts=INFINITE_RETRY_ATTEMPTS,
        timeout_s=0.0,
    )
    bad_registry = Registry(
        version=registry.version,
        robot_skills={**registry.robot_skills, "place_first_toast": bad_skill},
        human_steps=registry.human_steps,
        vlm_gates=registry.vlm_gates,
    )
    plan = {"task_name": "bad", "steps": [{"kind": ROBOT_SKILL, "name": "place_first_toast"}]}

    errors = validate_linear_plan(plan, bad_registry, SANDWICH_EXECUTOR)

    assert any("timeout_s must be > 0" in error for error in errors)


@pytest.mark.parametrize("bad", [0, -2])
def test_invalid_retry_value_fails(bad: int) -> None:
    registry = load_registry(REGISTRY_PATH)
    bad_skill = replace(registry.robot_skills["place_first_toast"], max_attempts=bad)
    bad_registry = Registry(
        version=registry.version,
        robot_skills={**registry.robot_skills, "place_first_toast": bad_skill},
        human_steps=registry.human_steps,
        vlm_gates=registry.vlm_gates,
    )
    plan = {"task_name": "bad", "steps": [{"kind": ROBOT_SKILL, "name": "place_first_toast"}]}

    errors = validate_linear_plan(plan, bad_registry, SANDWICH_EXECUTOR)

    assert any("max_attempts must be -1" in error for error in errors)


def test_unknown_robot_skill_fails() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = {"task_name": "bad", "steps": [{"kind": ROBOT_SKILL, "name": "invented_robot_skill"}]}

    errors = validate_linear_plan(plan, registry)

    assert any("not present in the registry" in error for error in errors)


def test_unknown_human_step_fails() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = {"task_name": "bad", "steps": [{"kind": HUMAN_STEP, "name": "invented_human_step"}]}

    errors = validate_linear_plan(plan, registry)

    assert any("not present in the registry" in error for error in errors)


def test_unknown_vlm_gate_fails() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = {"task_name": "bad", "steps": [{"kind": VLM_GATE, "name": "invented_gate"}]}

    errors = validate_linear_plan(plan, registry)

    assert any("not present in the registry" in error for error in errors)


def test_robot_skill_missing_from_executor_yaml_fails() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = {
        "task_name": "bad",
        "steps": [
            {"kind": ROBOT_SKILL, "name": "place_first_toast"},
            {"kind": VLM_GATE, "name": "first_toast_placed"},
        ],
    }

    errors = validate_linear_plan(plan, registry, BREAKFAST_EXECUTOR)

    assert any("not listed in executor YAML" in error for error in errors)


def test_vlm_gate_with_empty_task_fails() -> None:
    registry = load_registry(REGISTRY_PATH)
    bad_gate = replace(registry.vlm_gates["initial_scene_ready"], task="")
    bad_registry = Registry(
        version=registry.version,
        robot_skills=registry.robot_skills,
        human_steps=registry.human_steps,
        vlm_gates={**registry.vlm_gates, "initial_scene_ready": bad_gate},
    )
    plan = {"task_name": "bad", "steps": [{"kind": VLM_GATE, "name": "initial_scene_ready"}]}

    errors = validate_linear_plan(plan, bad_registry)

    assert any("non-empty task" in error for error in errors)


def test_human_step_without_instruction_fails() -> None:
    registry = load_registry(REGISTRY_PATH)
    bad_human = replace(registry.human_steps["pour_ingredient"], instruction="")
    bad_registry = Registry(
        version=registry.version,
        robot_skills=registry.robot_skills,
        human_steps={**registry.human_steps, "pour_ingredient": bad_human},
        vlm_gates=registry.vlm_gates,
    )
    plan = {
        "task_name": "bad",
        "steps": [
            {"kind": HUMAN_STEP, "name": "pour_ingredient"},
            {"kind": VLM_GATE, "name": "ingredient_poured"},
        ],
    }

    errors = validate_linear_plan(plan, bad_registry)

    assert any("non-empty instruction" in error for error in errors)


def test_forbidden_constructs_fail() -> None:
    registry = load_registry(REGISTRY_PATH)
    plan = {
        "task_name": "bad",
        "steps": [
            {"kind": "fallback", "name": "x"},
            {"kind": "parallel", "name": "x"},
            {"kind": VLM_GATE, "name": "initial_scene_ready", "raw_xml": "<Parallel />"},
        ],
    }

    errors = validate_linear_plan(plan, registry)

    assert any("forbidden kind 'fallback'" in error for error in errors)
    assert any("forbidden kind 'parallel'" in error for error in errors)
    assert any("forbidden fields ['raw_xml']" in error for error in errors)
