"""@file spatial_prior.py
@brief Deterministic spatial-prior out-of-distribution (OOD) gate for BT skills.

This module is the runtime half of the spatial-prior gating feature. It answers
one narrow, quantitative question before a learned skill runs:

    "Is the object the policy is about to manipulate located where the policy was
     actually trained to handle it?"

It does NOT judge task semantics (that is the VLM's job). The two checks are
intentionally independent and complementary:

  - Spatial prior (this module): fast, deterministic, no GPU. Detects spatial
    out-of-distribution object placements using a Gaussian fitted offline from
    the training demonstrations.
  - VLM gate (existing VlmNode): slow, semantic. Decides whether the task is
    actually complete / the scene is correct.

The prior is a 3D Gaussian N(mu, Sigma) over the object position (expressed in a
single robot base frame) estimated from the training dataset. At runtime we
compute the Mahalanobis distance of the observed object position to that
Gaussian. Under the in-distribution hypothesis the squared Mahalanobis distance
follows a chi-square distribution with 3 degrees of freedom, which gives a
principled, tunable acceptance threshold.

IMPORTANT MODELLING CAVEAT (documented, not hidden):
The offline prior is fitted from the end-effector position at the grasp instant
(the frame where the gripper transitions open -> closed). That grasp pose is a
PROXY for the object position: it differs from a perception object centroid by a
roughly constant grasp offset (gripper geometry + approach direction). The gate
is therefore designed to run first in SHADOW mode on the real robot so the
operator can measure the real observed-vs-prior distance, calibrate the offset
and/or threshold, and only then switch to ENFORCE mode. See
`docs/spatial_prior_gating.md` for the full rationale.

The module depends only on numpy so it stays trivially unit-testable without
ROS2, torch, or robot hardware.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

# Verdict status constants. Kept as plain strings so they serialize cleanly into
# logs and JSON without importing an enum across the ROS2 boundary.
PASS = "PASS"  # nosec B105 - verifier status token, not a password.
FAIL = "FAIL"
ABSTAIN = "ABSTAIN"

# Schema version for the on-disk prior JSON. Bump only on incompatible changes.
PRIOR_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class SpatialPriorVerdict:
    """Outcome of evaluating one observed object position against a prior.

    Attributes:
    - status: one of PASS (in-distribution), FAIL (out-of-distribution), or
      ABSTAIN (not enough information to decide; the gate must not block).
    - distance: Mahalanobis distance when computed, else None.
    - threshold: acceptance threshold the distance was compared against.
    - reason: short machine-friendly reason string for observability.
    - frame_id: frame of the observed position used for the decision.
    - n_demos: number of demonstrations the prior was fitted from.
    """

    status: str
    reason: str
    distance: float | None = None
    threshold: float | None = None
    frame_id: str | None = None
    n_demos: int | None = None

    @property
    def blocks(self) -> bool:
        """@brief Whether this verdict should block a skill under ENFORCE mode.

        Only an explicit FAIL blocks. ABSTAIN never blocks because the gate
        could not gather enough information to make a safe decision.
        """
        return self.status == FAIL

    def as_dict(self) -> dict[str, Any]:
        """@brief JSON/log-friendly representation of the verdict."""
        return {
            "status": self.status,
            "reason": self.reason,
            "distance": None if self.distance is None else round(float(self.distance), 4),
            "threshold": None if self.threshold is None else round(float(self.threshold), 4),
            "frame_id": self.frame_id,
            "n_demos": self.n_demos,
        }


@dataclass
class SpatialPrior:
    """A fitted 3D Gaussian spatial prior used to gate a single skill.

    The prior is loaded from a JSON file produced by `fit_spatial_prior.py`. It
    stores the mean position `mu`, the covariance `sigma`, the frame the
    positions live in, and the acceptance threshold on the Mahalanobis distance.
    """

    skill: str
    object_name: str
    frame_id: str
    mu: np.ndarray
    sigma: np.ndarray
    n_demos: int
    mahalanobis_threshold: float
    source_dataset: str = ""
    proxy: str = "grasp_ee_position"
    min_pose_confidence: float = 0.0
    sigma_regularization_m2: float = 1e-6
    confidence_level: float = 0.99
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    # Cached inverse covariance, computed lazily after construction.
    _sigma_inv: np.ndarray | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """@brief Validate shapes and precompute the regularized inverse covariance."""
        self.mu = np.asarray(self.mu, dtype=float).reshape(-1)
        if self.mu.shape != (3,):
            raise ValueError(f"Prior mu must be a 3-vector, got shape {self.mu.shape}.")
        self.sigma = np.asarray(self.sigma, dtype=float)
        if self.sigma.shape != (3, 3):
            raise ValueError(f"Prior sigma must be 3x3, got shape {self.sigma.shape}.")
        if self.n_demos < 1:
            raise ValueError("Prior n_demos must be >= 1.")
        if self.mahalanobis_threshold <= 0:
            raise ValueError("Prior mahalanobis_threshold must be > 0.")
        # Regularize the covariance so it is always invertible even when one
        # axis has near-zero variance (e.g. a flat tabletop grasp where z barely
        # changes across demos). Adding a small isotropic term is the standard,
        # numerically safe way to do this.
        regularized = self.sigma + np.eye(3) * float(self.sigma_regularization_m2)
        try:
            self._sigma_inv = np.linalg.inv(regularized)
        except np.linalg.LinAlgError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Prior covariance is not invertible: {exc}") from exc

    @property
    def sigma_inv(self) -> np.ndarray:
        """@brief Regularized inverse covariance used by the Mahalanobis metric."""
        assert self._sigma_inv is not None  # set in __post_init__
        return self._sigma_inv

    def mahalanobis_distance(self, position: np.ndarray) -> float:
        """@brief Mahalanobis distance of a 3D position to this prior.

        @param position 3-vector object position in `self.frame_id`.
        @return Non-negative Mahalanobis distance (sqrt of the quadratic form).
        """
        delta = np.asarray(position, dtype=float).reshape(-1) - self.mu
        if delta.shape != (3,):
            raise ValueError(f"position must be a 3-vector, got shape {delta.shape}.")
        squared = float(delta @ self.sigma_inv @ delta)
        # Numerical noise can produce a tiny negative value; clamp to zero.
        return float(np.sqrt(max(squared, 0.0)))

    def evaluate(
        self,
        *,
        observed_translation: np.ndarray | list[float] | None,
        frame_id: str | None,
        pose_confidence: float | None = None,
    ) -> SpatialPriorVerdict:
        """@brief Decide PASS / FAIL / ABSTAIN for one observed object position.

        The gate ABSTAINS (never blocks) whenever it cannot make a trustworthy
        decision: missing pose, frame mismatch (e.g. perception returned a
        camera-frame pose because hand-eye calibration is missing), or a pose
        whose confidence is below the configured minimum.

        @param observed_translation 3D object position, or None when unavailable.
        @param frame_id Frame the observed position is expressed in.
        @param pose_confidence Optional perception confidence in [0, 1].
        @return A `SpatialPriorVerdict`.
        """
        if observed_translation is None:
            return SpatialPriorVerdict(
                status=ABSTAIN,
                reason="no_observed_pose",
                frame_id=frame_id,
                n_demos=self.n_demos,
            )

        position = np.asarray(observed_translation, dtype=float).reshape(-1)
        if position.shape != (3,) or not np.all(np.isfinite(position)):
            return SpatialPriorVerdict(
                status=ABSTAIN,
                reason="invalid_observed_pose",
                frame_id=frame_id,
                n_demos=self.n_demos,
            )

        # Frame mismatch is the common real-robot failure: without calibrated
        # hand-eye transforms the perception node returns camera-frame poses,
        # which are NOT comparable to a base-frame prior. Abstain loudly.
        if frame_id is not None and frame_id != self.frame_id:
            return SpatialPriorVerdict(
                status=ABSTAIN,
                reason=f"frame_mismatch:{frame_id}!={self.frame_id}",
                frame_id=frame_id,
                n_demos=self.n_demos,
            )

        if pose_confidence is not None and pose_confidence < self.min_pose_confidence:
            return SpatialPriorVerdict(
                status=ABSTAIN,
                reason=f"low_pose_confidence:{pose_confidence:.3f}<{self.min_pose_confidence:.3f}",
                frame_id=frame_id,
                n_demos=self.n_demos,
            )

        distance = self.mahalanobis_distance(position)
        status = PASS if distance <= self.mahalanobis_threshold else FAIL
        return SpatialPriorVerdict(
            status=status,
            reason="in_distribution" if status == PASS else "out_of_distribution",
            distance=distance,
            threshold=self.mahalanobis_threshold,
            frame_id=self.frame_id,
            n_demos=self.n_demos,
        )

    # ---- (de)serialization -------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """@brief Serialize the prior to a JSON-ready dict."""
        return {
            "schema_version": PRIOR_SCHEMA_VERSION,
            "skill": self.skill,
            "object": self.object_name,
            "source_dataset": self.source_dataset,
            "frame_id": self.frame_id,
            "proxy": self.proxy,
            "n_demos": int(self.n_demos),
            "mu": [float(v) for v in self.mu],
            "sigma": [[float(v) for v in row] for row in self.sigma],
            "sigma_regularization_m2": float(self.sigma_regularization_m2),
            "mahalanobis_threshold": float(self.mahalanobis_threshold),
            "confidence_level": float(self.confidence_level),
            "min_pose_confidence": float(self.min_pose_confidence),
            "notes": self.notes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpatialPrior:
        """@brief Build a `SpatialPrior` from a parsed JSON dict."""
        version = int(data.get("schema_version", 0))
        if version != PRIOR_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported spatial prior schema_version={version}. Expected {PRIOR_SCHEMA_VERSION}."
            )
        required = ("skill", "frame_id", "mu", "sigma", "n_demos", "mahalanobis_threshold")
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Spatial prior JSON is missing required keys: {missing}.")
        return cls(
            skill=str(data["skill"]),
            object_name=str(data.get("object", "")),
            frame_id=str(data["frame_id"]),
            mu=np.asarray(data["mu"], dtype=float),
            sigma=np.asarray(data["sigma"], dtype=float),
            n_demos=int(data["n_demos"]),
            mahalanobis_threshold=float(data["mahalanobis_threshold"]),
            source_dataset=str(data.get("source_dataset", "")),
            proxy=str(data.get("proxy", "grasp_ee_position")),
            min_pose_confidence=float(data.get("min_pose_confidence", 0.0)),
            sigma_regularization_m2=float(data.get("sigma_regularization_m2", 1e-6)),
            confidence_level=float(data.get("confidence_level", 0.99)),
            notes=str(data.get("notes", "")),
            metadata=dict(data.get("metadata", {})),
        )

    def save(self, path: str | Path) -> None:
        """@brief Write the prior to a JSON file (parent dirs created)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> SpatialPrior:
        """@brief Load a prior from a JSON file produced by the fitter."""
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)


