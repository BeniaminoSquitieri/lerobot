#!/usr/bin/env python3

"""Bundle a runtime BT experiment output directory into a single tar.gz archive.

Collects the generated artifacts and experiment logs for sharing or archiving a
trial set. By default it includes only text/JSON/XML/YAML artifacts and the
experiment logs; it never bundles videos or images. Uses only the standard
library so it runs anywhere the rest of the tooling runs.
"""

from __future__ import annotations

import argparse
import sys
import tarfile
from pathlib import Path

# Subdirectories of the output dir that are bundled when present.
_BUNDLED_SUBDIRS = (
    "plans",
    "raw_model_responses",
    "trees",
    "config",
    "manifests",
)

# Experiment log files that are bundled when present.
_BUNDLED_EXPERIMENT_FILES = (
    "trials.jsonl",
    "trials.csv",
    "trials_events.csv",
    "summary.csv",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bundle runtime BT experiment artifacts into a tar.gz archive.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("generated_bt"),
        help="Generated BT output directory to bundle.",
    )
    parser.add_argument(
        "--trial-id",
        type=str,
        default="",
        help="Optional trial id recorded in the bundle README.",
    )
    parser.add_argument(
        "--task",
        type=str,
        default="",
        help="Optional task name recorded in the bundle README.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output tar.gz path.",
    )
    args = parser.parse_args(argv)

    output_dir = args.output_dir
    if not output_dir.exists():
        print(f"Output dir does not exist: {output_dir}", file=sys.stderr)
        return 1

    members = _collect_members(output_dir)
    if not members:
        print(f"No bundleable artifacts found under: {output_dir}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    readme_text = _build_readme(task=args.task, trial_id=args.trial_id, members=members)
    with tarfile.open(args.out, "w:gz") as archive:
        for path, arcname in members:
            archive.add(path, arcname=arcname)
        _add_readme(archive, readme_text)

    print(f"wrote bundle: {args.out}")
    for _, arcname in members:
        print(f"  added: {arcname}")
    return 0


def _collect_members(output_dir: Path) -> list[tuple[Path, str]]:
    members: list[tuple[Path, str]] = []
    base = output_dir.name or "generated_bt"
    for subdir in _BUNDLED_SUBDIRS:
        path = output_dir / subdir
        if path.is_dir():
            members.append((path, f"{base}/{subdir}"))
    experiments_dir = output_dir / "experiments"
    for filename in _BUNDLED_EXPERIMENT_FILES:
        path = experiments_dir / filename
        if path.is_file():
            members.append((path, f"{base}/experiments/{filename}"))
    return members


def _build_readme(*, task: str, trial_id: str, members: list[tuple[Path, str]]) -> str:
    lines = [
        "Runtime BT experiment bundle",
        "============================",
        f"task: {task or '(unspecified)'}",
        f"trial_id: {trial_id or '(unspecified)'}",
        "",
        "Contents:",
    ]
    lines.extend(f"- {arcname}" for _, arcname in members)
    lines.append("")
    lines.append(
        "Note: direct XML is an offline unsafe baseline only and is not executable "
        "through the safe runtime path."
    )
    return "\n".join(lines) + "\n"


def _add_readme(archive: tarfile.TarFile, text: str) -> None:
    import io

    data = text.encode("utf-8")
    info = tarfile.TarInfo(name="README.txt")
    info.size = len(data)
    archive.addfile(info, io.BytesIO(data))


if __name__ == "__main__":
    raise SystemExit(main())
