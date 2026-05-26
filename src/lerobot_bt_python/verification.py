# Comment: executes this BT logic statement.
"""@file verification.py
@brief Stateful relay for external post-skill VLM checks.

The BT runtime only knows that a learned skill finished executing. The final
decision about whether the scene looks correct can arrive later from an
external verifier such as a VLM. This module keeps the latest check attempt
per skill so the BT can poll for a verdict and the verifier can report one.
"""

# Comment: imports dependencies or symbols required by the module.
from __future__ import annotations

# Comment: imports dependencies or symbols required by the module.
import time
# Comment: imports dependencies or symbols required by the module.
from collections.abc import Callable
# Comment: imports dependencies or symbols required by the module.
from dataclasses import dataclass
# Comment: imports dependencies or symbols required by the module.
from threading import Lock

# Comment: assigns or prepares a value used by later statements.
VLM_PENDING = "PENDING"
# Comment: assigns or prepares a value used by later statements.
VLM_RUNNING = "RUNNING"
# Comment: assigns or prepares a value used by later statements.
VLM_WAIT_HUMAN = "WAIT_HUMAN"
# Comment: assigns or prepares a value used by later statements.
VLM_NEEDS_MANUAL_HELP = "MANUAL_INTERVENTION_REQUIRED"
# Comment: assigns or prepares a value used by later statements.
VLM_SUCCESS = "SUCCESS"
# Comment: assigns or prepares a value used by later statements.
VLM_FAILURE = "FAILURE"
# Comment: assigns or prepares a value used by later statements.
VLM_UNKNOWN = "UNKNOWN"

# Comment: assigns or prepares a value used by later statements.
VLM_TERMINAL_STATUSES = {
    # Comment: executes this BT logic statement.
    VLM_SUCCESS,
    # Comment: executes this BT logic statement.
    VLM_FAILURE,
# Comment: closes a call, data structure, or multiline block.
}

# Comment: assigns or prepares a value used by later statements.
VLM_WAITING_STATUSES = {
    # Comment: executes this BT logic statement.
    VLM_PENDING,
    # Comment: executes this BT logic statement.
    VLM_RUNNING,
    # Comment: executes this BT logic statement.
    VLM_WAIT_HUMAN,
    # Comment: executes this BT logic statement.
    VLM_NEEDS_MANUAL_HELP,
# Comment: closes a call, data structure, or multiline block.
}

# Comment: assigns or prepares a value used by later statements.
_ALLOWED_VLM_STATUSES = VLM_TERMINAL_STATUSES | VLM_WAITING_STATUSES


# Comment: applies a decorator to the following definition.
@dataclass(frozen=True)
class VlmCheckSnapshot:
    # Comment: executes this BT logic statement.
    """@brief Immutable state for the latest VLM check attempt of one skill."""

    # Comment: executes this BT logic statement.
    skill_name: str
    # Comment: executes this BT logic statement.
    """Skill name used by the BT XML and Python server."""

    # Comment: executes this BT logic statement.
    attempt_id: int
    # Comment: executes this BT logic statement.
    """Monotonic attempt id for this skill; increments on each successful rollout."""

    # Comment: executes this BT logic statement.
    status: str
    # Comment: executes this BT logic statement.
    """VLM check state: waiting, terminal, or UNKNOWN."""

    # Comment: executes this BT logic statement.
    message: str
    # Comment: executes this BT logic statement.
    """Human-readable explanation for logs and operators."""

    # Comment: assigns or prepares a value used by later statements.
    created_at_s: float = 0.0
    # Comment: executes this BT logic statement.
    """Monotonic timestamp when this VLM check attempt was opened."""

    # Comment: assigns or prepares a value used by later statements.
    timeout_s: float = 0.0
    # Comment: executes this BT logic statement.
    """Maximum seconds to wait for SUCCESS; non-positive values disable expiry."""


# Comment: applies a decorator to the following definition.
@dataclass(frozen=True)
class VlmCheckUpdate:
    # Comment: executes this BT logic statement.
    """@brief Result returned after trying to apply a verifier report."""

    # Comment: executes this BT logic statement.
    accepted: bool
    # Comment: executes this BT logic statement.
    """True when the report was applied to the active pending attempt."""

    # Comment: executes this BT logic statement.
    message: str
    # Comment: executes this BT logic statement.
    """Explanation of why the report was accepted or rejected."""

    # Comment: executes this BT logic statement.
    snapshot: VlmCheckSnapshot | None
    # Comment: executes this BT logic statement.
    """Updated or current snapshot; absent when no attempt exists."""


