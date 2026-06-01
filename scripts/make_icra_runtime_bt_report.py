#!/usr/bin/env python3

"""Render a Markdown report from runtime BT experiment logs for the ICRA paper.

Reads the append-only JSONL log (and optional CSV summaries and verifier events)
and emits a single dependency-free Markdown report: overview, conditions tested,
aggregate summary table, failure-category counts, and a trial-level table. No
plotting and no third-party dependencies.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

# Allow running as a standalone script via PYTHONPATH=src or directly.
_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lerobot_bt_python.bt_generation import experiment_log  # noqa: E402

_BASELINE_NOTE = (
    "Direct XML is an offline unsafe baseline only and is not executable through "
    "the safe runtime path."
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render a Markdown ICRA report from runtime BT experiment logs.",
    )
    parser.add_argument(
        "--experiments-dir",
        type=Path,
        default=Path("generated_bt/experiments"),
        help="Directory containing trials.jsonl and optional CSV/JSONL files.",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=Path("generated_bt/experiments/icra_report.md"),
        help="Output Markdown report path.",
    )
    args = parser.parse_args(argv)

    jsonl_path = args.experiments_dir / "trials.jsonl"
    if not jsonl_path.exists():
        print(f"trials.jsonl does not exist: {jsonl_path}", file=sys.stderr)
        return 1

    events = experiment_log.read_events(jsonl_path)
    trials = experiment_log.merge_trials(events)
    summary = experiment_log.summarize_events(events)

    sections: list[str] = []
    sections.append(_overview_section(trials))
    sections.append(_conditions_section(trials))
    sections.append(_summary_section(summary))
    sections.append(_failure_section(trials))
    sections.append(_trials_section(trials))

    ablation = _read_optional_csv(args.experiments_dir / "ablation_results.csv")
    if ablation:
        sections.append(_ablation_section(ablation))

    verifier_path = args.experiments_dir / "verifier_events.jsonl"
    if verifier_path.exists():
        sections.append(_verifier_section(verifier_path))

    sections.append(f"## Notes\n\n- {_BASELINE_NOTE}\n")

    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text("\n".join(sections), encoding="utf-8")
    print(f"wrote report: {args.out_md}")
    return 0


def _overview_section(trials: list[dict]) -> str:
    annotated = sum(1 for t in trials if t.get("annotated"))
    return (
        "# Runtime BT ICRA experiment report\n\n"
        "## Overview\n\n"
        f"- Total trials: {len(trials)}\n"
        f"- Annotated trials: {annotated}\n"
    )


def _conditions_section(trials: list[dict]) -> str:
    conditions = Counter(
        (str(t.get("task_name", "")), str(t.get("planner_label", "")), str(t.get("condition_label", "")))
        for t in trials
    )
    lines = ["## Conditions tested\n", "| task | planner_label | condition_label | trials |", "| --- | --- | --- | --- |"]
    for (task, planner_label, condition_label), count in conditions.items():
        lines.append(f"| {task} | {planner_label} | {condition_label} | {count} |")
    return "\n".join(lines) + "\n"


def _summary_section(summary: list[dict]) -> str:
    fields = list(experiment_log.SUMMARY_FIELDS)
    lines = ["## Summary\n", "| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in summary:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(lines) + "\n"


def _failure_section(trials: list[dict]) -> str:
    categories: "Counter[str]" = Counter()
    for trial in trials:
        category = trial.get("failure_category")
        if category and category != "none":
            categories[category] += 1
    lines = ["## Failure categories\n", "| failure_category | count |", "| --- | --- |"]
    if not categories:
        lines.append("| (none recorded) | 0 |")
    for category, count in categories.most_common():
        lines.append(f"| {category} | {count} |")
    return "\n".join(lines) + "\n"


def _trials_section(trials: list[dict]) -> str:
    fields = [
        "trial_id",
        "task_name",
        "planner_label",
        "condition_label",
        "generation_success",
        "runner_success",
        "task_success",
        "outcome_label",
        "failure_category",
    ]
    lines = ["## Trials\n", "| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for trial in trials:
        lines.append("| " + " | ".join(str(trial.get(field, "")) for field in fields) + " |")
    return "\n".join(lines) + "\n"


def _ablation_section(rows: list[dict]) -> str:
    if not rows:
        return ""
    fields = list(rows[0].keys())
    lines = ["## Offline ablation\n", "| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(lines) + "\n"


def _verifier_section(verifier_path: Path) -> str:
    import json

    raw = Counter()
    published = Counter()
    coerced = 0
    total = 0
    for line in verifier_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        raw[str(event.get("raw_status", ""))] += 1
        published[str(event.get("published_status", ""))] += 1
        if event.get("was_wait_human_coerced"):
            coerced += 1
    lines = [
        "## VLM verifier events\n",
        f"- Total verifier events: {total}",
        f"- WAIT_HUMAN -> RUNNING coercions: {coerced}",
        "",
        "| status | raw count | published count |",
        "| --- | --- | --- |",
    ]
    statuses = sorted(set(raw) | set(published))
    for status in statuses:
        lines.append(f"| {status} | {raw.get(status, 0)} | {published.get(status, 0)} |")
    return "\n".join(lines) + "\n"


def _read_optional_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    raise SystemExit(main())