def chi_square_threshold(confidence_level: float, dof: int = 3) -> float:
    """@brief Mahalanobis acceptance threshold for a Gaussian OOD test.

    The squared Mahalanobis distance of an in-distribution sample to a fitted
    Gaussian is chi-square distributed with `dof` degrees of freedom. The
    acceptance threshold on the (non-squared) Mahalanobis distance is therefore
    sqrt(chi2.ppf(confidence_level, dof)).

    This implementation avoids a hard SciPy dependency: it uses SciPy when
    available, otherwise falls back to a small lookup table for the common
    confidence levels with dof=3.

    @param confidence_level Probability mass to keep as in-distribution, e.g. 0.99.
    @param dof Degrees of freedom (3 for a 3D position prior).
    @return Mahalanobis distance threshold (> 0).
    """
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be in the open interval (0, 1).")
    try:
        from scipy.stats import chi2  # type: ignore

        return float(np.sqrt(chi2.ppf(confidence_level, dof)))
    except Exception as exc:  # noqa: BLE001 - SciPy optional; fall back to a table.
        if dof != 3:
            raise ValueError(
                "chi_square_threshold fallback table only supports dof=3 without SciPy."
            ) from exc
        # sqrt(chi2.ppf(level, df=3)) for common levels.
        table = {
            0.90: 2.5003,
            0.95: 2.7955,
            0.975: 3.0575,
            0.99: 3.3682,
            0.995: 3.5707,
            0.999: 4.0331,
        }
        if confidence_level not in table:
            raise ValueError(
                "Without SciPy, confidence_level must be one of "
                f"{sorted(table)} for dof=3; got {confidence_level}."
            ) from exc
        return table[confidence_level]
