from __future__ import annotations

import pytest

from sandwich_bt_python.config import ObservationConditionConfig, SkillTransitionConfig
from sandwich_bt_python.simulation import (
    MockCustomManipulator,
    MockServerConfig,
    MockSkillCommandExecutor,
    MockSkillConfig,
    MockSkillTransition,
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


def test_mock_executor_until_success_returns_success_without_timeout() -> None:
    robot = MockCustomManipulator()
    robot.connect()

    executor = MockSkillCommandExecutor(
        cfg=MockServerConfig(
            skills=[
                MockSkillConfig(
                    name="demo_skill",
                    transition=MockSkillTransition(mode="until_success", max_duration_s=0.1),
                )
            ],
        ),
        robot=robot,
    )

    result = executor.execute_skill("demo_skill")

    assert result.success
    assert result.status == "SUCCESS"
    assert robot.sent_actions
