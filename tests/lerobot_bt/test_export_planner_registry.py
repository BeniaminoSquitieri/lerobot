#!/usr/bin/env python

"""Tests for planner registry payload export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lerobot_bt_python.bt_generation.export_planner_registry import build_planner_registry_payload
from lerobot_bt_python.bt_generation.registry import load_registry


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/skills_registry.yaml"


def test_make_sandwich_payload_contains_canonical_task_sequence() -> None:
    registry = load_registry(REGISTRY_PATH)
    payload = build_planner_registry_payload("make_sandwich", registry)

    assert payload["canonical_task_sequence"] == [
        {"kind": "vlm_gate", "name": "initial_scene_ready"},
        {"kind": "robot_skill", "name": "place_first_toast"},
        {"kind": "human_step", "name": "pour_ingredient"},
        {"kind": "vlm_gate", "name": "ingredient_poured"},
        {"kind": "vlm_gate", "name": "second_toast_ready"},
        {"kind": "robot_skill", "name": "place_second_toast"},
        {"kind": "vlm_gate", "name": "make_sandwich.task_complete"},
    ]


def test_make_sandwich_sequence_places_ingredient_poured_after_pour_ingredient() -> None:
    registry = load_registry(REGISTRY_PATH)
    payload = build_planner_registry_payload("make_sandwich", registry)
    names = [step["name"] for step in payload["canonical_task_sequence"]]

    assert names.index("ingredient_poured") == names.index("pour_ingredient") + 1


def test_make_coffee_payload_contains_canonical_task_sequence() -> None:
    registry = load_registry(REGISTRY_PATH)
    payload = build_planner_registry_payload("make_coffee", registry)

    assert payload["canonical_task_sequence"] == [
        {"kind": "vlm_gate", "name": "make_coffee.scene_0_ready"},
        {"kind": "human_step", "name": "make_coffee.cup_under_dispenser"},
        {"kind": "robot_skill", "name": "pick_and_insert_capsule"},
        {"kind": "robot_skill", "name": "close_coffee_machine"},
        {"kind": "human_step", "name": "make_coffee.human_press_start_button"},
    ]


def test_ordering_constraints_are_adjacent_step_pairs() -> None:
    registry = load_registry(REGISTRY_PATH)
    payload = build_planner_registry_payload("make_sandwich", registry)

    assert payload["ordering_constraints"] == [
        {"before": "initial_scene_ready", "after": "place_first_toast"},
        {"before": "place_first_toast", "after": "pour_ingredient"},
        {"before": "pour_ingredient", "after": "ingredient_poured"},
        {"before": "ingredient_poured", "after": "second_toast_ready"},
        {"before": "second_toast_ready", "after": "place_second_toast"},
        {"before": "place_second_toast", "after": "make_sandwich.task_complete"},
    ]


def test_payload_filters_entries_and_keeps_rules_json_serializable() -> None:
    registry = load_registry(REGISTRY_PATH)
    payload = build_planner_registry_payload("make_sandwich", registry)

    assert {entry["name"] for entry in payload["robot_skills"]} == {
        "place_first_toast",
        "place_second_toast",
    }
    assert {entry["name"] for entry in payload["human_steps"]} == {"pour_ingredient"}
    assert {
        "initial_scene_ready",
        "ingredient_poured",
        "second_toast_ready",
        "make_sandwich.task_complete",
    }.issubset({entry["name"] for entry in payload["vlm_gates"]})
    for rule in [
        "return_json_only",
        "no_xml",
        "registered_names_only",
        "do_not_change_step_kinds",
        "follow_canonical_task_sequence",
        "do_not_reorder_steps",
        "do_not_add_steps",
        "do_not_remove_steps",
    ]:
        assert payload["rules"][rule] is True
    json.dumps(payload)


def test_export_fails_on_missing_registry_entry() -> None:
    class DummyRegistry:
        objects = {}

        def kind_for_name(self, name: str) -> None:
            return None

    with pytest.raises(ValueError, match="not present in registry"):
        build_planner_registry_payload("make_sandwich", DummyRegistry())  # type: ignore[arg-type]
