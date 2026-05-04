"""Package entry for the Python execution layer of the sandwich BT stack.

This module exposes the configuration dataclasses from `config.py` at the
package top-level so callers can import them from
`sandwich_bt_python` instead of the deeper module path. The module uses a
lazy `__getattr__` so importing the package does not immediately deserialize
or import heavy policy modules.

Design notes:
- `__all__` lists the exported symbols supported by the package surface.
- `__getattr__` lazily imports the actual dataclasses from `config.py` when
  they are requested. This reduces import-time overhead and avoids importing
  optional heavy dependencies unless the caller actually needs the types.
"""

from __future__ import annotations

from typing import Any

# Public symbols provided by this package. Keep in sync with the dataclasses
# defined in `config.py` that represent the runtime configuration.
__all__ = [
    "ObservationConditionConfig",
    "PrimitiveSkillConfig",
    "RecoveryConfig",
    "RecoveryStepConfig",
    "SkillCommandServerConfig",
    "SkillTransitionConfig",
]


def __getattr__(name: str) -> Any:
    """Lazily resolve exported dataclasses from `config.py`.

    When a caller does `from sandwich_bt_python import PrimitiveSkillConfig`,
    Python will request the attribute from this module. We intercept that
    lookup, import the real symbols from `config.py`, and return them. If the
    requested name is not in `__all__`, a normal AttributeError is raised.
    """
    if name not in __all__:
        # Preserve the normal attribute access semantics by raising AttributeError
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    # Import here to avoid the cost at package import time. The imported
    # classes are lightweight dataclasses and will be returned directly.
    from .config import (
        ObservationConditionConfig,
        PrimitiveSkillConfig,
        RecoveryConfig,
        RecoveryStepConfig,
        SkillCommandServerConfig,
        SkillTransitionConfig,
    )

    # Map the exported name to the actual class object and return it.
    exported = {
        "ObservationConditionConfig": ObservationConditionConfig,
        "PrimitiveSkillConfig": PrimitiveSkillConfig,
        "RecoveryConfig": RecoveryConfig,
        "RecoveryStepConfig": RecoveryStepConfig,
        "SkillCommandServerConfig": SkillCommandServerConfig,
        "SkillTransitionConfig": SkillTransitionConfig,
    }
    return exported[name]
