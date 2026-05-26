# Comment: executes this BT logic statement.
"""@file conditions.py
@brief Helpers to evaluate observation-based termination conditions.

The executor consults these functions at every control loop iteration to
decide whether a rollout should continue, succeed, or fail. The functions are
designed to be simple, defensive, and explicit about type/shape errors so
misconfigured predicates fail fast.
"""

# Comment: imports dependencies or symbols required by the module.
from collections.abc import Iterable
# Comment: imports dependencies or symbols required by the module.
from typing import Any

# Comment: imports dependencies or symbols required by the module.
import numpy as np

# Comment: imports dependencies or symbols required by the module.
from .config import ObservationConditionConfig


# Comment: defines the function or method _to_scalar.
def _to_scalar(value: Any) -> float:
    # Comment: executes this BT logic statement.
    """Coerce an observation value to a Python float.

    Accepts either a scalar convertible to `float` or a 0-d / 1-element
    `numpy.ndarray`. If the array contains more than one element we raise an
    error because the condition system expects scalar-compatible inputs.
    """
    # Comment: evaluates a condition and chooses the branch to run.
    if isinstance(value, np.ndarray):
        # Defensive: only accept arrays containing exactly one element.
        # Comment: evaluates a condition and chooses the branch to run.
        if value.size != 1:
            # Comment: raises an explicit error for the caller.
            raise ValueError(f"Expected a scalar-compatible array, got shape {value.shape}.")
        # Flatten to 1D and take the first (only) element.
        # Comment: returns the computed value to the caller.
        return float(value.reshape(-1)[0])
    # For other numeric-like objects, rely on float(...) conversion which will
    # raise a TypeError or ValueError for unsupported types.
    # Comment: returns the computed value to the caller.
    return float(value)


# Comment: defines the function or method evaluate_condition.
def evaluate_condition(condition: ObservationConditionConfig, observation: dict[str, Any]) -> bool:
    # Comment: executes this BT logic statement.
    """Evaluate a single `ObservationConditionConfig` against an observation.

    Returns True if the condition holds, False otherwise. If the requested key
    is missing from `observation`, the condition is considered False. This
    conservative approach avoids accidental successes when inputs are missing.
    """
    # If the observation does not contain the requested key, treat as False.
    # Comment: evaluates a condition and chooses the branch to run.
    if condition.key not in observation:
        # Comment: returns the computed value to the caller.
        return False

    # Convert the observation value to a scalar float for comparisons.
    # Comment: assigns or prepares a value used by later statements.
    obs_value = _to_scalar(observation[condition.key])
    # Optionally compare against the absolute value.
    # Comment: evaluates a condition and chooses the branch to run.
    if condition.use_abs:
        # Comment: assigns or prepares a value used by later statements.
        obs_value = abs(obs_value)

    # Dispatch supported comparison operators.
    # Comment: evaluates a condition and chooses the branch to run.
    if condition.op == "gt":
        # Comment: returns the computed value to the caller.
        return obs_value > condition.value
    # Comment: evaluates a condition and chooses the branch to run.
    if condition.op == "ge":
        # Comment: returns the computed value to the caller.
        return obs_value >= condition.value
    # Comment: evaluates a condition and chooses the branch to run.
    if condition.op == "lt":
        # Comment: returns the computed value to the caller.
        return obs_value < condition.value
    # Comment: evaluates a condition and chooses the branch to run.
    if condition.op == "le":
        # Comment: returns the computed value to the caller.
        return obs_value <= condition.value
    # Comment: evaluates a condition and chooses the branch to run.
    if condition.op == "eq":
        # Comment: returns the computed value to the caller.
        return obs_value == condition.value
    # Comment: evaluates a condition and chooses the branch to run.
    if condition.op == "between":
        # 'between' requires a secondary bound; raise helpful error if missing.
        # Comment: evaluates a condition and chooses the branch to run.
        if condition.value_max is None:
            # Comment: raises an explicit error for the caller.
            raise ValueError("Condition op='between' requires value_max.")
        # Comment: returns the computed value to the caller.
        return condition.value <= obs_value <= condition.value_max

    # Guard against unsupported operators to catch config typos early.
    # Comment: raises an explicit error for the caller.
    raise ValueError(f"Unsupported condition op '{condition.op}'.")


# Comment: defines the function or method evaluate_all.
def evaluate_all(conditions: Iterable[ObservationConditionConfig], observation: dict[str, Any]) -> bool:
    # Comment: executes this BT logic statement.
    """Return True if all provided conditions hold against the observation.

    Used to implement the 'all_conditions' termination mode. An empty
    conditions iterable returns False to indicate there is nothing to satisfy.
    """
    # Comment: assigns or prepares a value used by later statements.
    conditions = list(conditions)
    # Comment: evaluates a condition and chooses the branch to run.
    if not conditions:
        # Comment: returns the computed value to the caller.
        return False
    # Comment: returns the computed value to the caller.
    return all(evaluate_condition(condition, observation) for condition in conditions)


# Comment: defines the function or method evaluate_any.
def evaluate_any(conditions: Iterable[ObservationConditionConfig], observation: dict[str, Any]) -> bool:
    # Comment: executes this BT logic statement.
    """Return True if any provided condition holds against the observation.

    Used for failure predicates where a single triggered condition should stop
    the rollout. An empty iterable returns False (no failure detected).
    """
    # Comment: assigns or prepares a value used by later statements.
    conditions = list(conditions)
    # Comment: evaluates a condition and chooses the branch to run.
    if not conditions:
        # Comment: returns the computed value to the caller.
        return False
    # Comment: returns the computed value to the caller.
    return any(evaluate_condition(condition, observation) for condition in conditions)
