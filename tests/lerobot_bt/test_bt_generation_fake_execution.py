#!/usr/bin/env python

"""Pure-Python fake execution tests for generated Linear IR plans."""

from __future__ import annotations

from pathlib import Path

from lerobot_bt_python.bt_generation.planner import build_linear_plan
from lerobot_bt_python.bt_generation.registry import load_registry
from lerobot_bt_python.fakes.fake_bt_executor_server import (
    ERROR,
    FAILURE,
    SUCCESS,
    TIMEOUT,
    execute_linear_plan_with_fake_responses,
    load_fake_scenario,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/skills_registry.yaml"


def _sandwich_plan() -> dict:
    registry = load_registry(REGISTRY_PATH)
    return build_linear_plan("make_sandwich", registry)


def test_success_all_reaches_success() -> None:
    result = execute_linear_plan_with_fake_responses(
        _sandwich_plan(),
        load_fake_scenario("success_all"),
    )

    assert result.status == SUCCESS
    assert "place_first_toast" in result.robot_skills
    assert "place_second_toast" in result.robot_skills


def test_initial_scene_failed_blocks_before_robot_skills() -> None:
    result = execute_linear_plan_with_fake_responses(
        _sandwich_plan(),
        load_fake_scenario("initial_scene_failed"),
    )

    assert result.status == FAILURE
    assert result.robot_skills == []
    assert result.visited_steps == ["initial_scene_ready"]


def test_robot_first_toast_failed_blocks_the_plan() -> None:
    result = execute_linear_plan_with_fake_responses(
        _sandwich_plan(),
        load_fake_scenario("robot_first_toast_failed"),
    )

    assert result.status == FAILURE
    assert "place_first_toast" in result.visited_steps
    assert "pour_ingredient" not in result.visited_steps


def test_human_pouring_timeout_blocks_before_second_toast() -> None:
    result = execute_linear_plan_with_fake_responses(
        _sandwich_plan(),
        load_fake_scenario("human_pouring_timeout"),
        running_poll_limit=2,
    )

    assert result.status == TIMEOUT
    assert "pour_ingredient" in result.visited_steps
    assert "place_second_toast" not in result.visited_steps


def test_vlm_postcondition_failed_blocks_the_plan() -> None:
    result = execute_linear_plan_with_fake_responses(
        _sandwich_plan(),
        load_fake_scenario("vlm_postcondition_failed"),
    )

    assert result.status == FAILURE
    assert result.visited_steps == ["initial_scene_ready", "place_first_toast"]
    assert "pour_ingredient" not in result.visited_steps


def test_unknown_status_is_not_running_forever() -> None:
    result = execute_linear_plan_with_fake_responses(
        _sandwich_plan(),
        load_fake_scenario("unknown_status"),
        running_poll_limit=2,
    )

    assert result.status in {ERROR, FAILURE}
    assert result.status != SUCCESS
    assert result.visited_steps == ["initial_scene_ready", "place_first_toast"]
