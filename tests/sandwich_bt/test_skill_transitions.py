from __future__ import annotations

from types import SimpleNamespace

import pytest

from sandwich_bt_python.config import (
    ObservationConditionConfig,
    PrimitiveSkillConfig,
    SkillCommandServerConfig,
    SkillTransitionConfig,
)


def test_until_success_requires_success_conditions() -> None:
    with pytest.raises(ValueError, match="requires at least one success_condition"):
        SkillTransitionConfig(mode="until_success")


def test_until_success_accepts_explicit_success_conditions() -> None:
    cfg = SkillTransitionConfig(
        mode="until_success",
        success_conditions=[ObservationConditionConfig(key="gripper", op="gt", value=0.5)],
    )

    assert cfg.mode == "until_success"
    assert len(cfg.success_conditions) == 1


def test_skill_config_rejects_todo_model_placeholder() -> None:
    with pytest.raises(ValueError, match="placeholder checkpoint"):
        PrimitiveSkillConfig(
            name="demo_skill",
            dataset_repo_id="demo/dataset",
            task="demo",
            policy=SimpleNamespace(pretrained_path="TODO_MODEL_DEMO"),
        )


def test_server_config_rejects_duplicate_skill_names() -> None:
    with pytest.raises(ValueError, match="Duplicate skill names"):
        SkillCommandServerConfig(
            robot=SimpleNamespace(cameras={"wrist": object()}),
            skills=[
                SimpleNamespace(name="demo_skill"),
                SimpleNamespace(name="demo_skill"),
            ],
        )


def test_server_config_rejects_missing_expected_skill() -> None:
    with pytest.raises(ValueError, match="missing BT-required skill"):
        SkillCommandServerConfig(
            robot=SimpleNamespace(cameras={"wrist": object()}),
            skills=[SimpleNamespace(name="demo_skill")],
            expected_skill_names=["demo_skill", "missing_skill"],
        )


def test_server_config_rejects_missing_required_camera() -> None:
    with pytest.raises(ValueError, match="missing required camera"):
        SkillCommandServerConfig(
            robot=SimpleNamespace(cameras={"wrist": object()}),
            skills=[SimpleNamespace(name="demo_skill")],
            required_cameras=["wrist", "left"],
        )


def test_server_config_rejects_empty_camera_config() -> None:
    with pytest.raises(ValueError, match="At least one robot camera"):
        SkillCommandServerConfig(
            robot=SimpleNamespace(cameras={}),
            skills=[SimpleNamespace(name="demo_skill")],
        )
