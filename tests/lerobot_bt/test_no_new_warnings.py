#!/usr/bin/env python

"""Static guard: no new warning machinery in edited Pass 2 modules.

Asserts that the source files touched in the Pass 2 debuggability cleanup do
not introduce ``warnings.warn``, ``DeprecationWarning``, or
``PendingDeprecationWarning`` references. The Pass 1 deprecation logs use
``logging`` only and must remain the only deprecation surface.
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]

EDITED_FILES = (
    "src/lerobot_bt_python/server.py",
    "src/lerobot_bt_python/verification.py",
    "src/lerobot_bt_python/conditions.py",
    "src/lerobot_bt_python/executor.py",
    "src/lerobot_bt_python/config.py",
    "src/lerobot_bt_python/__init__.py",
)

FORBIDDEN_TOKENS = (
    "warnings.warn",
    "DeprecationWarning",
    "PendingDeprecationWarning",
)


@pytest.mark.parametrize("rel_path", EDITED_FILES)
def test_no_warning_machinery(rel_path: str) -> None:
    source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
    offenders = [token for token in FORBIDDEN_TOKENS if token in source]
    assert not offenders, (
        f"{rel_path} unexpectedly references {offenders}. Pass 2 must not introduce "
        f"Python warning machinery; use logging only."
    )
