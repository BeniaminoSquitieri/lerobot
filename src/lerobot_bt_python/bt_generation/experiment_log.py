"""Append-only experiment logging for runtime BT generation.

This module records measurable outcomes (generation and runner events) as
JSONL so a paper can report success/failure rates per task and condition.

Design constraints:
- It does not change the safe runtime path or any validation logic.
- It only observes outcomes; failures are first-class data points.
- JSONL is append-only; each line is a self-contained event object.
"""

from __future__ import annotations

import csv
import json
import time
import uuid
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any

# Schema version for every logged event. Bump only on a breaking change.
SCHEMA_VERSION = 1

# Event types.
EVENT_GENERATION = "generation"
EVENT_RUNNER = "runner"
EVENT_ANNOTATION = "annotation"

# Stable failure-stage constants. These name *where* the pipeline stopped.
STAGE_PARSE = "parse"
STAGE_VALIDATION = "validation"
STAGE_STATIC_CHECK = "static_check"
STAGE_ARTIFACT_WRITE = "artifact_write"
STAGE_RUNNER = "runner"
STAGE_SERVICE = "service"
STAGE_UNKNOWN = "unknown"

FAILURE_STAGES = (
    STAGE_PARSE,
    STAGE_VALIDATION,
    STAGE_STATIC_CHECK,
    STAGE_ARTIFACT_WRITE,
    STAGE_RUNNER,
    STAGE_SERVICE,
    STAGE_UNKNOWN,
)

# Operator-facing annotation vocabularies. These describe the observed outcome
# of a trial after a human watched it run; they never affect runtime behavior.
TASK_SUCCESS_VALUES = ("success", "failure", "unknown")

OUTCOME_LABELS = (
    "completed",
    "partial",
    "aborted",
    "operator_stop",
    "hardware_fail",
    "perception_fail",
    "planner_fail",
    "runner_fail",
    "unknown",
)

FAILURE_CATEGORIES = (
    "none",
    "planner_invalid",
    "validation_failed",
    "service_unavailable",
    "runner_failed",
    "skill_failed",
    "verifier_false_positive",
    "verifier_false_negative",
    "camera_missing",
    "model_error",
    "human_step_timeout",
    "safety_stop",
    "unknown",
)

# Default file name used when a caller only provides an output directory.
DEFAULT_LOG_DIRNAME = "experiments"
DEFAULT_LOG_FILENAME = "trials.jsonl"

# Ordered field list shared by event rows and the event-level CSV.
EVENT_FIELDS = (
    "schema_version",
    "event_type",
    "trial_id",
    "task_name",
    "planner",
    "planner_label",
    "condition_label",
    "success",
    "failure_stage",
    "failure_reason",
    "timestamp_unix_s",
    "duration_s",
    "output_dir",
    "linear_ir_path",
    "raw_response_path",
    "tree_xml_path",
    "bt_yaml_path",
    "manifest_path",
    # Runner-only extras (present on runner events).
    "runner_started",
    "runner_return_code",
    # Annotation-only extras (present on annotation events).
    "task_success",
    "outcome_label",
    "failure_category",
    "operator_notes",
    # Environment/command snapshot (optional on any event; older logs omit them).
    "git_commit",
    "git_branch",
    "hostname",
    "ros_distro",
    "command",
)

# Aggregated, trial-level summary columns (one row per task/planner/condition).
SUMMARY_FIELDS = (
    "task_name",
    "planner_label",
    "condition_label",
    "count_trials",
    "generation_success_rate",
    "runner_success_rate",
    "task_success_rate",
    "annotated_trial_count",
    "parse_failure_count",
    "validation_failure_count",
    "static_check_failure_count",
    "runner_failure_count",
    "top_failure_categories",
)

# Trial-level merged columns (one row per trial_id).
TRIAL_FIELDS = (
    "trial_id",
    "task_name",
    "planner",
    "planner_label",
    "condition_label",
    "generation_success",
    "generation_failure_stage",
    "runner_started",
    "runner_return_code",
    "runner_success",
    "task_success",
    "outcome_label",
    "failure_category",
    "operator_notes",
    "annotated",
    "git_commit",
    "git_branch",
    "hostname",
    "ros_distro",
    "command",
    "first_timestamp_unix_s",
    "last_timestamp_unix_s",
)


