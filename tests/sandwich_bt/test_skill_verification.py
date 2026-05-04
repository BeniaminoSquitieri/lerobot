from __future__ import annotations

import pytest

from sandwich_bt_python.simulation import (
    MockGetSkillVerificationRequest,
    MockReportSkillVerificationRequest,
    MockRunNamedCommandRequest,
    build_demo_stack,
)
from sandwich_bt_python.verification import (
    FAILED_VERIFICATION_STATUS,
    PENDING_VERIFICATION_STATUS,
    SUCCESSFUL_VERIFICATION_STATUS,
    SkillVerificationRegistry,
)


def test_verification_registry_rejects_stale_attempt_reports() -> None:
    registry = SkillVerificationRegistry(known_skill_names={"place_first_toast"})

    first_attempt = registry.begin_attempt("place_first_toast")
    second_attempt = registry.begin_attempt("place_first_toast")

    stale_update = registry.report(
        skill_name="place_first_toast",
        attempt_id=first_attempt.attempt_id,
        status=FAILED_VERIFICATION_STATUS,
        message="old result",
    )

    assert first_attempt.attempt_id == 1
    assert second_attempt.attempt_id == 2
    assert not stale_update.accepted
    assert stale_update.snapshot is not None
    assert stale_update.snapshot.attempt_id == 2


def test_verification_registry_requires_known_success_or_failure_status() -> None:
    registry = SkillVerificationRegistry(known_skill_names={"place_first_toast"})
    registry.begin_attempt("place_first_toast")

    with pytest.raises(ValueError, match="Unsupported verification status"):
        registry.report(
            skill_name="place_first_toast",
            status=PENDING_VERIFICATION_STATUS,
        )


def test_mock_service_exposes_pending_then_successful_verification() -> None:
    service = build_demo_stack()

    skill_response = service.handle_request(
        MockRunNamedCommandRequest(kind="skill", name="place_first_toast")
    )
    pending = service.handle_verification_query(
        MockGetSkillVerificationRequest(skill_name="place_first_toast")
    )
    report = service.handle_verification_report(
        MockReportSkillVerificationRequest(
            skill_name="place_first_toast",
            status=SUCCESSFUL_VERIFICATION_STATUS,
            message="scene looks correct",
            confidence=0.91,
        )
    )
    resolved = service.handle_verification_query(
        MockGetSkillVerificationRequest(skill_name="place_first_toast")
    )

    assert skill_response.success
    assert pending.has_attempt
    assert pending.status == PENDING_VERIFICATION_STATUS
    assert report.accepted
    assert report.applied_attempt_id == pending.attempt_id
    assert resolved.status == SUCCESSFUL_VERIFICATION_STATUS
    assert resolved.message == "scene looks correct"
    assert resolved.confidence == pytest.approx(0.91)
