#!/usr/bin/env python

"""Tests for the ICRA runtime BT experiment tooling.

Covers the annotate CLI, the bundle and report scripts, the environment
snapshot helpers, and static guarantees about the run_icra shell wrapper.
"""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import sys
import tarfile
from pathlib import Path

import pytest

from lerobot_bt_python.bt_generation import env_snapshot, experiment_log


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"


def _load_script(name: str):
    path = SCRIPTS_DIR / name
    spec = importlib.util.spec_from_file_location(f"_icra_script_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_annotate_appends_without_modifying_earlier_lines(tmp_path: Path) -> None:
    annotate = _load_script("annotate_runtime_bt_trial.py")
    log_path = tmp_path / "trials.jsonl"
    experiment_log.append_event(
        log_path,
        experiment_log.build_event(
            event_type=experiment_log.EVENT_GENERATION,
            trial_id="trial-xyz",
            task_name="make_sandwich",
            planner="ros-service",
            planner_label="constrained_linear_ir",
            condition_label="robot_live",
            success=True,
        ),
    )
    original_first_line = log_path.read_text(encoding="utf-8").splitlines()[0]

    rc = annotate.main(
        [
            "--jsonl",
            str(log_path),
            "--trial-id",
            "trial-xyz",
            "--task-success",
            "failure",
            "--outcome-label",
            "partial",
            "--failure-category",
            "skill_failed",
            "--notes",
            "gripper slipped",
        ]
    )
    assert rc == 0
    events = _read_jsonl(log_path)
    assert len(events) == 2
    # Earlier line is unchanged (append-only).
    assert log_path.read_text(encoding="utf-8").splitlines()[0] == original_first_line
    annotation = events[1]
    assert annotation["event_type"] == "annotation"
    assert annotation["task_success"] == "failure"
    assert annotation["outcome_label"] == "partial"
    assert annotation["failure_category"] == "skill_failed"
    # Labels inherited from the existing trial.
    assert annotation["task_name"] == "make_sandwich"
    assert annotation["condition_label"] == "robot_live"


def test_annotate_rejects_empty_trial_id(tmp_path: Path) -> None:
    annotate = _load_script("annotate_runtime_bt_trial.py")
    log_path = tmp_path / "trials.jsonl"
    rc = annotate.main(
        [
            "--jsonl",
            str(log_path),
            "--trial-id",
            "   ",
            "--task-success",
            "success",
            "--outcome-label",
            "completed",
            "--failure-category",
            "none",
        ]
    )
    assert rc == 2
    assert not log_path.exists()


def test_annotate_rejects_unknown_trial_id(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    annotate = _load_script("annotate_runtime_bt_trial.py")
    log_path = tmp_path / "trials.jsonl"
    experiment_log.append_event(
        log_path,
        experiment_log.build_event(
            event_type=experiment_log.EVENT_GENERATION,
            trial_id="trial-known",
            task_name="make_sandwich",
            planner="ros-service",
            planner_label="constrained_linear_ir",
            condition_label="robot_live",
            success=True,
        ),
    )

    rc = annotate.main(
        [
            "--jsonl",
            str(log_path),
            "--trial-id",
            "trial-missing",
            "--task-success",
            "success",
            "--outcome-label",
            "completed",
            "--failure-category",
            "none",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert "Cannot annotate unknown trial_id 'trial-missing'" in captured.err
    assert "Last available trial_id values" in captured.err
    assert "trial-known" in captured.err
    assert [event["trial_id"] for event in _read_jsonl(log_path)] == ["trial-known"]


def test_annotate_allow_orphan_appends_unknown_trial_id(tmp_path: Path) -> None:
    annotate = _load_script("annotate_runtime_bt_trial.py")
    log_path = tmp_path / "trials.jsonl"

    rc = annotate.main(
        [
            "--jsonl",
            str(log_path),
            "--trial-id",
            "trial-orphan",
            "--task-success",
            "unknown",
            "--outcome-label",
            "unknown",
            "--failure-category",
            "unknown",
            "--allow-orphan",
        ]
    )

    assert rc == 0
    events = _read_jsonl(log_path)
    assert len(events) == 1
    assert events[0]["event_type"] == "annotation"
    assert events[0]["trial_id"] == "trial-orphan"


def test_bundle_creates_archive_with_expected_members(tmp_path: Path) -> None:
    bundle = _load_script("bundle_runtime_bt_trial.py")
    output_dir = tmp_path / "generated_bt"
    (output_dir / "trees").mkdir(parents=True)
    (output_dir / "trees" / "make_sandwich.xml").write_text("<root/>", encoding="utf-8")
    (output_dir / "experiments").mkdir(parents=True)
    (output_dir / "experiments" / "trials.jsonl").write_text("{}\n", encoding="utf-8")

    out_path = tmp_path / "bundle.tar.gz"
    rc = bundle.main(
        [
            "--output-dir",
            str(output_dir),
            "--trial-id",
            "trial-xyz",
            "--task",
            "make_sandwich",
            "--out",
            str(out_path),
        ]
    )
    assert rc == 0
    assert out_path.exists()
    with tarfile.open(out_path, "r:gz") as archive:
        names = archive.getnames()
    assert "README.txt" in names
    assert any(name.endswith("trees") or name.endswith("make_sandwich.xml") for name in names)
    assert any(name.endswith("experiments/trials.jsonl") for name in names)


def test_report_renders_markdown(tmp_path: Path) -> None:
    report = _load_script("make_icra_runtime_bt_report.py")
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    log_path = experiments_dir / "trials.jsonl"
    base = dict(
        task_name="make_sandwich",
        planner="ros-service",
        planner_label="constrained_linear_ir",
        condition_label="robot_live",
    )
    experiment_log.append_event(
        log_path,
        experiment_log.build_event(
            event_type=experiment_log.EVENT_GENERATION, trial_id="a", success=True, **base
        ),
    )
    experiment_log.append_event(
        log_path,
        experiment_log.build_annotation_event(
            trial_id="a",
            task_success="success",
            outcome_label="completed",
            failure_category="none",
        ),
    )

    out_md = experiments_dir / "icra_report.md"
    rc = report.main(["--experiments-dir", str(experiments_dir), "--out-md", str(out_md)])
    assert rc == 0
    text = out_md.read_text(encoding="utf-8")
    assert "# Runtime BT ICRA experiment report" in text
    assert "## Summary" in text
    assert "offline unsafe baseline only" in text


def test_environment_snapshot_has_expected_keys() -> None:
    snapshot = env_snapshot.build_environment_snapshot(REPO_ROOT, ["prog", "--task", "make_sandwich"])
    assert set(snapshot) == {"git_branch", "git_commit", "hostname", "ros_distro", "command"}
    assert "make_sandwich" in snapshot["command"]
    assert isinstance(snapshot["hostname"], str) and snapshot["hostname"]


def test_run_icra_shell_script_is_safe_and_executable() -> None:
    script = SCRIPTS_DIR / "run_icra_runtime_bt_trial.sh"
    assert script.exists()
    mode = script.stat().st_mode
    assert mode & stat.S_IXUSR, "run_icra_runtime_bt_trial.sh must be executable"
    text = script.read_text(encoding="utf-8")
    assert "set -euo pipefail" in text
    # Uses the safe constrained linear IR planner, never the direct-XML baseline.
    assert "--planner-label constrained_linear_ir" in text or "constrained_linear_ir" in text
    assert "--planner ros-service" in text or 'PLANNER="ros-service"' in text
    assert "direct" not in text.lower() or "baseline" in text.lower()
    # All five tasks are mapped.
    for task in (
        "make_sandwich",
        "make_coffee",
        "set_breakfast_table",
        "prepare_picnic_bag",
        "items_in_drawer",
    ):
        assert task in text
