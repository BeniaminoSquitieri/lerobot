#!/usr/bin/env python

"""Static safety checks for BT runtime and executor YAML profiles."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest
import yaml

from lerobot_bt_python.bt_generation.registry import is_valid_max_attempts


REPO_ROOT = Path(__file__).resolve().parents[2]
BT_CONFIG_DIR = REPO_ROOT / "src/lerobot_bt_runtime_cpp/config"
EXECUTOR_CONFIG_DIR = REPO_ROOT / "src/lerobot_bt_python"
MAX_SKILL_DURATION_S = 300.0
ITEMS_IN_DRAWER_EXECUTOR = EXECUTOR_CONFIG_DIR / "items_in_drawer_executor.yaml"
SKILL_SERVER_CONFIG_PATH = REPO_ROOT / "src/lerobot_bt_python/config.py"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path} must contain a YAML mapping"
    return data


def _executor_yaml_paths() -> list[Path]:
    return sorted(EXECUTOR_CONFIG_DIR.glob("*_executor.yaml"))


def _bt_yaml_paths() -> list[Path]:
    return sorted(BT_CONFIG_DIR.glob("*_bt.yaml"))


def _skill_server_default_node(field_name: str) -> ast.AST:
    module = ast.parse(SKILL_SERVER_CONFIG_PATH.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == "SkillCommandServerConfig":
            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    if child.target.id == field_name and child.value is not None:
                        return child.value
    raise AssertionError(f"Default for {field_name} not found in SkillCommandServerConfig")


def _skill_server_literal_default(field_name: str) -> Any:
    node = _skill_server_default_node(field_name)
    if not isinstance(node, ast.Constant):
        raise AssertionError(f"Default for {field_name} is not a literal constant")
    return node.value


@pytest.mark.parametrize("path", _bt_yaml_paths(), ids=lambda path: path.name)
def test_bt_retry_values_are_valid(path: Path) -> None:
    cfg = _load_yaml(path)
    bt_params = cfg["lerobot_bt_runner"]["ros__parameters"]["bt"]

    retry_limits = {
        key: value
        for key, value in bt_params.items()
        if key.endswith("_max_attempts")
    }

    assert retry_limits, f"{path} should define retry limits"
    for key, value in retry_limits.items():
        assert isinstance(value, int), f"{path}:{key} must be an integer"
        assert is_valid_max_attempts(value), f"{path}:{key} must be -1 or a positive integer"


@pytest.mark.parametrize("value", [-1, 1, 3])
def test_retry_value_helper_accepts_supported_values(value: int) -> None:
    assert is_valid_max_attempts(value)


@pytest.mark.parametrize("value", [0, -2, -10])
def test_retry_value_helper_rejects_invalid_values(value: int) -> None:
    assert not is_valid_max_attempts(value)


@pytest.mark.parametrize("path", _executor_yaml_paths(), ids=lambda path: path.name)
def test_executor_vlm_timeout_is_enabled(path: Path) -> None:
    cfg = _load_yaml(path)

    # 0 means "no per-attempt timeout" (gate waits indefinitely); negative is invalid.
    assert float(cfg["vlm_timeout_s"]) >= 0.0, f"{path}:vlm_timeout_s must be >= 0"


@pytest.mark.parametrize("path", _executor_yaml_paths(), ids=lambda path: path.name)
def test_executor_skill_durations_are_bounded(path: Path) -> None:
    cfg = _load_yaml(path)

    for skill in cfg.get("skills", []):
        transition = skill.get("transition", {})
        max_duration_s = float(transition.get("max_duration_s", 0.0))
        assert 0.0 < max_duration_s <= MAX_SKILL_DURATION_S, (
            f"{path}:{skill.get('name')} transition.max_duration_s must be "
            f"within (0, {MAX_SKILL_DURATION_S}] seconds"
        )


@pytest.mark.parametrize("path", _executor_yaml_paths(), ids=lambda path: path.name)
def test_selected_policy_variants_exist(path: Path) -> None:
    cfg = _load_yaml(path)
    default_variant = cfg.get("policy_variant")

    for skill in cfg.get("skills", []):
        selected_variant = skill.get("policy_variant") or default_variant
        policy_variants = skill.get("policy_variants", {})
        assert selected_variant in policy_variants, (
            f"{path}:{skill.get('name')} selects missing policy variant "
            f"{selected_variant!r}; available={sorted(policy_variants)}"
        )


@pytest.mark.parametrize("path", _executor_yaml_paths(), ids=lambda path: path.name)
def test_camera_publish_map_covers_required_cameras(path: Path) -> None:
    cfg = _load_yaml(path)
    required_cameras = set(cfg.get("required_cameras", []))
    camera_publish_map = cfg.get("camera_publish_map", {})

    assert required_cameras <= set(camera_publish_map), (
        f"{path}:camera_publish_map must cover required cameras "
        f"{sorted(required_cameras)}"
    )


def test_items_in_drawer_omits_runtime_defaults() -> None:
    cfg = _load_yaml(ITEMS_IN_DRAWER_EXECUTOR)

    omitted_literal_defaults = {
        "bt_command_service",
        "vlm_state_service",
        "legacy_vlm_result_service",
        "vlm_request_topic",
        "vlm_result_topic",
        "policy_variant",
        "fps",
        "display_data",
        "play_sounds",
        "reset_robot_on_startup",
        "reset_robot_before_skill",
        "camera_publish_fps",
        "camera_publish_jpeg_quality",
    }
    omitted_factory_defaults = {
        "rename_map",
        "robot_action_processor",
        "robot_observation_processor",
    }

    for key in sorted(omitted_literal_defaults | omitted_factory_defaults):
        assert key not in cfg, f"{ITEMS_IN_DRAWER_EXECUTOR}:{key} should rely on config defaults"


def test_items_in_drawer_omitted_defaults_match_skill_server_defaults() -> None:
    expected_literal_defaults = {
        "bt_command_service": "/lerobot_bt/run",
        "vlm_state_service": "/lerobot_bt/vlm_state",
        "legacy_vlm_result_service": "/lerobot_bt/vlm_result_legacy",
        "vlm_request_topic": "/lerobot_bt/vlm_request",
        "vlm_result_topic": "/lerobot_bt/vlm_result",
        "policy_variant": "act",
        "fps": 10,
        "display_data": True,
        "play_sounds": True,
        "reset_robot_on_startup": True,
        "reset_robot_before_skill": True,
        "camera_publish_fps": 10.0,
        "camera_publish_jpeg_quality": 80,
    }

    for field_name, expected_value in expected_literal_defaults.items():
        actual_value = _skill_server_literal_default(field_name)
        assert actual_value == expected_value, (
            f"SkillCommandServerConfig.{field_name} changed to {actual_value!r}; "
            f"update {ITEMS_IN_DRAWER_EXECUTOR.name} or this test accordingly"
        )

    for field_name in ("rename_map", "robot_action_processor", "robot_observation_processor"):
        default_node = _skill_server_default_node(field_name)
        assert isinstance(default_node, ast.Call), (
            f"SkillCommandServerConfig.{field_name} should keep an explicit default factory"
        )
