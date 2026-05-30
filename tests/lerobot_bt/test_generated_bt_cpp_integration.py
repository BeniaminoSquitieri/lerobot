#!/usr/bin/env python

"""Optional generated XML/YAML + fake ROS2 server + C++ runner tests."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/test_generated_bt_with_fake_server.sh"


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
