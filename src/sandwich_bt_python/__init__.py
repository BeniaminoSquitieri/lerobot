"""Python execution layer for the sandwich Behavior Tree stack."""

from __future__ import annotations

from typing import Any

__all__ = [
    "ObservationConditionConfig",
    "PrimitiveSkillConfig",
    "RecoveryConfig",
    "RecoveryStepConfig",
    "SkillCommandServerConfig",
    "SkillTransitionConfig",
]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    from .config import (
        ObservationConditionConfig,
        PrimitiveSkillConfig,
        RecoveryConfig,
        RecoveryStepConfig,
        SkillCommandServerConfig,
        SkillTransitionConfig,
    )

    exported = {
        "ObservationConditionConfig": ObservationConditionConfig,
        "PrimitiveSkillConfig": PrimitiveSkillConfig,
        "RecoveryConfig": RecoveryConfig,
        "RecoveryStepConfig": RecoveryStepConfig,
        "SkillCommandServerConfig": SkillCommandServerConfig,
        "SkillTransitionConfig": SkillTransitionConfig,
    }
    return exported[name]
