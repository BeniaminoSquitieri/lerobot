#!/usr/bin/env python

"""Static AST contract for structured VLM log strings in server.py.

Scope is strictly limited to the two functions named below. The test does not
pin exact wording; it asserts that the structured key-value substrings appear
somewhere among the string-literal arguments to existing logger calls inside
each function.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = REPO_ROOT / "src" / "lerobot_bt_python" / "server.py"

# Substrings that mark structured log formatting. We require at least three of
# these to appear in the string-literal logger arguments of each function so
# the contract tolerates partial fields when a parsing path lacks skill/attempt.
STRUCTURED_TOKENS = ("event=", "skill=", "attempt=", "status=", "topic=")
MIN_TOKENS_REQUIRED = 3


def _server_class() -> ast.ClassDef:
    module = ast.parse(SERVER_PATH.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == "SkillCommandServer":
            return node
    raise AssertionError("SkillCommandServer class not found in server.py")


def _function(class_node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for child in class_node.body:
        if isinstance(child, ast.FunctionDef) and child.name == name:
            return child
    raise AssertionError(f"Method SkillCommandServer.{name} not found")


def _collect_logger_string_literals(func: ast.FunctionDef) -> list[str]:
    """Return the concatenated string content of every logger.* call inside ``func``.

    Recognizes both ``self.get_logger().LEVEL(...)`` calls and plain
    ``logger.LEVEL(...)`` calls. For each call, the first positional argument
    is inspected and any ``ast.Constant[str]`` or ``ast.JoinedStr`` (f-string)
    is reduced to its literal text fragments.
    """
    collected: list[str] = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        method_name = node.func.attr
        if method_name not in {"info", "warning", "error", "debug", "exception"}:
            continue
        # Accept either `self.get_logger().<level>(...)` or `<name>.<level>(...)`.
        receiver = node.func.value
        is_ros_logger = (
            isinstance(receiver, ast.Call)
            and isinstance(receiver.func, ast.Attribute)
            and receiver.func.attr == "get_logger"
        )
        is_module_logger = isinstance(receiver, ast.Name) and receiver.id == "logger"
        if not (is_ros_logger or is_module_logger):
            continue
        if not node.args:
            continue
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            collected.append(first_arg.value)
        elif isinstance(first_arg, ast.JoinedStr):
            parts: list[str] = []
            for piece in first_arg.values:
                if isinstance(piece, ast.Constant) and isinstance(piece.value, str):
                    parts.append(piece.value)
            collected.append("".join(parts))
    return collected


@pytest.mark.parametrize("func_name", ["_publish_vlm_request", "_handle_vlm_result_topic"])
def test_structured_tokens_present(func_name: str) -> None:
    class_node = _server_class()
    func = _function(class_node, func_name)
    literals = _collect_logger_string_literals(func)
    assert literals, f"No string-literal logger calls found in {func_name}"

    combined = "\n".join(literals)
    present = [token for token in STRUCTURED_TOKENS if token in combined]
    assert len(present) >= MIN_TOKENS_REQUIRED, (
        f"{func_name} should expose at least {MIN_TOKENS_REQUIRED} of "
        f"{STRUCTURED_TOKENS} in its logger string literals; found only {present}. "
        f"Literals: {literals!r}"
    )


def test_publish_vlm_request_has_event_tag() -> None:
    """The publication site must always include the event tag for log filtering."""
    class_node = _server_class()
    func = _function(class_node, "_publish_vlm_request")
    literals = _collect_logger_string_literals(func)
    assert any("event=" in lit for lit in literals), (
        f"_publish_vlm_request logger calls must include an event= tag; got {literals!r}"
    )
