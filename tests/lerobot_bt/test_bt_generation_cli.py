#!/usr/bin/env python

"""CLI tests for deterministic BT generation."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/skills_registry.yaml"
SANDWICH_EXECUTOR = REPO_ROOT / "src/lerobot_bt_python/make_sandwich_executor.yaml"
BREAKFAST_EXECUTOR = REPO_ROOT / "src/lerobot_bt_python/set_breakfast_table_executor.yaml"


def test_cli_generates_make_sandwich(tmp_path: Path) -> None:
    tree = tmp_path / "generated_make_sandwich.xml"
    config = tmp_path / "generated_make_sandwich_bt.yaml"

    result = _run_cli("make_sandwich", SANDWICH_EXECUTOR, tree, config)

    assert result.returncode == 0, result.stderr
    assert "human_step:" in result.stdout
    ET.parse(tree)
    cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
    assert cfg["lerobot_bt_runner"]["ros__parameters"]["bt"]["place_first_toast_max_attempts"] == -1


def test_cli_generates_set_breakfast_table(tmp_path: Path) -> None:
    tree = tmp_path / "generated_set_breakfast_table.xml"
    config = tmp_path / "generated_set_breakfast_table_bt.yaml"

    result = _run_cli("set_breakfast_table", BREAKFAST_EXECUTOR, tree, config)

    assert result.returncode == 0, result.stderr
    ET.parse(tree)
    yaml.safe_load(config.read_text(encoding="utf-8"))


def test_cli_unknown_task_fails_without_outputs(tmp_path: Path) -> None:
    tree = tmp_path / "bad.xml"
    config = tmp_path / "bad.yaml"

    result = _run_cli("unknown_task", SANDWICH_EXECUTOR, tree, config)

    assert result.returncode != 0
    assert "Unknown task_name" in result.stderr
    assert not tree.exists()
    assert not config.exists()


def _run_cli(task: str, executor_yaml: Path, out_tree: Path, out_config: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "lerobot_bt_python.bt_generation.generate",
            "--task",
            task,
            "--registry",
            str(REGISTRY_PATH),
            "--executor-yaml",
            str(executor_yaml),
            "--out-tree",
            str(out_tree),
            "--out-config",
            str(out_config),
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
