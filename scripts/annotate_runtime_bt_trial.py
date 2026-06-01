#!/usr/bin/env python3

"""Append an operator annotation for a runtime BT trial.

This records what a human observed after watching a trial run (did the task
actually succeed, what kind of outcome, what failed). It is append-only: it
never edits or deletes earlier log lines, so the raw generation/runner events
stay intact. Annotations are provenance, not control: they do not change any
runtime behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as a standalone script via PYTHONPATH=src or directly.
_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lerobot_bt_python.bt_generation import experiment_log  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Append an operator annotation event for a runtime BT trial.",
    )
    parser.add_argument(
        "--jsonl",
        type=Path,
        default=Path("generated_bt/experiments/trials.jsonl"),
        help="Append-only JSONL log to annotate.",
    )
    parser.add_argument(
        "--trial-id",
        type=str,
        required=True,
        help="Trial id printed by generate_and_run (must be non-empty).",
    )
    parser.add_argument(
        "--task-success",
        choices=experiment_log.TASK_SUCCESS_VALUES,
        required=True,
        help="Did the task actually succeed, as judged by the operator.",
    )
    parser.add_argument(
        "--outcome-label",
        choices=experiment_log.OUTCOME_LABELS,
        required=True,
        help="Observed outcome category.",
    )
    parser.add_argument(
        "--failure-category",
        choices=experiment_log.FAILURE_CATEGORIES,
        required=True,
        help="Failure category ('none' when the task succeeded).",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Free-form operator notes.",
    )
    parser.add_argument(
        "--task-name",
        type=str,
        default="",
        help="Optional task name to copy onto the annotation event.",
    )
    parser.add_argument(
        "--planner-label",
        type=str,
        default="",
        help="Optional planner label to copy onto the annotation event.",
    )
    parser.add_argument(
        "--condition-label",
        type=str,
        default="",
        help="Optional condition label to copy onto the annotation event.",
    )
    args = parser.parse_args(argv)

    trial_id = args.trial_id.strip()
    if not trial_id:
        print("--trial-id must be a non-empty value.", file=sys.stderr)
        return 2

    # If the trial already exists in the log, inherit its labels so the
    # annotation groups with the rest of the trial without re-typing them.
    task_name = args.task_name
    planner = ""
    planner_label = args.planner_label
    condition_label = args.condition_label
    if args.jsonl.exists():
        for event in experiment_log.read_events(args.jsonl):
            if event.get("trial_id") != trial_id:
                continue
            task_name = task_name or str(event.get("task_name") or "")
            planner = planner or str(event.get("planner") or "")
            planner_label = planner_label or str(event.get("planner_label") or "")
            condition_label = condition_label or str(event.get("condition_label") or "")

    event = experiment_log.build_annotation_event(
        trial_id=trial_id,
        task_success=args.task_success,
        outcome_label=args.outcome_label,
        failure_category=args.failure_category,
        operator_notes=args.notes,
        task_name=task_name,
        planner=planner,
        planner_label=planner_label,
        condition_label=condition_label,
    )
    experiment_log.append_event(args.jsonl, event)
    print(f"appended annotation for trial_id: {trial_id}")
    print(json.dumps(event))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