def new_trial_id(task_name: str, planner: str) -> str:
    """Return a unique, human-traceable trial id for one generation attempt."""

    stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
    suffix = uuid.uuid4().hex[:8]
    safe_task = (task_name or "task").strip() or "task"
    safe_planner = (planner or "planner").strip() or "planner"
    return f"{safe_task}__{safe_planner}__{stamp}__{suffix}"


def default_log_path(output_dir: Path) -> Path:
    """Return the default trials.jsonl path under an output directory."""

    return Path(output_dir) / DEFAULT_LOG_DIRNAME / DEFAULT_LOG_FILENAME


def resolve_log_path(
    experiment_log: Path | None,
    output_dir: Path | None,
) -> Path | None:
    """Resolve which JSONL path to log to, if any.

    Explicit --experiment-log wins. Otherwise, if --output-dir is present,
    default to <output_dir>/experiments/trials.jsonl. If neither is given,
    return None (no logging).
    """

    if experiment_log is not None:
        return Path(experiment_log)
    if output_dir is not None:
        return default_log_path(output_dir)
    return None


def build_event(
    *,
    event_type: str,
    trial_id: str,
    task_name: str,
    planner: str,
    planner_label: str,
    condition_label: str,
    success: bool,
    failure_stage: str | None = None,
    failure_reason: str | None = None,
    duration_s: float | None = None,
    timestamp_unix_s: float | None = None,
    output_dir: str | None = None,
    linear_ir_path: str | None = None,
    raw_response_path: str | None = None,
    tree_xml_path: str | None = None,
    bt_yaml_path: str | None = None,
    manifest_path: str | None = None,
    runner_started: bool | None = None,
    runner_return_code: int | None = None,
    git_commit: str | None = None,
    git_branch: str | None = None,
    hostname: str | None = None,
    ros_distro: str | None = None,
    command: str | None = None,
) -> "OrderedDict[str, Any]":
    """Build a fully-populated event dict with a stable field order."""

    event: "OrderedDict[str, Any]" = OrderedDict()
    event["schema_version"] = SCHEMA_VERSION
    event["event_type"] = event_type
    event["trial_id"] = trial_id
    event["task_name"] = task_name
    event["planner"] = planner
    event["planner_label"] = planner_label
    event["condition_label"] = condition_label
    event["success"] = bool(success)
    event["failure_stage"] = failure_stage
    event["failure_reason"] = failure_reason
    event["timestamp_unix_s"] = time.time() if timestamp_unix_s is None else timestamp_unix_s
    event["duration_s"] = duration_s
    event["output_dir"] = output_dir
    event["linear_ir_path"] = linear_ir_path
    event["raw_response_path"] = raw_response_path
    event["tree_xml_path"] = tree_xml_path
    event["bt_yaml_path"] = bt_yaml_path
    event["manifest_path"] = manifest_path
    if event_type == EVENT_RUNNER:
        event["runner_started"] = runner_started
        event["runner_return_code"] = runner_return_code
    # Environment/command snapshot is optional; only emit keys that are set so
    # older readers and CSVs stay backward compatible (absent => empty).
    if git_commit is not None:
        event["git_commit"] = git_commit
    if git_branch is not None:
        event["git_branch"] = git_branch
    if hostname is not None:
        event["hostname"] = hostname
    if ros_distro is not None:
        event["ros_distro"] = ros_distro
    if command is not None:
        event["command"] = command
    return event


