"""Generation manifest helpers for runtime BT artifacts."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest for a file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    """Return the SHA-256 hex digest for UTF-8 text."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_generation_manifest(
    *,
    task_name: str,
    planner: str,
    registry_path: Path,
    executor_yaml_path: Path | None,
    tree_xml_path: Path,
    bt_yaml_path: Path,
    canonical_task_sequence: list[dict[str, str]],
    linear_ir_path: Path | None = None,
    raw_response_path: Path | None = None,
    generated_at_unix_s: int | None = None,
) -> dict[str, Any]:
    """Build a manifest for generated BT artifacts and their source contract."""

    canonical_task_sequence_text = json.dumps(canonical_task_sequence, sort_keys=True)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "task_name": task_name,
        "planner": planner,
        "registry_path": str(registry_path),
        "executor_yaml_path": str(executor_yaml_path) if executor_yaml_path is not None else None,
        "tree_xml_path": str(tree_xml_path),
        "bt_yaml_path": str(bt_yaml_path),
        "registry_sha256": sha256_file(registry_path),
        "tree_xml_sha256": sha256_file(tree_xml_path),
        "bt_yaml_sha256": sha256_file(bt_yaml_path),
        "canonical_task_sequence_sha256": sha256_text(canonical_task_sequence_text),
        "generated_at_unix_s": int(time.time() if generated_at_unix_s is None else generated_at_unix_s),
    }

    if executor_yaml_path is not None and executor_yaml_path.exists():
        manifest["executor_yaml_sha256"] = sha256_file(executor_yaml_path)
    if linear_ir_path is not None and linear_ir_path.exists():
        manifest["linear_ir_path"] = str(linear_ir_path)
        manifest["linear_ir_sha256"] = sha256_file(linear_ir_path)
    if raw_response_path is not None and raw_response_path.exists():
        manifest["raw_response_path"] = str(raw_response_path)

    return manifest


def write_generation_manifest(path: Path, manifest: dict) -> None:
    """Write a generation manifest as stable JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
