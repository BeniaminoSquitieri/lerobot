#!/usr/bin/env python

"""Tests for append-only experiment logging in runtime BT generation."""

from __future__ import annotations

import json
from pathlib import Path

from lerobot_bt_python.bt_generation import experiment_log, generate


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/skills_registry.yaml"
SANDWICH_EXECUTOR = REPO_ROOT / "src/lerobot_bt_python/make_sandwich_executor.yaml"
ASSET_DIR = REPO_ROOT / "tests/assets/vlm_planner"


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_append_event_appends_jsonl_lines(tmp_path: Path) -> None:
    log_path = tmp_path / "trials.jsonl"
    event_one = experiment_log.build_event(
        event_type=experiment_log.EVENT_GENERATION,
        trial_id="t1",
        task_name="make_sandwich",
        planner="template",
        planner_label="template",
        condition_label="default",
        success=True,
    )
    event_two = experiment_log.build_event(
        event_type=experiment_log.EVENT_RUNNER,
        trial_id="t1",
        task_name="make_sandwich",
        planner="template",
        planner_label="template",
        condition_label="default",
        success=False,
        failure_stage=experiment_log.STAGE_RUNNER,
        runner_started=True,
        runner_return_code=1,
    )

    experiment_log.append_event(log_path, event_one)
    experiment_log.append_event(log_path, event_two)

    events = _read_jsonl(log_path)
    assert len(events) == 2
    assert events[0]["schema_version"] == 1
    assert events[0]["event_type"] == "generation"
    assert events[1]["event_type"] == "runner"
    assert events[1]["runner_return_code"] == 1


def test_write_csv_summary_aggregates_rates(tmp_path: Path) -> None:
    log_path = tmp_path / "trials.jsonl"
    base = dict(
        task_name="make_sandwich",
        planner="model-response",
        planner_label="constrained",
        condition_label="default",
    )
    experiment_log.append_event(
        log_path,
        experiment_log.build_event(
            event_type=experiment_log.EVENT_GENERATION, trial_id="a", success=True, **base
        ),
    )
    experiment_log.append_event(
        log_path,
        experiment_log.build_event(
            event_type=experiment_log.EVENT_GENERATION,
            trial_id="b",
            success=False,
            failure_stage=experiment_log.STAGE_PARSE,
            **base,
        ),
    )
    experiment_log.append_event(
        log_path,
        experiment_log.build_event(
            event_type=experiment_log.EVENT_RUNNER,
            trial_id="a",
            success=True,
            runner_started=True,
            runner_return_code=0,
            **base,
        ),
    )

    summary_csv = tmp_path / "summary.csv"
    experiment_log.write_csv_summary(log_path, summary_csv)

    rows = summary_csv.read_text(encoding="utf-8").splitlines()
    header = rows[0].split(",")
    assert header == list(experiment_log.SUMMARY_FIELDS)
    data = dict(zip(header, rows[1].split(",")))
    assert data["task_name"] == "make_sandwich"
    assert data["planner_label"] == "constrained"
    assert data["count"] == "3"
    assert data["generation_success_rate"] == "0.5000"
    assert data["runner_success_rate"] == "1.0000"
    assert data["parse_failure_count"] == "1"


def test_failure_stage_aggregation_counts_each_stage(tmp_path: Path) -> None:
    events = []
    for stage in (
        experiment_log.STAGE_PARSE,
        experiment_log.STAGE_VALIDATION,
        experiment_log.STAGE_STATIC_CHECK,
        experiment_log.STAGE_RUNNER,
    ):
        events.append(
            experiment_log.build_event(
                event_type=experiment_log.EVENT_GENERATION,
                trial_id=stage,
                task_name="make_sandwich",
                planner="model-response",
                planner_label="constrained",
                condition_label="default",
                success=False,
                failure_stage=stage,
            )
        )
    rows = experiment_log.summarize_events(events)
    assert len(rows) == 1
    row = rows[0]
    assert row["parse_failure_count"] == 1
    assert row["validation_failure_count"] == 1
    assert row["static_check_failure_count"] == 1
    assert row["runner_failure_count"] == 1


def test_default_experiment_path_uses_output_dir(tmp_path: Path) -> None:
    output_dir = tmp_path / "generated_bt"
    rc = generate.main(
        [
            "--task",
            "make_sandwich",
            "--planner",
            "template",
            "--registry",
            str(REGISTRY_PATH),
            "--executor-yaml",
            str(SANDWICH_EXECUTOR),
            "--output-dir",
            str(output_dir),
        ]
    )
    assert rc == 0
    log_path = output_dir / "experiments" / "trials.jsonl"
    assert log_path.exists()
    events = _read_jsonl(log_path)
    assert len(events) == 1
    assert events[0]["event_type"] == "generation"
    assert events[0]["success"] is True
    assert events[0]["failure_stage"] is None
    assert events[0]["tree_xml_path"] == str(output_dir / "trees/make_sandwich.xml")


def test_generate_logs_on_invalid_model_response(tmp_path: Path) -> None:
    output_dir = tmp_path / "generated_bt"
    log_path = tmp_path / "custom_trials.jsonl"
    rc = generate.main(
        [
            "--task",
            "make_sandwich",
            "--planner",
            "model-response",
            "--model-response-file",
            str(ASSET_DIR / "make_sandwich_bad_xml_response.txt"),
            "--registry",
            str(REGISTRY_PATH),
            "--executor-yaml",
            str(SANDWICH_EXECUTOR),
            "--output-dir",
            str(output_dir),
            "--experiment-log",
            str(log_path),
            "--planner-label",
            "constrained",
            "--condition-label",
            "abl1",
        ]
    )
    assert rc == 1
    events = _read_jsonl(log_path)
    assert len(events) == 1
    event = events[0]
    assert event["success"] is False
    assert event["failure_stage"] == experiment_log.STAGE_PARSE
    assert event["planner_label"] == "constrained"
    assert event["condition_label"] == "abl1"
    assert event["failure_reason"]


def test_generate_logs_validation_failure(tmp_path: Path) -> None:
    output_dir = tmp_path / "generated_bt"
    rc = generate.main(
        [
            "--task",
            "make_sandwich",
            "--planner",
            "model-response",
            "--model-response-file",
            str(ASSET_DIR / "make_sandwich_bad_invented_skill.json"),
            "--registry",
            str(REGISTRY_PATH),
            "--executor-yaml",
            str(SANDWICH_EXECUTOR),
            "--output-dir",
            str(output_dir),
        ]
    )
    assert rc == 1
    log_path = output_dir / "experiments" / "trials.jsonl"
    events = _read_jsonl(log_path)
    assert len(events) == 1
    assert events[0]["success"] is False
    assert events[0]["failure_stage"] in {
        experiment_log.STAGE_VALIDATION,
        experiment_log.STAGE_PARSE,
    }
