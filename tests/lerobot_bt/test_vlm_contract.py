#!/usr/bin/env python

from __future__ import annotations

import ast
import importlib
import re
import warnings
from pathlib import Path
from types import SimpleNamespace

import pytest

from lerobot_bt_python.verification import (
    VLM_FAILURE,
    VLM_NEEDS_MANUAL_HELP,
    VLM_PENDING,
    VLM_RUNNING,
    VLM_SUCCESS,
    VLM_WAIT_HUMAN,
    SceneVerdictStore,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
COMMENT_STRIP_PATTERN = re.compile(r"^\s*# Comment:.*$")


def _module_ast(rel_path: str) -> ast.Module:
    return ast.parse((REPO_ROOT / rel_path).read_text(encoding="utf-8"))


def _class_method(module: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return child
    raise AssertionError(f"Method {class_name}.{method_name} not found")


def _find_dict_assignment(function_node: ast.FunctionDef, variable_name: str) -> ast.Dict:
    for node in ast.walk(function_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable_name:
                    if isinstance(node.value, ast.Dict):
                        return node.value
    raise AssertionError(f"Dictionary assignment for {variable_name} not found")


def _dict_literal_items(dict_node: ast.Dict) -> dict[str, ast.AST]:
    items: dict[str, ast.AST] = {}
    for key_node, value_node in zip(dict_node.keys, dict_node.values, strict=True):
        if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
            items[key_node.value] = value_node
    return items


def _module_constant_dict(module: ast.Module, name: str) -> dict[str, str]:
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name and isinstance(node.value, ast.Dict):
                    result: dict[str, str] = {}
                    for key_node, value_node in zip(node.value.keys, node.value.values, strict=True):
                        if (
                            isinstance(key_node, ast.Constant)
                            and isinstance(key_node.value, str)
                            and isinstance(value_node, ast.Constant)
                            and isinstance(value_node.value, str)
                        ):
                            result[key_node.value] = value_node.value
                    return result
    raise AssertionError(f"Constant dict {name} not found")


def _skill_server_config_default(field_name: str) -> str:
    module = _module_ast("src/lerobot_bt_python/config.py")
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == "SkillCommandServerConfig":
            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    if child.target.id == field_name and isinstance(child.value, ast.Constant):
                        value = child.value.value
                        if isinstance(value, str):
                            return value
    raise AssertionError(f"Default for {field_name} not found")


def test_active_request_schema():
    module = _module_ast("src/lerobot_bt_python/server.py")
    publish_fn = _class_method(module, "SkillCommandServer", "_publish_vlm_request")
    payload = _find_dict_assignment(publish_fn, "payload")
    payload_items = _dict_literal_items(payload)

    required_keys = {
        "event",
        "skill_name",
        "attempt_id",
        "status",
        "message",
        "task",
        "allowed_statuses",
        "allowed_next_actions",
    }
    assert required_keys.issubset(set(payload_items))

    attempt_id_node = payload_items["attempt_id"]
    assert isinstance(attempt_id_node, ast.Call)
    assert isinstance(attempt_id_node.func, ast.Name)
    assert attempt_id_node.func.id == "int"

    allowed_statuses_node = payload_items["allowed_statuses"]
    assert isinstance(allowed_statuses_node, ast.List)
    allowed_statuses = {
        elt.value
        for elt in allowed_statuses_node.elts
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
    }
    assert {
        "PENDING",
        "RUNNING",
        "WAIT_HUMAN",
        "MANUAL_INTERVENTION_REQUIRED",
        "SUCCESS",
        "FAILURE",
    }.issubset(allowed_statuses)


def test_active_result_schema():
    bridge_module = _module_ast("src/lerobot_bt_python/bt_vlm_bridge.py")
    bridge_handler = _class_method(bridge_module, "BtPandaVlmBridge", "_handle_panda_status")
    result_payload = _find_dict_assignment(bridge_handler, "result_payload")
    payload_items = _dict_literal_items(result_payload)

    assert {"skill_name", "attempt_id", "status", "message"}.issubset(set(payload_items))

    attempt_id_node = payload_items["attempt_id"]
    attempt_id_expr = ast.unparse(attempt_id_node)
    assert attempt_id_expr.startswith("int(")
    assert "active_request.get(\"attempt_id\", 0)" in attempt_id_expr or "active_request.get('attempt_id', 0)" in attempt_id_expr

    panda_map = _module_constant_dict(bridge_module, "PANDA_TO_BT_STATUS")
    mapped_values = set(panda_map.values())
    assert {VLM_PENDING, VLM_RUNNING, VLM_SUCCESS, VLM_FAILURE}.issubset(mapped_values)

    expected_vocabulary = {
        VLM_PENDING,
        VLM_RUNNING,
        VLM_WAIT_HUMAN,
        VLM_NEEDS_MANUAL_HELP,
        VLM_SUCCESS,
        VLM_FAILURE,
    }
    assert VLM_PENDING in expected_vocabulary


def test_topic_names_are_stable():
    bridge_module = _module_ast("src/lerobot_bt_python/bt_vlm_bridge.py")

    request_topic = None
    result_topic = None
    for node in bridge_module.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id == "BT_VLM_REQUEST_TOPIC" and isinstance(node.value, ast.Constant):
                request_topic = node.value.value
            if node.targets[0].id == "BT_VLM_RESULT_TOPIC" and isinstance(node.value, ast.Constant):
                result_topic = node.value.value

    assert request_topic == "/lerobot_bt/vlm_request"
    assert result_topic == "/lerobot_bt/vlm_result"
    assert _skill_server_config_default("vlm_request_topic") == "/lerobot_bt/vlm_request"
    assert _skill_server_config_default("vlm_result_topic") == "/lerobot_bt/vlm_result"


def test_legacy_service_name_default():
    config_module = pytest.importorskip("lerobot_bt_python.config", reason="lerobot_bt_python.config import unavailable")

    primitive_skill = config_module.PrimitiveSkillConfig(
        name="dummy_skill",
        dataset_repo_id="dummy/repo",
        task="dummy task",
        policy=SimpleNamespace(pretrained_path="dummy/checkpoint"),
    )
    cfg = config_module.SkillCommandServerConfig(
        robot=SimpleNamespace(cameras={"cam0": object()}),
        skills=[primitive_skill],
        display_data=False,
        play_sounds=False,
        reset_robot_on_startup=False,
        reset_robot_before_skill=False,
    )

    assert cfg.legacy_vlm_result_service == "/lerobot_bt/vlm_result_legacy"


def test_legacy_srv_type_importable():
    srv_module = pytest.importorskip(
        "lerobot_bt_interfaces.srv",
        reason="ROS2 interface bindings are not available in this environment",
    )
    if not hasattr(srv_module, "ReportSkillVerification"):
        pytest.skip("Generated ReportSkillVerification binding is unavailable in this environment")


def test_pending_status_on_timeout():
    time_now = [100.0]
    registry = SceneVerdictStore(
        known_skill_names={"test_skill"},
        vlm_timeout_s=30.0,
        clock=lambda: time_now[0],
    )

    opened = registry.begin_attempt("test_skill")
    assert opened.status == VLM_PENDING

    latest = registry.get_latest("test_skill")
    assert latest is not None
    assert latest.status == VLM_PENDING

    running_update = registry.report(
        skill_name="test_skill",
        attempt_id=0,
        status=VLM_RUNNING,
        message="still checking",
    )
    assert running_update.accepted
    assert running_update.snapshot is not None
    assert running_update.snapshot.status == VLM_RUNNING

    time_now[0] = 129.0
    late_but_not_timed_out = registry.get_latest("test_skill")
    assert late_but_not_timed_out is not None
    assert late_but_not_timed_out.status in {VLM_PENDING, VLM_RUNNING}


def test_no_warning_at_import():
    pytest.importorskip("rclpy", reason="rclpy is not available")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.import_module("lerobot_bt_python.server")
        importlib.import_module("lerobot_bt_python.bt_vlm_bridge")

    deprecation = [
        w
        for w in caught
        if issubclass(w.category, (DeprecationWarning, PendingDeprecationWarning))
    ]
    assert deprecation == []


def test_comment_strip_safety():
    assert COMMENT_STRIP_PATTERN.match("# Comment: imports dependencies")
    assert COMMENT_STRIP_PATTERN.match("    # Comment: executes this BT logic statement.")

    preserved_comment_examples = [
        "# TODO: keep this",
        "# FIXME: keep this",
        "# NOTE: keep this",
        "# WARNING: keep this",
        "# XXX: keep this",
        "# HACK: keep this",
        "# noqa: F401",
        "# type: ignore[attr-defined]",
        "# pragma: no cover",
        "# https://example.com/some/context",
        "# BT-1234 keep this rationale",
    ]
    for line in preserved_comment_examples:
        assert COMMENT_STRIP_PATTERN.match(line) is None
