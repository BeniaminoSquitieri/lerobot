#!/usr/bin/env python

"""Tests for the deterministic BT generation registry."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from lerobot_bt_python.bt_generation.registry import (
    EXPECTED_EXECUTORS,
    HUMAN_STEP,
    INFINITE_RETRY_ATTEMPTS,
    ROBOT_SKILL,
    VLM_GATE,
    Registry,
    is_valid_max_attempts,
    load_registry,
    validate_registry,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/skills_registry.yaml"


def test_registry_loads_and_validates() -> None:
    registry = load_registry(REGISTRY_PATH)

    assert validate_registry(registry) == []


def test_registry_names_are_globally_unique() -> None:
    registry = load_registry(REGISTRY_PATH)
    names = [entry.name for entry in registry.all_entries]

    assert len(names) == len(set(names))


def test_verify_after_targets_existing_vlm_gates() -> None:
    registry = load_registry(REGISTRY_PATH)

    for entry in [*registry.robot_skills.values(), *registry.human_steps.values()]:
        if entry.verify_after is not None:
            assert entry.verify_after in registry.vlm_gates


def test_human_steps_have_instructions() -> None:
    registry = load_registry(REGISTRY_PATH)

    assert registry.human_steps
    for entry in registry.human_steps.values():
        assert entry.kind == HUMAN_STEP
        assert entry.instruction.strip()


def test_vlm_gates_have_tasks() -> None:
    registry = load_registry(REGISTRY_PATH)

    assert registry.vlm_gates
    for entry in registry.vlm_gates.values():
        assert entry.kind == VLM_GATE
        assert entry.task.strip()


def test_timeouts_attempts_and_executors_are_valid() -> None:
    registry = load_registry(REGISTRY_PATH)

    for entry in registry.all_entries:
        assert entry.timeout_s > 0.0
        assert is_valid_max_attempts(entry.max_attempts)
        assert entry.executor == EXPECTED_EXECUTORS[entry.kind]


def test_registry_accepts_infinite_retries_for_robot_skills() -> None:
    registry = load_registry(REGISTRY_PATH)

    assert registry.robot_skills["place_first_toast"].max_attempts == INFINITE_RETRY_ATTEMPTS
    assert validate_registry(registry) == []


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

    errors = validate_registry(bad_registry)

    assert any("timeout_s must be > 0" in error for error in errors)


@pytest.mark.parametrize("bad", [0, -2, -10])
def test_invalid_retry_values_fail(bad: int) -> None:
    registry = load_registry(REGISTRY_PATH)
    bad_skill = replace(registry.robot_skills["place_first_toast"], max_attempts=bad)
    bad_registry = Registry(
        version=registry.version,
        robot_skills={**registry.robot_skills, "place_first_toast": bad_skill},
        human_steps=registry.human_steps,
        vlm_gates=registry.vlm_gates,
    )

    errors = validate_registry(bad_registry)

    assert any("max_attempts must be -1" in error for error in errors)


def test_robot_skill_names_are_explicitly_robotic() -> None:
    registry = load_registry(REGISTRY_PATH)

    assert registry.robot_skills["place_first_toast"].kind == ROBOT_SKILL
    assert registry.human_steps["pour_ingredient"].kind == HUMAN_STEP
