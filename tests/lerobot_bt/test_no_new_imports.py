#!/usr/bin/env python

"""Static guard: no new runtime dependencies sneaking into edited Pass 2 modules.

Pass 2 was purely additive at the message-string level. No new imports
(beyond ``logging``, which was already added in Pass 1) should appear in the
edited modules. This test bans specific new dependencies that an
implementation agent might be tempted to introduce while reworking log calls.
"""

from __future__ import annotations

import ast
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

FORBIDDEN_IMPORT_ROOTS = (
    "structlog",
    "loguru",
    "rich.logging",
)


def _top_level_imports(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                names.add(f"{module}.{alias.name}" if module else alias.name)
    return names


@pytest.mark.parametrize("rel_path", EDITED_FILES)
def test_no_forbidden_imports(rel_path: str) -> None:
    source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
    imports = _top_level_imports(source)
    offenders = sorted(
        imp for imp in imports
        if any(imp == root or imp.startswith(root + ".") for root in FORBIDDEN_IMPORT_ROOTS)
    )
    assert not offenders, (
        f"{rel_path} unexpectedly imports {offenders}. "
        f"Pass 2 must not pull in new logging dependencies."
    )


def test_rclpy_logging_module_not_used_directly() -> None:
    """Inside ROS nodes, log routing must continue to flow through ``self.get_logger()``.

    Importing ``rclpy.logging`` at the top of ``server.py`` would suggest a
    rerouted logging path; reject that early.
    """
    source = (REPO_ROOT / "src" / "lerobot_bt_python" / "server.py").read_text(encoding="utf-8")
    imports = _top_level_imports(source)
    assert "rclpy.logging" not in imports, (
        "server.py must not import rclpy.logging at module top-level; "
        "use self.get_logger() inside ROS callbacks."
    )
