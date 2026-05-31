#!/usr/bin/env python

"""Offline script coverage for repo-local generated BT outputs."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_offline_script_uses_generated_bt_dir(tmp_path: Path) -> None:
    output_dir = tmp_path / "generated_bt"
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
    env["PYTHON_BIN"] = sys.executable
    env["GENERATED_BT_DIR"] = str(output_dir)

    result = subprocess.run(
        ["bash", "scripts/check_generated_bt_offline.sh"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "writing generated BT artifacts to" in result.stdout
    assert (output_dir / "trees/make_sandwich.xml").exists()
    assert (output_dir / "trees/set_breakfast_table.xml").exists()
    assert (output_dir / "trees/make_coffee.xml").exists()
    assert (output_dir / "trees/prepare_picnic_bag.xml").exists()
    assert (output_dir / "trees/items_in_drawer.xml").exists()
    assert (output_dir / "config/make_sandwich_bt.yaml").exists()
    assert (output_dir / "plans/make_sandwich_linear_ir.json").exists()
    assert (output_dir / "raw_model_responses/make_sandwich_raw_response.json").exists()
