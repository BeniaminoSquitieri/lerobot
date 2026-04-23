"""Condition evaluation helpers for skill termination.

Flow role:
1. The executor is running a live rollout of one learned primitive.
2. At every control step, it checks whether the rollout should:
   - keep running,
   - end with success,
   - end with failure.
3. These helpers evaluate the observation-based rules used in that decision.
"""

from collections.abc import Iterable
from typing import Any

import numpy as np

from .config import ObservationConditionConfig


def _to_scalar(value: Any) -> float:
    if isinstance(value, np.ndarray):
        if value.size != 1:
            raise ValueError(f"Expected a scalar-compatible array, got shape {value.shape}.")
        return float(value.reshape(-1)[0])
    return float(value)


def evaluate_condition(condition: ObservationConditionConfig, observation: dict[str, Any]) -> bool:
    # Reads one processed observation key and applies the configured comparison.
    if condition.key not in observation:
        return False

    obs_value = _to_scalar(observation[condition.key])
    if condition.use_abs:
        obs_value = abs(obs_value)

    if condition.op == "gt":
        return obs_value > condition.value
    if condition.op == "ge":
        return obs_value >= condition.value
    if condition.op == "lt":
        return obs_value < condition.value
    if condition.op == "le":
        return obs_value <= condition.value
    if condition.op == "eq":
        return obs_value == condition.value
    if condition.op == "between":
        if condition.value_max is None:
            raise ValueError("Condition op='between' requires value_max.")
        return condition.value <= obs_value <= condition.value_max

    raise ValueError(f"Unsupported condition op '{condition.op}'.")


def evaluate_all(conditions: Iterable[ObservationConditionConfig], observation: dict[str, Any]) -> bool:
    # Used for "all success conditions must be true".
    conditions = list(conditions)
    if not conditions:
        return False
    return all(evaluate_condition(condition, observation) for condition in conditions)


def evaluate_any(conditions: Iterable[ObservationConditionConfig], observation: dict[str, Any]) -> bool:
    # Used for "any failure condition can stop the rollout immediately".
    conditions = list(conditions)
    if not conditions:
        return False
    return any(evaluate_condition(condition, observation) for condition in conditions)
