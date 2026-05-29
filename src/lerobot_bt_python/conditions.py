"""@file conditions.py
@brief Helpers to evaluate observation-based termination conditions.

The executor consults these functions at every control loop iteration to
decide whether a rollout should continue, succeed, or fail. The functions are
designed to be simple, defensive, and explicit about type/shape errors so
misconfigured predicates fail fast.
"""

from collections.abc import Iterable
from typing import Any

import numpy as np

from .config import ObservationConditionConfig


def _to_scalar(value: Any) -> float:
    """Coerce an observation value to a Python float.

    Accepts either a scalar convertible to `float` or a 0-d / 1-element
    `numpy.ndarray`. If the array contains more than one element we raise an
    error because the condition system expects scalar-compatible inputs.
    """
    if isinstance(value, np.ndarray):
        # Defensive: only accept arrays containing exactly one element.
        if value.size != 1:
            raise ValueError(f"Expected a scalar-compatible array, got shape {value.shape}.")
        # Flatten to 1D and take the first (only) element.
        return float(value.reshape(-1)[0])
    # For other numeric-like objects, rely on float(...) conversion which will
    # raise a TypeError or ValueError for unsupported types.
    return float(value)


def evaluate_condition(condition: ObservationConditionConfig, observation: dict[str, Any]) -> bool:
    """Evaluate a single `ObservationConditionConfig` against an observation.

    Returns True if the condition holds, False otherwise. If the requested key
    is missing from `observation`, the condition is considered False. This
    conservative approach avoids accidental successes when inputs are missing.
    """
    # If the observation does not contain the requested key, treat as False.
    if condition.key not in observation:
        return False

    # Convert the observation value to a scalar float for comparisons.
    obs_value = _to_scalar(observation[condition.key])
    # Optionally compare against the absolute value.
    if condition.use_abs:
        obs_value = abs(obs_value)

    # Dispatch supported comparison operators.
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
        # 'between' requires a secondary bound; raise helpful error if missing.
        if condition.value_max is None:
            raise ValueError("Condition op='between' requires value_max.")
        return condition.value <= obs_value <= condition.value_max

    # Guard against unsupported operators to catch config typos early.
    raise ValueError(f"Unsupported condition op '{condition.op}'.")


def evaluate_all(conditions: Iterable[ObservationConditionConfig], observation: dict[str, Any]) -> bool:
    """Return True if all provided conditions hold against the observation.

    Used to implement the 'all_conditions' termination mode. An empty
    conditions iterable returns False to indicate there is nothing to satisfy.
    """
    conditions = list(conditions)
    if not conditions:
        return False
    return all(evaluate_condition(condition, observation) for condition in conditions)


def evaluate_any(conditions: Iterable[ObservationConditionConfig], observation: dict[str, Any]) -> bool:
    """Return True if any provided condition holds against the observation.

    Used for failure predicates where a single triggered condition should stop
    the rollout. An empty iterable returns False (no failure detected).
    """
    conditions = list(conditions)
    if not conditions:
        return False
    return any(evaluate_condition(condition, observation) for condition in conditions)
