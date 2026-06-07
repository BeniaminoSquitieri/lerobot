#!/usr/bin/env python

from __future__ import annotations

from lerobot_bt_python.executor import _ActiveSkillTracker
from lerobot_bt_python.vlm.verification import VLM_FAILURE, VLM_SUCCESS


def test_active_skill_tracker_accepts_matching_attempt_id() -> None:
    tracker = _ActiveSkillTracker()
    tracker.begin("place_first_toast", attempt_id=1)

    accepted = tracker.report(
        skill_name="place_first_toast",
        attempt_id=1,
        status=VLM_SUCCESS,
        message="done",
    )

    assert accepted is True
    result = tracker.get("place_first_toast")
    assert result is not None
    assert result.status == VLM_SUCCESS


def test_active_skill_tracker_still_accepts_legacy_attempt_zero() -> None:
    tracker = _ActiveSkillTracker()
    tracker.begin("place_first_toast", attempt_id=7)

    accepted = tracker.report(
        skill_name="place_first_toast",
        attempt_id=0,
        status=VLM_FAILURE,
        message="stop now",
    )

    assert accepted is True
    result = tracker.get("place_first_toast")
    assert result is not None
    assert result.status == VLM_FAILURE


def test_active_skill_tracker_rejects_stale_attempt_id() -> None:
    tracker = _ActiveSkillTracker()
    tracker.begin("place_first_toast", attempt_id=2)

    accepted = tracker.report(
        skill_name="place_first_toast",
        attempt_id=1,
        status=VLM_SUCCESS,
        message="stale",
    )

    assert accepted is False
    assert tracker.get("place_first_toast") is None


def test_active_skill_tracker_preserves_result_when_same_attempt_begins_again() -> None:
    tracker = _ActiveSkillTracker()
    tracker.begin("place_second_toast", attempt_id=3)
    tracker.report(
        skill_name="place_second_toast",
        attempt_id=3,
        status=VLM_SUCCESS,
        message="already done",
    )

    tracker.begin("place_second_toast", attempt_id=3)

    result = tracker.get("place_second_toast")
    assert result is not None
    assert result.status == VLM_SUCCESS
    assert result.message == "already done"
