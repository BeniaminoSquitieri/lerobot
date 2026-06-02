#!/usr/bin/env python

"""Tests for repository-owned task contract loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from lerobot_bt_python.bt_generation.task_contracts import load_task_contracts


REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_CONTRACTS_PATH = REPO_ROOT / "src/lerobot_bt_python/bt_generation/task_templates.yaml"


def test_default_task_contracts_load_repo_owned_templates() -> None:
    task_templates, allowed_variants = load_task_contracts(TASK_CONTRACTS_PATH)

    assert task_templates["make_sandwich"][0] == {
        "kind": "vlm_gate",
        "name": "initial_scene_ready",
    }
    assert task_templates["make_sandwich"][-1] == {
        "kind": "vlm_gate",
        "name": "make_sandwich.task_complete",
    }
    assert allowed_variants == {}


def test_task_contracts_reject_unsupported_step_fields(tmp_path: Path) -> None:
    bad_contract = tmp_path / "bad_task_templates.yaml"
    bad_contract.write_text(
        """
task_templates:
  make_sandwich:
    - kind: vlm_gate
      name: initial_scene_ready
      comment: should_fail
allowed_variants: {}
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="contains unsupported fields"):
        load_task_contracts(bad_contract)