# Comment: executes this BT logic statement.
"""@file __init__.py
@brief Package entry for the Python execution layer of the LeRobot BT stack.

This module exposes the configuration dataclasses from `config.py` at the
package top-level so callers can import them from
`lerobot_bt_python` instead of the deeper module path. The module uses a
lazy `__getattr__` so importing the package does not immediately deserialize
or import heavy policy modules.

@details `__all__` lists the exported symbols supported by the package surface.
`__getattr__` lazily imports the actual dataclasses from `config.py` when they
are requested. This reduces import-time overhead and avoids importing optional
heavy dependencies unless the caller actually needs the types.
"""

# Comment: imports dependencies or symbols required by the module.
from __future__ import annotations

# Comment: imports dependencies or symbols required by the module.
from typing import Any

# Public symbols provided by this package. Keep in sync with the dataclasses
# defined in `config.py` that represent the runtime configuration.
# Comment: assigns or prepares a value used by later statements.
__all__ = [
    # Comment: executes this BT logic statement.
    "ObservationConditionConfig",
    # Comment: executes this BT logic statement.
    "PrimitiveSkillConfig",
    # Comment: executes this BT logic statement.
    "SkillCommandServerConfig",
    # Comment: executes this BT logic statement.
    "SkillTransitionConfig",
# Comment: closes a call, data structure, or multiline block.
]


# Comment: defines the function or method __getattr__.
def __getattr__(name: str) -> Any:
    # Comment: executes this BT logic statement.
    """@brief Lazily resolve exported dataclasses from `config.py`.

    When a caller does `from lerobot_bt_python import PrimitiveSkillConfig`,
    Python will request the attribute from this module. We intercept that
    lookup, import the real symbols from `config.py`, and return them. If the
    requested name is not in `__all__`, a normal AttributeError is raised.
    """
    # Comment: evaluates a condition and chooses the branch to run.
    if name not in __all__:
        # Preserve the normal attribute access semantics by raising AttributeError
        # Comment: raises an explicit error for the caller.
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    # Import here to avoid the cost at package import time. The imported
    # classes are lightweight dataclasses and will be returned directly.
    # Comment: imports dependencies or symbols required by the module.
    from .config import (
        # Comment: executes this BT logic statement.
        ObservationConditionConfig,
        # Comment: executes this BT logic statement.
        PrimitiveSkillConfig,
        # Comment: executes this BT logic statement.
        SkillCommandServerConfig,
        # Comment: executes this BT logic statement.
        SkillTransitionConfig,
    # Comment: closes a call, data structure, or multiline block.
    )

    # Map the exported name to the actual class object and return it.
    # Comment: assigns or prepares a value used by later statements.
    exported = {
        # Comment: executes this BT logic statement.
        "ObservationConditionConfig": ObservationConditionConfig,
        # Comment: executes this BT logic statement.
        "PrimitiveSkillConfig": PrimitiveSkillConfig,
        # Comment: executes this BT logic statement.
        "SkillCommandServerConfig": SkillCommandServerConfig,
        # Comment: executes this BT logic statement.
        "SkillTransitionConfig": SkillTransitionConfig,
    # Comment: closes a call, data structure, or multiline block.
    }
    # Comment: returns the computed value to the caller.
    return exported[name]
