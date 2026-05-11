from __future__ import annotations

import pytest

from sandwich_bt_python.verification import (
    VLM_FAILURE,
    VLM_NEEDS_MANUAL_HELP,
    VLM_PENDING,
    VLM_RUNNING,
    VLM_SUCCESS,
    VlmCheckRegistry,
)


def test_vlm_check_registry_rejects_stale_attempt_reports() -> None:
    registry = VlmCheckRegistry(known_skill_names={"place_first_toast"})

    first_attempt = registry.begin_attempt("place_first_toast")
    second_attempt = registry.begin_attempt("place_first_toast")

    stale_update = registry.report(
        skill_name="place_first_toast",
        attempt_id=first_attempt.attempt_id,
        status=VLM_FAILURE,
        message="old result",
    )

    assert first_attempt.attempt_id == 1
    assert second_attempt.attempt_id == 2
    assert not stale_update.accepted
    assert stale_update.snapshot is not None
    assert stale_update.snapshot.attempt_id == 2


def test_vlm_check_registry_requires_known_status() -> None:
    registry = VlmCheckRegistry(known_skill_names={"place_first_toast"})
    registry.begin_attempt("place_first_toast")

    with pytest.raises(ValueError, match="Unsupported VLM status"):
        registry.report(
            skill_name="place_first_toast",
            status="BOGUS",
        )


def test_vlm_check_registry_accepts_waiting_updates_before_final_status() -> None:
    registry = VlmCheckRegistry(known_skill_names={"pour_ingredient"})
    attempt = registry.begin_attempt("pour_ingredient")

    running = registry.report(
        skill_name="pour_ingredient",
        attempt_id=attempt.attempt_id,
        status=VLM_RUNNING,
        message="human is pouring",
    )
    manual = registry.report(
        skill_name="pour_ingredient",
        attempt_id=attempt.attempt_id,
        status=VLM_NEEDS_MANUAL_HELP,
        message="human hand still in scene",
    )
    success = registry.report(
        skill_name="pour_ingredient",
        attempt_id=attempt.attempt_id,
        status=VLM_SUCCESS,
        message="pouring completed",
    )
    stale = registry.report(
        skill_name="pour_ingredient",
        attempt_id=attempt.attempt_id,
        status=VLM_FAILURE,
        message="late failure",
    )

    assert running.accepted
    assert manual.accepted
    assert success.accepted
    assert not stale.accepted
    latest = registry.get_latest("pour_ingredient")
    assert latest is not None
    assert latest.status == VLM_SUCCESS
    assert latest.message == "pouring completed"


def test_vlm_check_registry_times_out_waiting_attempt_as_failure() -> None:
    now_s = 100.0

    def clock() -> float:
        return now_s

    registry = VlmCheckRegistry(
        known_skill_names={"place_first_toast"},
        vlm_timeout_s=2.0,
        clock=clock,
    )
    attempt = registry.begin_attempt("place_first_toast")

    now_s = 101.9
    pending = registry.get_latest("place_first_toast")
    assert pending is not None
    assert pending.status == VLM_PENDING

    now_s = 102.0
    timed_out = registry.get_latest("place_first_toast")
    assert timed_out is not None
    assert timed_out.attempt_id == attempt.attempt_id
    assert timed_out.status == VLM_FAILURE
    assert "timed out after 2.00s without SUCCESS" in timed_out.message

    late_success = registry.report(
        skill_name="place_first_toast",
        attempt_id=attempt.attempt_id,
        status=VLM_SUCCESS,
        message="late VLM success",
    )
    assert not late_success.accepted
    assert late_success.snapshot is not None
    assert late_success.snapshot.status == VLM_FAILURE
