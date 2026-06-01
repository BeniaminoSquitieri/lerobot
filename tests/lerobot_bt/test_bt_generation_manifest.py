#!/usr/bin/env python

"""Tests for generated BT artifact manifests."""

from __future__ import annotations

import json
from pathlib import Path

from lerobot_bt_python.bt_generation.manifest import (
    build_generation_manifest,
    sha256_file,
    sha256_text,
    write_generation_manifest,
)


def test_generation_manifest_hashes_artifacts(tmp_path: Path) -> None:
    registry = tmp_path / "skills_registry.yaml"
    executor = tmp_path / "executor.yaml"
    tree = tmp_path / "tree.xml"
    bt_yaml = tmp_path / "bt.yaml"
    linear_ir = tmp_path / "linear_ir.json"
    raw_response = tmp_path / "raw_response.json"
    manifest_path = tmp_path / "manifests" / "task_manifest.json"

    registry.write_text("version: 1\n", encoding="utf-8")
    executor.write_text("skills: []\n", encoding="utf-8")
    tree.write_text("<root />\n", encoding="utf-8")
    bt_yaml.write_text("lerobot_bt_runner: {}\n", encoding="utf-8")
    linear_ir.write_text('{"task_name": "demo", "steps": []}\n', encoding="utf-8")
    raw_response.write_text('{"task_name": "demo", "steps": []}\n', encoding="utf-8")

    canonical_task_sequence = [{"kind": "vlm_gate", "name": "demo.ready"}]
    manifest = build_generation_manifest(
        task_name="demo",
        planner="model-response",
        registry_path=registry,
        executor_yaml_path=executor,
        tree_xml_path=tree,
        bt_yaml_path=bt_yaml,
        canonical_task_sequence=canonical_task_sequence,
        linear_ir_path=linear_ir,
        raw_response_path=raw_response,
        generated_at_unix_s=123,
    )

    assert manifest["schema_version"] == 1
    assert manifest["task_name"] == "demo"
    assert manifest["planner"] == "model-response"
    assert manifest["registry_path"] == str(registry)
    assert manifest["executor_yaml_path"] == str(executor)
    assert manifest["tree_xml_path"] == str(tree)
    assert manifest["bt_yaml_path"] == str(bt_yaml)
    assert manifest["linear_ir_path"] == str(linear_ir)
    assert manifest["raw_response_path"] == str(raw_response)
    assert manifest["registry_sha256"] == sha256_file(registry)
    assert manifest["executor_yaml_sha256"] == sha256_file(executor)
    assert manifest["linear_ir_sha256"] == sha256_file(linear_ir)
    assert manifest["tree_xml_sha256"] == sha256_file(tree)
    assert manifest["bt_yaml_sha256"] == sha256_file(bt_yaml)
    assert manifest["canonical_task_sequence_sha256"] == sha256_text(
        json.dumps(canonical_task_sequence, sort_keys=True)
    )
    assert manifest["generated_at_unix_s"] == 123

    write_generation_manifest(manifest_path, manifest)

    assert json.loads(manifest_path.read_text(encoding="utf-8")) == manifest
