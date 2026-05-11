from __future__ import annotations

import pytest

from sandwich_bt_python.config import ObservationConditionConfig, SkillTransitionConfig


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
