#!/usr/bin/env python

"""Static guard: no timing measurements inside Batch B log sites.

Pass 2 explicitly excluded latency instrumentation. This test enforces that
``_publish_vlm_request`` and ``_handle_vlm_result_topic`` do not call any of
the common timing primitives.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = REPO_ROOT / "src" / "lerobot_bt_python" / "server.py"

# (module, attribute) pairs that constitute a timing measurement.
FORBIDDEN_CALLS = {
    ("time", "time"),
    ("time", "perf_counter"),
    ("time", "monotonic"),
    ("time", "monotonic_ns"),
    ("time", "perf_counter_ns"),
    ("datetime", "now"),
    ("datetime", "utcnow"),
}


def _server_method(name: str) -> ast.FunctionDef:
    module = ast.parse(SERVER_PATH.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == "SkillCommandServer":
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == name:
                    return child
    raise AssertionError(f"Method SkillCommandServer.{name} not found")


def _calls_in(func: ast.FunctionDef) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            value = node.func.value
            if isinstance(value, ast.Name):
                found.add((value.id, node.func.attr))
            elif isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
                # e.g. datetime.datetime.now -> (datetime, now) collapsed.
                found.add((value.attr, node.func.attr))
    return found


@pytest.mark.parametrize("func_name", ["_publish_vlm_request", "_handle_vlm_result_topic"])
def test_no_timing_in_log_sites(func_name: str) -> None:
    func = _server_method(func_name)
    calls = _calls_in(func)
    offenders = sorted(calls & FORBIDDEN_CALLS)
    assert not offenders, (
        f"{func_name} must not call timing primitives in Pass 2; found {offenders}."
    )
