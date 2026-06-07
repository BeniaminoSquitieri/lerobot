#!/usr/bin/env python

"""Pin disambiguating context in select VLM error messages.

Tests do not pin exact wording; they assert that critical context appears as
substrings inside ``ValueError`` text raised by ``SceneVerdictStore.report``.
"""

from __future__ import annotations

import pytest

from lerobot_bt_python.vlm.verification import SceneVerdictStore


def test_report_with_invalid_status_mentions_token_and_expected_set() -> None:
    """An unknown status must surface both the offending token and the allowed set."""
    registry = SceneVerdictStore(known_skill_names={"pick_apple"})
    registry.begin_attempt("pick_apple")
    bad_token = "DEFINITELY_NOT_A_STATUS"

    with pytest.raises(ValueError) as excinfo:
        registry.report(skill_name="pick_apple", status=bad_token)

    message = str(excinfo.value)
    assert bad_token in message, f"Error message should include the offending status token; got: {message!r}"
    assert "Expected one of" in message, (
        f"Error message should advertise the expected vocabulary; got: {message!r}"
    )


def test_report_with_invalid_status_lists_known_statuses() -> None:
    """The expected vocabulary should enumerate at least SUCCESS and FAILURE."""
    registry = SceneVerdictStore(known_skill_names={"pick_apple"})
    registry.begin_attempt("pick_apple")

    with pytest.raises(ValueError) as excinfo:
        registry.report(skill_name="pick_apple", status="nope")

    message = str(excinfo.value)
    for required in ("SUCCESS", "FAILURE"):
        assert required in message, f"Error message should mention the {required} status; got: {message!r}"