def build_annotation_event(
    *,
    trial_id: str,
    task_success: str,
    outcome_label: str,
    failure_category: str,
    operator_notes: str = "",
    task_name: str = "",
    planner: str = "",
    planner_label: str = "",
    condition_label: str = "",
    timestamp_unix_s: float | None = None,
) -> "OrderedDict[str, Any]":
    """Build an operator annotation event recorded after observing a trial."""

    event: "OrderedDict[str, Any]" = OrderedDict()
    event["schema_version"] = SCHEMA_VERSION
    event["event_type"] = EVENT_ANNOTATION
    event["trial_id"] = trial_id
    event["task_name"] = task_name
    event["planner"] = planner
    event["planner_label"] = planner_label
    event["condition_label"] = condition_label
    # An annotation is not itself a pipeline success/failure; treat task_success
    # as the meaningful signal. Keep success aligned for convenient filtering.
    event["success"] = task_success == "success"
    event["failure_stage"] = None
    event["failure_reason"] = None
    event["timestamp_unix_s"] = time.time() if timestamp_unix_s is None else timestamp_unix_s
    event["duration_s"] = None
    event["task_success"] = task_success
    event["outcome_label"] = outcome_label
    event["failure_category"] = failure_category
    event["operator_notes"] = operator_notes
    return event


