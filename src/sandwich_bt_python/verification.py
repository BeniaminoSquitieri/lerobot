"""Stateful relay for external post-skill verification.

The BT runtime only knows that a learned skill finished executing. The final
decision about whether the scene looks correct can arrive later from an
external verifier such as a VLM. This module keeps the latest attempt state
per skill so the BT can poll for a verdict and the verifier can report one.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

PENDING_VERIFICATION_STATUS = "PENDING"
SUCCESSFUL_VERIFICATION_STATUS = "SUCCESS"
FAILED_VERIFICATION_STATUS = "FAILURE"
UNKNOWN_VERIFICATION_STATUS = "UNKNOWN"

_ALLOWED_REPORTED_STATUSES = {
    SUCCESSFUL_VERIFICATION_STATUS,
    FAILED_VERIFICATION_STATUS,
}


@dataclass(frozen=True)
class SkillVerificationSnapshot:
    skill_name: str
    attempt_id: int
    status: str
    message: str
    confidence: float = 0.0


@dataclass(frozen=True)
class SkillVerificationUpdateResult:
    accepted: bool
    message: str
    snapshot: SkillVerificationSnapshot | None


class SkillVerificationRegistry:
    """In-memory verification state keyed by BT skill name."""

    def __init__(self, *, known_skill_names: set[str] | None = None) -> None:
        self._known_skill_names = set(known_skill_names or set())
        self._attempt_counters: dict[str, int] = {}
        self._attempts: dict[str, SkillVerificationSnapshot] = {}
        self._lock = Lock()

    def register_skill_name(self, skill_name: str) -> None:
        """Allow later verification calls for a skill discovered at runtime."""
        if not skill_name:
            raise ValueError("skill_name must not be empty.")
        with self._lock:
            self._known_skill_names.add(skill_name)

    def begin_attempt(self, skill_name: str, *, message: str = "") -> SkillVerificationSnapshot:
        """Create a fresh pending verification state for one skill attempt."""
        default_message = f"Awaiting external verification for skill '{skill_name}'."
        with self._lock:
            self._validate_skill_name(skill_name)
            attempt_id = self._attempt_counters.get(skill_name, 0) + 1
            self._attempt_counters[skill_name] = attempt_id
            snapshot = SkillVerificationSnapshot(
                skill_name=skill_name,
                attempt_id=attempt_id,
                status=PENDING_VERIFICATION_STATUS,
                message=message or default_message,
                confidence=0.0,
            )
            self._attempts[skill_name] = snapshot
            return snapshot

    def get_latest(self, skill_name: str) -> SkillVerificationSnapshot | None:
        with self._lock:
            self._validate_skill_name(skill_name)
            return self._attempts.get(skill_name)

    def report(
        self,
        *,
        skill_name: str,
        status: str,
        message: str = "",
        confidence: float = 0.0,
        attempt_id: int = 0,
    ) -> SkillVerificationUpdateResult:
        """Apply an external verification verdict to the latest pending attempt."""
        if status not in _ALLOWED_REPORTED_STATUSES:
            raise ValueError(
                f"Unsupported verification status '{status}'. Expected one of {sorted(_ALLOWED_REPORTED_STATUSES)}."
            )
        if confidence < 0.0:
            raise ValueError("verification confidence must be >= 0.")

        with self._lock:
            self._validate_skill_name(skill_name)
            latest_snapshot = self._attempts.get(skill_name)
            if latest_snapshot is None:
                return SkillVerificationUpdateResult(
                    accepted=False,
                    message=f"No completed attempt is awaiting verification for skill '{skill_name}'.",
                    snapshot=None,
                )

            target_attempt_id = latest_snapshot.attempt_id if attempt_id == 0 else attempt_id
            if latest_snapshot.attempt_id != target_attempt_id:
                return SkillVerificationUpdateResult(
                    accepted=False,
                    message=(
                        f"Verification report for skill '{skill_name}' targeted attempt {target_attempt_id}, "
                        f"but the latest attempt is {latest_snapshot.attempt_id}."
                    ),
                    snapshot=latest_snapshot,
                )

            if latest_snapshot.status != PENDING_VERIFICATION_STATUS:
                return SkillVerificationUpdateResult(
                    accepted=False,
                    message=(
                        f"Attempt {target_attempt_id} for skill '{skill_name}' is already resolved as "
                        f"{latest_snapshot.status}."
                    ),
                    snapshot=latest_snapshot,
                )

            updated_snapshot = SkillVerificationSnapshot(
                skill_name=skill_name,
                attempt_id=target_attempt_id,
                status=status,
                message=message or f"External verifier reported {status} for skill '{skill_name}'.",
                confidence=confidence,
            )
            self._attempts[skill_name] = updated_snapshot
            return SkillVerificationUpdateResult(
                accepted=True,
                message=f"Applied verification status {status} to skill '{skill_name}' attempt {target_attempt_id}.",
                snapshot=updated_snapshot,
            )

    def _validate_skill_name(self, skill_name: str) -> None:
        if not skill_name:
            raise ValueError("skill_name must not be empty.")
        if self._known_skill_names and skill_name not in self._known_skill_names:
            raise ValueError(f"Unknown skill '{skill_name}'.")
