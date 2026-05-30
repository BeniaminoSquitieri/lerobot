#!/usr/bin/env python

"""Static safety checks for BT runtime and executor YAML profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
BT_CONFIG_DIR = REPO_ROOT / "src/lerobot_bt_runtime_cpp/config"
EXECUTOR_CONFIG_DIR = REPO_ROOT / "src/lerobot_bt_python"
MAX_SKILL_DURATION_S = 300.0


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path} must contain a YAML mapping"
    return data


def _executor_yaml_paths() -> list[Path]:
    return sorted(EXECUTOR_CONFIG_DIR.glob("*_executor.yaml"))


def _bt_yaml_paths() -> list[Path]:
    return sorted(BT_CONFIG_DIR.glob("*_bt.yaml"))


@pytest.mark.parametrize("path", _bt_yaml_paths(), ids=lambda path: path.name)
def test_bt_retry_limits_are_finite(path: Path) -> None:
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
        assert value > 0, f"{path}:{key} must be finite and positive"


@pytest.mark.parametrize("path", _executor_yaml_paths(), ids=lambda path: path.name)
def test_executor_vlm_timeout_is_enabled(path: Path) -> None:
    cfg = _load_yaml(path)

    assert float(cfg["vlm_timeout_s"]) > 0.0, f"{path}:vlm_timeout_s must be positive"


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