def append_event(path: Path, event: dict) -> None:
    """Append one event as a JSON line to an append-only JSONL file."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, sort_keys=False)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def read_events(jsonl_path: Path) -> list[dict]:
    """Read all events from a JSONL file, skipping blank lines."""

    path = Path(jsonl_path)
    events: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def write_events_csv(jsonl_path: Path, csv_path: Path) -> None:
    """Write a flat, event-level CSV (one row per logged event)."""

    events = read_events(jsonl_path)
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(EVENT_FIELDS))
        writer.writeheader()
        for event in events:
            writer.writerow({field: event.get(field, "") for field in EVENT_FIELDS})


def write_trial_csv(jsonl_path: Path, csv_path: Path) -> None:
    """Write a trial-level CSV merging generation/runner/annotation by trial_id."""

    events = read_events(jsonl_path)
    rows = merge_trials(events)
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(TRIAL_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in TRIAL_FIELDS})


def merge_trials(events: list[dict]) -> list[dict]:
    """Merge generation, runner, and annotation events into one row per trial.

    Events without a trial_id are ignored (they cannot be merged). Missing
    fields become empty strings so old logs remain readable.
    """

    trials: "OrderedDict[str, dict]" = OrderedDict()
    for event in events:
        trial_id = event.get("trial_id")
        if not trial_id:
            continue
        row = trials.setdefault(
            trial_id,
            {
                "trial_id": trial_id,
                "task_name": "",
                "planner": "",
                "planner_label": "",
                "condition_label": "",
                "generation_success": "",
                "generation_failure_stage": "",
                "runner_started": "",
                "runner_return_code": "",
                "runner_success": "",
                "task_success": "",
                "outcome_label": "",
                "failure_category": "",
                "operator_notes": "",
                "annotated": False,
                "git_commit": "",
                "git_branch": "",
                "hostname": "",
                "ros_distro": "",
                "command": "",
                "first_timestamp_unix_s": "",
                "last_timestamp_unix_s": "",
            },
        )

        for key in ("task_name", "planner", "planner_label", "condition_label"):
            value = event.get(key)
            if value not in (None, "") and not row[key]:
                row[key] = value
        for key in ("git_commit", "git_branch", "hostname", "ros_distro", "command"):
            value = event.get(key)
            if value not in (None, "") and not row[key]:
                row[key] = value

        timestamp = event.get("timestamp_unix_s")
        if timestamp is not None:
            if row["first_timestamp_unix_s"] == "" or timestamp < row["first_timestamp_unix_s"]:
                row["first_timestamp_unix_s"] = timestamp
            if row["last_timestamp_unix_s"] == "" or timestamp > row["last_timestamp_unix_s"]:
                row["last_timestamp_unix_s"] = timestamp

        event_type = event.get("event_type")
        if event_type == EVENT_GENERATION:
            row["generation_success"] = bool(event.get("success"))
            row["generation_failure_stage"] = event.get("failure_stage") or ""
        elif event_type == EVENT_RUNNER:
            row["runner_started"] = event.get("runner_started")
            row["runner_return_code"] = event.get("runner_return_code")
            row["runner_success"] = bool(event.get("success"))
        elif event_type == EVENT_ANNOTATION:
            row["annotated"] = True
            row["task_success"] = event.get("task_success") or ""
            row["outcome_label"] = event.get("outcome_label") or ""
            row["failure_category"] = event.get("failure_category") or ""
            row["operator_notes"] = event.get("operator_notes") or ""

    return list(trials.values())


def write_csv_summary(jsonl_path: Path, csv_path: Path) -> None:
    """Write an aggregated, trial-level CSV summary grouped by task/planner/condition."""

    events = read_events(jsonl_path)
    rows = summarize_events(events)
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SUMMARY_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize_events(events: list[dict]) -> list[dict]:
    """Aggregate trials per (task_name, planner_label, condition_label)."""

    trials = merge_trials(events)
    groups: "OrderedDict[tuple[str, str, str], dict]" = OrderedDict()
    for trial in trials:
        key = (
            str(trial.get("task_name", "")),
            str(trial.get("planner_label", "")),
            str(trial.get("condition_label", "")),
        )
        bucket = groups.setdefault(
            key,
            {
                "count_trials": 0,
                "generation_total": 0,
                "generation_success": 0,
                "runner_total": 0,
                "runner_success": 0,
                "task_total": 0,
                "task_success": 0,
                "annotated_trial_count": 0,
                "parse_failure_count": 0,
                "validation_failure_count": 0,
                "static_check_failure_count": 0,
                "runner_failure_count": 0,
                "failure_categories": Counter(),
            },
        )
        bucket["count_trials"] += 1

        gen_success = trial.get("generation_success")
        if isinstance(gen_success, bool):
            bucket["generation_total"] += 1
            if gen_success:
                bucket["generation_success"] += 1

        runner_success = trial.get("runner_success")
        if isinstance(runner_success, bool):
            bucket["runner_total"] += 1
            if runner_success:
                bucket["runner_success"] += 1

        if trial.get("annotated"):
            bucket["annotated_trial_count"] += 1
            task_success = trial.get("task_success")
            if task_success in ("success", "failure"):
                bucket["task_total"] += 1
                if task_success == "success":
                    bucket["task_success"] += 1

        stage = trial.get("generation_failure_stage")
        if stage == STAGE_PARSE:
            bucket["parse_failure_count"] += 1
        elif stage == STAGE_VALIDATION:
            bucket["validation_failure_count"] += 1
        elif stage == STAGE_STATIC_CHECK:
            bucket["static_check_failure_count"] += 1
        if trial.get("runner_success") is False:
            bucket["runner_failure_count"] += 1

        category = trial.get("failure_category")
        if category and category != "none":
            bucket["failure_categories"][category] += 1

    rows: list[dict] = []
    for (task_name, planner_label, condition_label), bucket in groups.items():
        rows.append(
            {
                "task_name": task_name,
                "planner_label": planner_label,
                "condition_label": condition_label,
                "count_trials": bucket["count_trials"],
                "generation_success_rate": _rate(
                    bucket["generation_success"], bucket["generation_total"]
                ),
                "runner_success_rate": _rate(
                    bucket["runner_success"], bucket["runner_total"]
                ),
                "task_success_rate": _rate(bucket["task_success"], bucket["task_total"]),
                "annotated_trial_count": bucket["annotated_trial_count"],
                "parse_failure_count": bucket["parse_failure_count"],
                "validation_failure_count": bucket["validation_failure_count"],
                "static_check_failure_count": bucket["static_check_failure_count"],
                "runner_failure_count": bucket["runner_failure_count"],
                "top_failure_categories": _format_top_categories(bucket["failure_categories"]),
            }
        )
    return rows


def _format_top_categories(counter: "Counter[str]") -> str:
    if not counter:
        return ""
    return ";".join(
        f"{name}:{count}" for name, count in counter.most_common()
    )


def _rate(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return ""
    return f"{numerator / denominator:.4f}"
