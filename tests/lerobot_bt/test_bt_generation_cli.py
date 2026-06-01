#!/usr/bin/env python

"""CLI tests for deterministic BT generation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

from lerobot_bt_python.bt_generation.static_checks import validate_xml_yaml_blackboard_keys


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/skills_registry.yaml"
SANDWICH_EXECUTOR = REPO_ROOT / "src/lerobot_bt_python/make_sandwich_executor.yaml"
BREAKFAST_EXECUTOR = REPO_ROOT / "src/lerobot_bt_python/set_breakfast_table_executor.yaml"
ASSET_DIR = REPO_ROOT / "tests/assets/vlm_planner"


def test_cli_generates_make_sandwich(tmp_path: Path) -> None:
    tree = tmp_path / "generated_make_sandwich.xml"
    config = tmp_path / "generated_make_sandwich_bt.yaml"

    result = _run_cli("make_sandwich", SANDWICH_EXECUTOR, tree, config)

    assert result.returncode == 0, result.stderr
    assert "human_step:" in result.stdout
    ET.parse(tree)
    cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
    bt_params = cfg["lerobot_bt_runner"]["ros__parameters"]["bt"]
    assert bt_params["place_first_toast_max_attempts"] == -1
    assert bt_params["place_second_toast_max_attempts"] == -1
    assert bt_params["place_first_toast_timeout_s"] == 120.0
    assert bt_params["place_second_toast_timeout_s"] == 120.0


def test_cli_output_dir_template_writes_standard_paths(tmp_path: Path) -> None:
    output_dir = tmp_path / "generated_bt"
    tree = output_dir / "trees/make_sandwich.xml"
    config = output_dir / "config/make_sandwich_bt.yaml"
    manifest = output_dir / "manifests/make_sandwich_manifest.json"

    result = _run_cli_args(
        [
            "--task",
            "make_sandwich",
            "--planner",
            "template",
            "--output-dir",
            str(output_dir),
        ],
        SANDWICH_EXECUTOR,
    )

    assert result.returncode == 0, result.stderr
    assert f"wrote tree: {tree}" in result.stdout
    assert f"wrote config: {config}" in result.stdout
    assert f"wrote manifest: {manifest}" in result.stdout
    ET.parse(tree)
    yaml.safe_load(config.read_text(encoding="utf-8"))
    assert validate_xml_yaml_blackboard_keys(tree, config) == []
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_data["task_name"] == "make_sandwich"
    assert manifest_data["planner"] == "template"
    assert manifest_data["tree_xml_path"] == str(tree)
    assert manifest_data["bt_yaml_path"] == str(config)
    assert "linear_ir_path" not in manifest_data
    assert "raw_response_path" not in manifest_data


def test_cli_output_dir_model_response_writes_plan_tree_config_and_raw_response(tmp_path: Path) -> None:
    output_dir = tmp_path / "generated_bt"
    plan = output_dir / "plans/make_sandwich_linear_ir.json"
    tree = output_dir / "trees/make_sandwich.xml"
    config = output_dir / "config/make_sandwich_bt.yaml"
    raw_response = output_dir / "raw_model_responses/make_sandwich_raw_response.json"
    manifest = output_dir / "manifests/make_sandwich_manifest.json"

    result = _run_cli_args(
        [
            "--task",
            "make_sandwich",
            "--planner",
            "model-response",
            "--model-response-file",
            str(ASSET_DIR / "make_sandwich_valid.json"),
            "--output-dir",
            str(output_dir),
        ],
        SANDWICH_EXECUTOR,
    )

    assert result.returncode == 0, result.stderr
    assert f"wrote plan: {plan}" in result.stdout
    assert f"wrote tree: {tree}" in result.stdout
    assert f"wrote config: {config}" in result.stdout
    assert f"wrote raw response: {raw_response}" in result.stdout
    assert f"wrote manifest: {manifest}" in result.stdout
    assert yaml.safe_load(plan.read_text(encoding="utf-8"))["task_name"] == "make_sandwich"
    assert raw_response.read_text(encoding="utf-8") == (ASSET_DIR / "make_sandwich_valid.json").read_text(
        encoding="utf-8"
    )
    ET.parse(tree)
    yaml.safe_load(config.read_text(encoding="utf-8"))
    assert validate_xml_yaml_blackboard_keys(tree, config) == []
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_data["planner"] == "model-response"
    assert manifest_data["linear_ir_path"] == str(plan)
    assert manifest_data["raw_response_path"] == str(raw_response)
    assert len(manifest_data["linear_ir_sha256"]) == 64


def test_cli_generates_set_breakfast_table(tmp_path: Path) -> None:
    tree = tmp_path / "generated_set_breakfast_table.xml"
    config = tmp_path / "generated_set_breakfast_table_bt.yaml"

    result = _run_cli("set_breakfast_table", BREAKFAST_EXECUTOR, tree, config)

    assert result.returncode == 0, result.stderr
    ET.parse(tree)
    yaml.safe_load(config.read_text(encoding="utf-8"))


def test_cli_explicit_paths_win_over_output_dir(tmp_path: Path) -> None:
    output_dir = tmp_path / "generated_bt"
    tree = tmp_path / "explicit.xml"
    config = tmp_path / "explicit_bt.yaml"

    result = _run_cli_args(
        [
            "--task",
            "make_sandwich",
            "--planner",
            "template",
            "--output-dir",
            str(output_dir),
            "--out-tree",
            str(tree),
            "--out-config",
            str(config),
        ],
        SANDWICH_EXECUTOR,
    )

    assert result.returncode == 0, result.stderr
    assert f"wrote tree: {tree}" in result.stdout
    assert f"wrote config: {config}" in result.stdout
    assert tree.exists()
    assert config.exists()
    assert not (output_dir / "trees/make_sandwich.xml").exists()
    assert not (output_dir / "config/make_sandwich_bt.yaml").exists()


def test_cli_unknown_task_fails_without_outputs(tmp_path: Path) -> None:
    tree = tmp_path / "bad.xml"
    config = tmp_path / "bad.yaml"

    result = _run_cli("unknown_task", SANDWICH_EXECUTOR, tree, config)

    assert result.returncode != 0
    assert "Unknown task_name" in result.stderr
    assert not tree.exists()
    assert not config.exists()


def test_cli_missing_one_explicit_output_path_fails(tmp_path: Path) -> None:
    tree = tmp_path / "bad.xml"

    result = _run_cli_args(
        [
            "--task",
            "make_sandwich",
            "--out-tree",
            str(tree),
        ],
        SANDWICH_EXECUTOR,
    )

    assert result.returncode != 0
    assert "--out-tree and --out-config must be provided together" in result.stderr
    assert not tree.exists()


def _run_cli(task: str, executor_yaml: Path, out_tree: Path, out_config: Path) -> subprocess.CompletedProcess[str]:
    return _run_cli_args(
        [
            "--task",
            task,
            "--out-tree",
            str(out_tree),
            "--out-config",
            str(out_config),
        ],
        executor_yaml,
    )


def _run_cli_args(args: list[str], executor_yaml: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "lerobot_bt_python.bt_generation.generate",
            "--registry",
            str(REGISTRY_PATH),
            "--executor-yaml",
            str(executor_yaml),
            *args,
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
