#!/usr/bin/env python3

"""Summarize runtime BT generation experiment events into CSV files.

Reads an append-only JSONL log produced by bt_generation experiment logging and
writes:
- an event-level CSV (one row per logged event); and
- an aggregated summary CSV grouped by task_name, planner_label, and
  condition_label.

Failures are useful data. They are counted per stage, not discarded.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as a standalone script via PYTHONPATH=src or directly.
_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lerobot_bt_python.bt_generation import experiment_log  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize runtime BT generation experiment events.",
    )
    parser.add_argument(
        "--jsonl",
        type=Path,
        default=Path("generated_bt/experiments/trials.jsonl"),
        help="Input append-only JSONL log.",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=Path("generated_bt/experiments/trials.csv"),
        help="Output event-level CSV path.",
    )
    parser.add_argument(
        "--summary-csv",
        type=Path,
        default=Path("generated_bt/experiments/summary.csv"),
        help="Output aggregated summary CSV path.",
    )
    args = parser.parse_args(argv)

    if not args.jsonl.exists():
        print(f"JSONL log does not exist: {args.jsonl}", file=sys.stderr)
        return 1

    experiment_log.write_events_csv(args.jsonl, args.out_csv)
    experiment_log.write_csv_summary(args.jsonl, args.summary_csv)
    print(f"wrote event CSV: {args.out_csv}")
    print(f"wrote summary CSV: {args.summary_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
