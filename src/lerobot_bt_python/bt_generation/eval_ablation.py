"""Offline ablation evaluator for raw Linear IR / model responses.

This tool measures how often raw model responses would pass validation under
different *offline* check configurations. It never executes the robot and never
modifies the runtime validator (`validate_linear_plan` stays strict).

Instead of weakening the validator, it runs the full strict validator once per
response and classifies the resulting error messages. Each ablation condition is
then a pure post-hoc filter over those classified errors:

- full_validator: pass only if there are no validation errors at all.
- no_canonical_sequence_check: pass if the only errors are canonical-sequence
  (ordering) errors.
- no_extra_field_check: pass if the only errors are strict extra-field errors.
- parse_only: pass if the response parses as Linear IR JSON (no validation).
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

from .registry import load_registry
from .validator import validate_linear_plan
from .vlm_planner import parse_planner_response

CONDITIONS = (
    "full_validator",
    "no_canonical_sequence_check",
    "no_extra_field_check",
    "parse_only",
)

OUTPUT_FIELDS = (
    "response_file",
    "task_name",
    "condition",
    "parse_success",
    "validation_success",
    "failure_reason",
    "hallucinated_name_count",
    "ordering_error",
    "extra_field_error",
)

# Substrings used to classify strict validator error messages offline.
_ORDERING_MARKERS = (
    "canonical task sequence",
)
_EXTRA_FIELD_MARKERS = (
    "unsupported strict fields",
)
_HALLUCINATED_MARKERS = (
    "is not present in the registry",
    "is ambiguous in the registry",
    "is not registered",
)


def _classify_errors(errors: list[str]) -> dict[str, Any]:
    ordering = [err for err in errors if _matches(err, _ORDERING_MARKERS)]
    extra_field = [err for err in errors if _matches(err, _EXTRA_FIELD_MARKERS)]
    hallucinated = [err for err in errors if _matches(err, _HALLUCINATED_MARKERS)]
    return {
        "ordering": ordering,
        "extra_field": extra_field,
        "hallucinated": hallucinated,
    }


def _matches(message: str, markers: tuple[str, ...]) -> bool:
    return any(marker in message for marker in markers)


def evaluate_response(
    response_file: Path,
    task_name: str,
    registry,
    executor_yaml: Path | None,
) -> list[dict[str, Any]]:
    """Return one result row per ablation condition for a single response."""

    text = response_file.read_text(encoding="utf-8")
    parse_success = True
    parse_error: str | None = None
    plan: dict[str, Any] | None = None
    try:
        plan = parse_planner_response(text)
    except Exception as exc:  # noqa: BLE001
        parse_success = False
        parse_error = str(exc)

    resolved_task = task_name
    if isinstance(plan, dict) and isinstance(plan.get("task_name"), str):
        resolved_task = plan["task_name"]

    errors: list[str] = []
    if parse_success and plan is not None:
        errors = validate_linear_plan(
            plan,
            registry,
            executor_yaml,
            strict_generated=True,
        )
    classified = _classify_errors(errors)

    rows: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        validation_success, failure_reason = _condition_outcome(
            condition,
            parse_success,
            parse_error,
            errors,
            classified,
        )
        rows.append(
            OrderedDict(
                (
                    ("response_file", str(response_file)),
                    ("task_name", resolved_task),
                    ("condition", condition),
                    ("parse_success", parse_success),
                    ("validation_success", validation_success),
                    ("failure_reason", failure_reason),
                    ("hallucinated_name_count", len(classified["hallucinated"])),
                    ("ordering_error", bool(classified["ordering"])),
                    ("extra_field_error", bool(classified["extra_field"])),
                )
            )
        )
    return rows


def _condition_outcome(
    condition: str,
    parse_success: bool,
    parse_error: str | None,
    errors: list[str],
    classified: dict[str, Any],
) -> tuple[bool, str | None]:
    if not parse_success:
        return False, parse_error

    if condition == "parse_only":
        return True, None

    if condition == "full_validator":
        residual = errors
    elif condition == "no_canonical_sequence_check":
        residual = [err for err in errors if err not in classified["ordering"]]
    elif condition == "no_extra_field_check":
        residual = [err for err in errors if err not in classified["extra_field"]]
    else:  # pragma: no cover - guarded by CONDITIONS
        raise ValueError(f"Unknown ablation condition: {condition}")

    if residual:
        return False, "; ".join(residual)
    return True, None


def _iter_response_files(responses_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in responses_dir.iterdir()
        if path.is_file() and path.suffix in {".json", ".txt"}
    )


def run(
    task_name: str,
    registry_path: Path,
    executor_yaml: Path | None,
    responses_dir: Path,
    out_jsonl: Path,
    out_csv: Path,
) -> list[dict[str, Any]]:
    registry = load_registry(registry_path)
    rows: list[dict[str, Any]] = []
    for response_file in _iter_response_files(responses_dir):
        rows.extend(evaluate_response(response_file, task_name, registry, executor_yaml))

    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=False) + "\n")

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in OUTPUT_FIELDS})
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline ablation over raw Linear IR / model responses.",
    )
    parser.add_argument("--task", required=True, help="Intended task name for validation context.")
    parser.add_argument("--registry", required=True, type=Path, help="skills_registry.yaml path.")
    parser.add_argument(
        "--executor-yaml",
        type=Path,
        help="Executor YAML used for consistency checks.",
    )
    parser.add_argument(
        "--responses-dir",
        required=True,
        type=Path,
        help="Directory of raw model responses (.json/.txt).",
    )
    parser.add_argument(
        "--out-jsonl",
        required=True,
        type=Path,
        help="Output JSONL of per-response, per-condition results.",
    )
    parser.add_argument(
        "--out-csv",
        required=True,
        type=Path,
        help="Output CSV of per-response, per-condition results.",
    )
    args = parser.parse_args(argv)

    if not args.responses_dir.exists():
        parser.error(f"responses-dir does not exist: {args.responses_dir}")

    rows = run(
        args.task,
        args.registry,
        args.executor_yaml,
        args.responses_dir,
        args.out_jsonl,
        args.out_csv,
    )
    print(f"evaluated {len(rows)} response/condition rows")
    print(f"wrote JSONL: {args.out_jsonl}")
    print(f"wrote CSV: {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
