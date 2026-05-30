#!/usr/bin/env python

"""Optional generated XML/YAML + fake ROS2 server + C++ runner tests."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/test_generated_bt_with_fake_server.sh"


def test_cpp_script_preflight_fails_cleanly_without_ros2() -> None:
    env = os.environ.copy()
    env["PATH"] = "/usr/bin:/bin"
    if shutil.which("ros2", path=env["PATH"]) is not None:
        pytest.skip("Cannot simulate missing ros2 because ros2 is visible in the base PATH.")
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    env["PYTHON_BIN"] = sys.executable

    result = subprocess.run(
        ["/bin/bash", str(SCRIPT), "success_all", "success"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )

    combined_output = result.stdout + result.stderr
    assert result.returncode == 2
    assert "ERROR: ROS2 not found" in combined_output
    assert "ModuleNotFoundError" not in combined_output
    assert "fake_bt_executor_server" not in combined_output


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [
        ("success_all", "success"),
        ("initial_scene_failed", "failure"),
    ],
)
def test_generated_bt_cpp_runner_with_fake_server(scenario: str, expected: str) -> None:
    if os.environ.get("LEROBOT_RUN_CPP_BT_INTEGRATION") != "1":
        pytest.skip("Set LEROBOT_RUN_CPP_BT_INTEGRATION=1 to run ROS2/C++ BT integration.")
    if shutil.which("ros2") is None:
        pytest.skip("ros2 CLI is not available.")

    result = subprocess.run(
        [str(SCRIPT), scenario, expected],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
