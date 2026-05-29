"""@file verification.py
@brief Stateful relay for external post-skill VLM checks.

The BT runtime only knows that a learned skill finished executing. The final
decision about whether the scene looks correct can arrive later from an
external verifier such as a VLM. This module keeps the latest check attempt
per skill so the BT can poll for a verdict and the verifier can report one.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock

VLM_PENDING = "PENDING"
VLM_RUNNING = "RUNNING"
VLM_WAIT_HUMAN = "WAIT_HUMAN"
VLM_NEEDS_MANUAL_HELP = "MANUAL_INTERVENTION_REQUIRED"
VLM_SUCCESS = "SUCCESS"
VLM_FAILURE = "FAILURE"
VLM_UNKNOWN = "UNKNOWN"

VLM_TERMINAL_STATUSES = {
    VLM_SUCCESS,
    VLM_FAILURE,
}

VLM_WAITING_STATUSES = {
    VLM_PENDING,
    VLM_RUNNING,
    VLM_WAIT_HUMAN,
    VLM_NEEDS_MANUAL_HELP,
}

_ALLOWED_VLM_STATUSES = VLM_TERMINAL_STATUSES | VLM_WAITING_STATUSES


@dataclass(frozen=True)
class VlmCheckSnapshot:
    """@brief Immutable state for the latest VLM check attempt of one skill."""

    skill_name: str
    """Skill name used by the BT XML and Python server."""

    attempt_id: int
    """Monotonic attempt id for this skill; increments on each successful rollout."""

    status: str
    """VLM check state: waiting, terminal, or UNKNOWN."""

    message: str
    """Human-readable explanation for logs and operators."""

    created_at_s: float = 0.0
    """Monotonic timestamp when this VLM check attempt was opened."""

    timeout_s: float = 0.0
    """Maximum seconds to wait for SUCCESS; non-positive values disable expiry."""


@dataclass(frozen=True)
class VlmCheckUpdate:
    """@brief Result returned after trying to apply a verifier report."""

    accepted: bool
    """True when the report was applied to the active pending attempt."""

    message: str
    """Explanation of why the report was accepted or rejected."""

    snapshot: VlmCheckSnapshot | None
    """Updated or current snapshot; absent when no attempt exists."""


class SceneVerdictStore:
    """@brief In-memory VLM check state keyed by BT skill name."""

    def __init__(
        self,
        *,
        known_skill_names: set[str] | None = None,
        vlm_timeout_s: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """@brief Create an empty registry constrained to optional known names."""
        if vlm_timeout_s < 0:
            raise ValueError("vlm_timeout_s must be >= 0.")
        self._known_skill_names = set(known_skill_names or set())
        self._vlm_timeout_s = float(vlm_timeout_s)
        self._clock = clock
        self._attempt_counters: dict[str, int] = {}
        self._attempts: dict[str, VlmCheckSnapshot] = {}
        self._lock = Lock()

    def register_skill_name(self, skill_name: str) -> None:
        """@brief Allow later VLM check calls for a skill discovered at runtime."""
        if not skill_name:
            raise ValueError("skill_name must not be empty.")
        with self._lock:
            self._known_skill_names.add(skill_name)

    def begin_attempt(self, skill_name: str, *, message: str = "") -> VlmCheckSnapshot:
        """@brief Create a fresh pending VLM check state for one skill attempt."""
        default_message = f"Awaiting VLM result for skill '{skill_name}'."
        with self._lock:
            self._validate_skill_name(skill_name)
            attempt_id = self._attempt_counters.get(skill_name, 0) + 1
            self._attempt_counters[skill_name] = attempt_id
            snapshot = VlmCheckSnapshot(
                skill_name=skill_name,
                attempt_id=attempt_id,
                status=VLM_PENDING,
                message=message or default_message,
                created_at_s=self._clock(),
                timeout_s=self._vlm_timeout_s,
            )
            self._attempts[skill_name] = snapshot
            return snapshot

    def get_latest(self, skill_name: str) -> VlmCheckSnapshot | None:
        """@brief Return the latest attempt snapshot for `skill_name`, if any."""
        with self._lock:
            self._validate_skill_name(skill_name)
            latest_snapshot = self._attempts.get(skill_name)
            return self._expire_if_needed_locked(latest_snapshot)

    def report(
        self,
        *,
        skill_name: str,
        status: str,
        message: str = "",
        attempt_id: int = 0,
    ) -> VlmCheckUpdate:
        """@brief Apply an external VLM result to the latest open attempt."""
        if status not in _ALLOWED_VLM_STATUSES:
            raise ValueError(
                f"Unsupported VLM status '{status}'. Expected one of {sorted(_ALLOWED_VLM_STATUSES)}."
            )
        with self._lock:
            self._validate_skill_name(skill_name)
            latest_snapshot = self._attempts.get(skill_name)
            latest_snapshot = self._expire_if_needed_locked(latest_snapshot)
            if latest_snapshot is None:
                return VlmCheckUpdate(
                    accepted=False,
                    message=f"No completed attempt is awaiting a VLM result for skill '{skill_name}'.",
                    snapshot=None,
                )

            target_attempt_id = latest_snapshot.attempt_id if attempt_id == 0 else attempt_id
            if latest_snapshot.attempt_id != target_attempt_id:
                return VlmCheckUpdate(
                    accepted=False,
                    message=(
                        f"VLM result for skill '{skill_name}' targeted attempt {target_attempt_id}, "
                        f"but the latest attempt is {latest_snapshot.attempt_id}."
                    ),
                    snapshot=latest_snapshot,
                )

            if latest_snapshot.status in VLM_TERMINAL_STATUSES:
                return VlmCheckUpdate(
                    accepted=False,
                    message=(
                        f"Attempt {target_attempt_id} for skill '{skill_name}' is already resolved as "
                        f"{latest_snapshot.status}."
                    ),
                    snapshot=latest_snapshot,
                )

            updated_snapshot = VlmCheckSnapshot(
                skill_name=skill_name,
                attempt_id=target_attempt_id,
                status=status,
                message=message or f"External verifier reported {status} for skill '{skill_name}'.",
                created_at_s=latest_snapshot.created_at_s,
                timeout_s=latest_snapshot.timeout_s,
            )
            self._attempts[skill_name] = updated_snapshot
            return VlmCheckUpdate(
                accepted=True,
                message=f"Applied VLM status {status} to skill '{skill_name}' attempt {target_attempt_id}.",
                snapshot=updated_snapshot,
            )

    def _expire_if_needed_locked(
        self,
        snapshot: VlmCheckSnapshot | None,
    ) -> VlmCheckSnapshot | None:
        """@brief Mark a waiting attempt as FAILURE once its VLM timeout expires."""
        if snapshot is None:
            return None
        if snapshot.status in VLM_TERMINAL_STATUSES:
            return snapshot
        if snapshot.timeout_s <= 0:
            return snapshot

        elapsed_s = self._clock() - snapshot.created_at_s
        if elapsed_s < snapshot.timeout_s:
            return snapshot

        failed_snapshot = VlmCheckSnapshot(
            skill_name=snapshot.skill_name,
            attempt_id=snapshot.attempt_id,
            status=VLM_FAILURE,
            message=(
                f"VLM check attempt {snapshot.attempt_id} for skill '{snapshot.skill_name}' timed out "
                f"after {snapshot.timeout_s:.2f}s without SUCCESS."
            ),
            created_at_s=snapshot.created_at_s,
            timeout_s=snapshot.timeout_s,
        )
        self._attempts[snapshot.skill_name] = failed_snapshot
        return failed_snapshot

    def _validate_skill_name(self, skill_name: str) -> None:
        """@brief Reject empty or unknown skill names before state mutation."""
        if not skill_name:
            raise ValueError("skill_name must not be empty.")
        if self._known_skill_names and skill_name not in self._known_skill_names:
            raise ValueError(f"Unknown skill '{skill_name}'.")
