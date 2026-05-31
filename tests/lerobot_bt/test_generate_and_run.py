#!/usr/bin/env python

"""ROS-free tests for generate-and-run workflow."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from lerobot_bt_python.bt_generation import generate_and_run


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/skills_registry.yaml"
SANDWICH_EXECUTOR = REPO_ROOT / "src/lerobot_bt_python/make_sandwich_executor.yaml"
MODEL_RESPONSE = REPO_ROOT / "tests/assets/vlm_planner/make_sandwich_valid.json"


def test_runner_command_is_constructed_correctly() -> None:
    assert generate_and_run.build_runner_command(
        Path("generated_bt/trees/make_sandwich.xml"),
        Path("generated_bt/config/make_sandwich_bt.yaml"),
    ) == [
        "ros2",
        "run",
        "lerobot_bt_runtime_cpp",
        "lerobot_bt_runner",
        "--ros-args",
        "--params-file",
        "generated_bt/config/make_sandwich_bt.yaml",
        "-p",
        "tree_xml_path:=generated_bt/trees/make_sandwich.xml",
    ]


def test_generate_and_run_no_run_generates_files_and_does_not_call_runner(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called with --no-run")

    monkeypatch.setattr(generate_and_run.subprocess, "run", fail_if_called)
    output_dir = tmp_path / "generated_bt"

    rc = generate_and_run.main([*_base_args(output_dir), "--planner", "template", "--no-run"])

    captured = capsys.readouterr()
    assert rc == 0
    assert (output_dir / "trees/make_sandwich.xml").exists()
    assert (output_dir / "config/make_sandwich_bt.yaml").exists()
    assert "runner command: ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner" in captured.out


def test_generation_failure_prevents_runner_execution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(generate_and_run.generate, "main", lambda argv: 1)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("runner should not start after generation failure")

    monkeypatch.setattr(generate_and_run.subprocess, "run", fail_if_called)

    rc = generate_and_run.main([*_base_args(tmp_path / "generated_bt"), "--planner", "template"])

    captured = capsys.readouterr()
    assert rc == 1
    assert "BT generation failed; not starting lerobot_bt_runner" in captured.err


def test_missing_generated_tree_or_config_fails_clearly(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(generate_and_run.generate, "main", lambda argv: 0)
    output_dir = tmp_path / "generated_bt"

    rc = generate_and_run.main([*_base_args(output_dir), "--planner", "template", "--no-run"])

    captured = capsys.readouterr()
    assert rc == 1
    assert "Expected generated file does not exist" in captured.err
    assert str(output_dir / "trees/make_sandwich.xml") in captured.err
    assert str(output_dir / "config/make_sandwich_bt.yaml") in captured.err


def test_generate_and_run_executes_runner_when_ros2_is_available(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "generated_bt"
    captured_command: list[str] = []

    monkeypatch.setattr(generate_and_run.shutil, "which", lambda name: "/usr/bin/ros2")

    def fake_run(command: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
        captured_command[:] = command
        return subprocess.CompletedProcess(command, 7)

    monkeypatch.setattr(generate_and_run.subprocess, "run", fake_run)

    rc = generate_and_run.main([*_base_args(output_dir), "--planner", "template"])

    assert rc == 7
    assert captured_command == generate_and_run.build_runner_command(
        output_dir / "trees/make_sandwich.xml",
        output_dir / "config/make_sandwich_bt.yaml",
    )


def test_missing_ros2_fails_actionably_after_generation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(generate_and_run.shutil, "which", lambda name: None)

    rc = generate_and_run.main([*_base_args(tmp_path / "generated_bt"), "--planner", "template"])

    captured = capsys.readouterr()
    assert rc == 127
    assert "ros2 command not found" in captured.err
    assert "Source ROS2 and the built workspace" in captured.err


def test_generate_and_run_model_response_no_run(tmp_path: Path) -> None:
    output_dir = tmp_path / "generated_bt"

    rc = generate_and_run.main(
        [
            *_base_args(output_dir),
            "--planner",
            "model-response",
            "--model-response-file",
            str(MODEL_RESPONSE),
            "--no-run",
        ]
    )

    assert rc == 0
    assert (output_dir / "plans/make_sandwich_linear_ir.json").exists()
    assert (output_dir / "trees/make_sandwich.xml").exists()
    assert (output_dir / "config/make_sandwich_bt.yaml").exists()


def test_generate_and_run_ros_service_no_run_with_monkeypatched_plan(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_request_plan_from_ros_service(task_name, planner_registry_payload, **kwargs):
        return json.dumps(
            {
                "task_name": "make_sandwich",
                "steps": [
                    {"kind": "vlm_gate", "name": "initial_scene_ready"},
                    {"kind": "robot_skill", "name": "place_first_toast"},
                    {"kind": "human_step", "name": "pour_ingredient"},
                    {"kind": "vlm_gate", "name": "ingredient_poured"},
                    {"kind": "vlm_gate", "name": "second_toast_ready"},
                    {"kind": "robot_skill", "name": "place_second_toast"},
                    {"kind": "vlm_gate", "name": "make_sandwich.task_complete"},
                ],
            }
        )

    monkeypatch.setattr(
        "lerobot_bt_python.bt_generation.ros_plan_client.request_plan_from_ros_service",
        fake_request_plan_from_ros_service,
    )
    output_dir = tmp_path / "generated_bt"

    rc = generate_and_run.main([*_base_args(output_dir), "--planner", "ros-service", "--no-run"])

    assert rc == 0
    assert (output_dir / "plans/make_sandwich_linear_ir.json").exists()
    assert (output_dir / "trees/make_sandwich.xml").exists()
    assert (output_dir / "config/make_sandwich_bt.yaml").exists()


def _base_args(output_dir: Path) -> list[str]:
    return [
        "--task",
        "make_sandwich",
        "--registry",
        str(REGISTRY_PATH),
        "--executor-yaml",
        str(SANDWICH_EXECUTOR),
        "--output-dir",
        str(output_dir),
    ]