# Comment: declares the class VlmCheckRegistry.
class VlmCheckRegistry:
    # Comment: executes this BT logic statement.
    """@brief In-memory VLM check state keyed by BT skill name."""

    # Comment: defines the function or method __init__.
    def __init__(
        # Comment: executes this BT logic statement.
        self,
        # Comment: executes this BT logic statement.
        *,
        # Comment: assigns or prepares a value used by later statements.
        known_skill_names: set[str] | None = None,
        # Comment: assigns or prepares a value used by later statements.
        vlm_timeout_s: float = 30.0,
        # Comment: assigns or prepares a value used by later statements.
        clock: Callable[[], float] = time.monotonic,
    # Comment: executes this BT logic statement.
    ) -> None:
        # Comment: executes this BT logic statement.
        """@brief Create an empty registry constrained to optional known names."""
        # Comment: evaluates a condition and chooses the branch to run.
        if vlm_timeout_s < 0:
            # Comment: raises an explicit error for the caller.
            raise ValueError("vlm_timeout_s must be >= 0.")
        # Comment: updates state or a field on the current object.
        self._known_skill_names = set(known_skill_names or set())
        # Comment: updates state or a field on the current object.
        self._vlm_timeout_s = float(vlm_timeout_s)
        # Comment: updates state or a field on the current object.
        self._clock = clock
        # Comment: updates state or a field on the current object.
        self._attempt_counters: dict[str, int] = {}
        # Comment: updates state or a field on the current object.
        self._attempts: dict[str, VlmCheckSnapshot] = {}
        # Comment: updates state or a field on the current object.
        self._lock = Lock()

    # Comment: defines the function or method register_skill_name.
    def register_skill_name(self, skill_name: str) -> None:
        # Comment: executes this BT logic statement.
        """@brief Allow later VLM check calls for a skill discovered at runtime."""
        # Comment: evaluates a condition and chooses the branch to run.
        if not skill_name:
            # Comment: raises an explicit error for the caller.
            raise ValueError("skill_name must not be empty.")
        # Comment: opens a managed context and guarantees its cleanup.
        with self._lock:
            # Comment: closes a call, data structure, or multiline block.
            self._known_skill_names.add(skill_name)

    # Comment: defines the function or method begin_attempt.
    def begin_attempt(self, skill_name: str, *, message: str = "") -> VlmCheckSnapshot:
        # Comment: executes this BT logic statement.
        """@brief Create a fresh pending VLM check state for one skill attempt."""
        # Comment: assigns or prepares a value used by later statements.
        default_message = f"Awaiting VLM result for skill '{skill_name}'."
        # Comment: opens a managed context and guarantees its cleanup.
        with self._lock:
            # Comment: closes a call, data structure, or multiline block.
            self._validate_skill_name(skill_name)
            # Comment: assigns or prepares a value used by later statements.
            attempt_id = self._attempt_counters.get(skill_name, 0) + 1
            # Comment: updates state or a field on the current object.
            self._attempt_counters[skill_name] = attempt_id
            # Comment: assigns or prepares a value used by later statements.
            snapshot = VlmCheckSnapshot(
                # Comment: assigns or prepares a value used by later statements.
                skill_name=skill_name,
                # Comment: assigns or prepares a value used by later statements.
                attempt_id=attempt_id,
                # Comment: assigns or prepares a value used by later statements.
                status=VLM_PENDING,
                # Comment: assigns or prepares a value used by later statements.
                message=message or default_message,
                # Comment: assigns or prepares a value used by later statements.
                created_at_s=self._clock(),
                # Comment: assigns or prepares a value used by later statements.
                timeout_s=self._vlm_timeout_s,
            # Comment: closes a call, data structure, or multiline block.
            )
            # Comment: updates state or a field on the current object.
            self._attempts[skill_name] = snapshot
            # Comment: returns the computed value to the caller.
            return snapshot

    # Comment: defines the function or method get_latest.
    def get_latest(self, skill_name: str) -> VlmCheckSnapshot | None:
        # Comment: executes this BT logic statement.
        """@brief Return the latest attempt snapshot for `skill_name`, if any."""
        # Comment: opens a managed context and guarantees its cleanup.
        with self._lock:
            # Comment: closes a call, data structure, or multiline block.
            self._validate_skill_name(skill_name)
            # Comment: assigns or prepares a value used by later statements.
            latest_snapshot = self._attempts.get(skill_name)
            # Comment: returns the computed value to the caller.
            return self._expire_if_needed_locked(latest_snapshot)

    # Comment: defines the function or method report.
    def report(
        # Comment: executes this BT logic statement.
        self,
        # Comment: executes this BT logic statement.
        *,
        # Comment: executes this BT logic statement.
        skill_name: str,
        # Comment: executes this BT logic statement.
        status: str,
        # Comment: assigns or prepares a value used by later statements.
        message: str = "",
        # Comment: assigns or prepares a value used by later statements.
        attempt_id: int = 0,
    # Comment: executes this BT logic statement.
    ) -> VlmCheckUpdate:
        # Comment: executes this BT logic statement.
        """@brief Apply an external VLM result to the latest open attempt."""
        # Comment: evaluates a condition and chooses the branch to run.
        if status not in _ALLOWED_VLM_STATUSES:
            # Comment: raises an explicit error for the caller.
            raise ValueError(
                # Comment: executes this BT logic statement.
                f"Unsupported VLM status '{status}'. Expected one of {sorted(_ALLOWED_VLM_STATUSES)}."
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: opens a managed context and guarantees its cleanup.
        with self._lock:
            # Comment: closes a call, data structure, or multiline block.
            self._validate_skill_name(skill_name)
            # Comment: assigns or prepares a value used by later statements.
            latest_snapshot = self._attempts.get(skill_name)
            # Comment: assigns or prepares a value used by later statements.
            latest_snapshot = self._expire_if_needed_locked(latest_snapshot)
            # Comment: evaluates a condition and chooses the branch to run.
            if latest_snapshot is None:
                # Comment: returns the computed value to the caller.
                return VlmCheckUpdate(
                    # Comment: assigns or prepares a value used by later statements.
                    accepted=False,
                    # Comment: assigns or prepares a value used by later statements.
                    message=f"No completed attempt is awaiting a VLM result for skill '{skill_name}'.",
                    # Comment: assigns or prepares a value used by later statements.
                    snapshot=None,
                # Comment: closes a call, data structure, or multiline block.
                )

            # Comment: assigns or prepares a value used by later statements.
            target_attempt_id = latest_snapshot.attempt_id if attempt_id == 0 else attempt_id
            # Comment: evaluates a condition and chooses the branch to run.
            if latest_snapshot.attempt_id != target_attempt_id:
                # Comment: returns the computed value to the caller.
                return VlmCheckUpdate(
                    # Comment: assigns or prepares a value used by later statements.
                    accepted=False,
                    # Comment: assigns or prepares a value used by later statements.
                    message=(
                        # Comment: executes this BT logic statement.
                        f"VLM result for skill '{skill_name}' targeted attempt {target_attempt_id}, "
                        # Comment: executes this BT logic statement.
                        f"but the latest attempt is {latest_snapshot.attempt_id}."
                    # Comment: executes this BT logic statement.
                    ),
                    # Comment: assigns or prepares a value used by later statements.
                    snapshot=latest_snapshot,
                # Comment: closes a call, data structure, or multiline block.
                )

            # Comment: evaluates a condition and chooses the branch to run.
            if latest_snapshot.status in VLM_TERMINAL_STATUSES:
                # Comment: returns the computed value to the caller.
                return VlmCheckUpdate(
                    # Comment: assigns or prepares a value used by later statements.
                    accepted=False,
                    # Comment: assigns or prepares a value used by later statements.
                    message=(
                        # Comment: executes this BT logic statement.
                        f"Attempt {target_attempt_id} for skill '{skill_name}' is already resolved as "
                        # Comment: executes this BT logic statement.
                        f"{latest_snapshot.status}."
                    # Comment: executes this BT logic statement.
                    ),
                    # Comment: assigns or prepares a value used by later statements.
                    snapshot=latest_snapshot,
                # Comment: closes a call, data structure, or multiline block.
                )

            # Comment: assigns or prepares a value used by later statements.
            updated_snapshot = VlmCheckSnapshot(
                # Comment: assigns or prepares a value used by later statements.
                skill_name=skill_name,
                # Comment: assigns or prepares a value used by later statements.
                attempt_id=target_attempt_id,
                # Comment: assigns or prepares a value used by later statements.
                status=status,
                # Comment: assigns or prepares a value used by later statements.
                message=message or f"External verifier reported {status} for skill '{skill_name}'.",
                # Comment: assigns or prepares a value used by later statements.
                created_at_s=latest_snapshot.created_at_s,
                # Comment: assigns or prepares a value used by later statements.
                timeout_s=latest_snapshot.timeout_s,
            # Comment: closes a call, data structure, or multiline block.
            )
            # Comment: updates state or a field on the current object.
            self._attempts[skill_name] = updated_snapshot
            # Comment: returns the computed value to the caller.
            return VlmCheckUpdate(
                # Comment: assigns or prepares a value used by later statements.
                accepted=True,
                # Comment: assigns or prepares a value used by later statements.
                message=f"Applied VLM status {status} to skill '{skill_name}' attempt {target_attempt_id}.",
                # Comment: assigns or prepares a value used by later statements.
                snapshot=updated_snapshot,
            # Comment: closes a call, data structure, or multiline block.
            )

    # Comment: defines the function or method _expire_if_needed_locked.
    def _expire_if_needed_locked(
        # Comment: executes this BT logic statement.
        self,
        # Comment: executes this BT logic statement.
        snapshot: VlmCheckSnapshot | None,
    # Comment: executes this BT logic statement.
    ) -> VlmCheckSnapshot | None:
        # Comment: executes this BT logic statement.
        """@brief Mark a waiting attempt as FAILURE once its VLM timeout expires."""
        # Comment: evaluates a condition and chooses the branch to run.
        if snapshot is None:
            # Comment: returns the computed value to the caller.
            return None
        # Comment: evaluates a condition and chooses the branch to run.
        if snapshot.status in VLM_TERMINAL_STATUSES:
            # Comment: returns the computed value to the caller.
            return snapshot
        # Comment: evaluates a condition and chooses the branch to run.
        if snapshot.timeout_s <= 0:
            # Comment: returns the computed value to the caller.
            return snapshot

        # Comment: assigns or prepares a value used by later statements.
        elapsed_s = self._clock() - snapshot.created_at_s
        # Comment: evaluates a condition and chooses the branch to run.
        if elapsed_s < snapshot.timeout_s:
            # Comment: returns the computed value to the caller.
            return snapshot

        # Comment: assigns or prepares a value used by later statements.
        failed_snapshot = VlmCheckSnapshot(
            # Comment: assigns or prepares a value used by later statements.
            skill_name=snapshot.skill_name,
            # Comment: assigns or prepares a value used by later statements.
            attempt_id=snapshot.attempt_id,
            # Comment: assigns or prepares a value used by later statements.
            status=VLM_FAILURE,
            # Comment: assigns or prepares a value used by later statements.
            message=(
                # Comment: executes this BT logic statement.
                f"VLM check attempt {snapshot.attempt_id} for skill '{snapshot.skill_name}' timed out "
                # Comment: executes this BT logic statement.
                f"after {snapshot.timeout_s:.2f}s without SUCCESS."
            # Comment: executes this BT logic statement.
            ),
            # Comment: assigns or prepares a value used by later statements.
            created_at_s=snapshot.created_at_s,
            # Comment: assigns or prepares a value used by later statements.
            timeout_s=snapshot.timeout_s,
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: updates state or a field on the current object.
        self._attempts[snapshot.skill_name] = failed_snapshot
        # Comment: returns the computed value to the caller.
        return failed_snapshot

    # Comment: defines the function or method _validate_skill_name.
    def _validate_skill_name(self, skill_name: str) -> None:
        # Comment: executes this BT logic statement.
        """@brief Reject empty or unknown skill names before state mutation."""
        # Comment: evaluates a condition and chooses the branch to run.
        if not skill_name:
            # Comment: raises an explicit error for the caller.
            raise ValueError("skill_name must not be empty.")
        # Comment: evaluates a condition and chooses the branch to run.
        if self._known_skill_names and skill_name not in self._known_skill_names:
            # Comment: raises an explicit error for the caller.
            raise ValueError(f"Unknown skill '{skill_name}'.")
