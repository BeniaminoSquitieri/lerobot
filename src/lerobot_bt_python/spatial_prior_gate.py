"""@file spatial_prior_gate.py
@brief Runtime orchestration for the spatial-prior OOD gate inside the BT server.

This module bridges three things that otherwise live in separate places:
  - the fitted priors on disk (`spatial_prior.SpatialPrior`),
  - the executor config (`config.SpatialPriorGateConfig`),
  - the live object pose obtained from the perception QueryObjectPose service.

It is deliberately ROS-agnostic: the live pose is supplied through an injected
`pose_provider` callable so the gate can be unit-tested without ROS2, the robot,
or the perception node. The BT server wires a real `pose_provider` backed by a
ROS service client; tests pass a fake.

The gate runs in one of three modes (see SpatialPriorGateConfig):
  - "off"     : `enabled` is False, `evaluate` is never called.
  - "shadow"  : evaluate + log, but `should_block` is always False.
  - "enforce" : a FAIL verdict blocks the skill; ABSTAIN never blocks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Optional

from .config import SpatialPriorGateConfig
from .spatial_prior import ABSTAIN, FAIL, PASS, SpatialPrior, SpatialPriorVerdict

# A pose_provider takes a perception object name and returns the observed pose
# as (translation_xyz | None, frame_id | None, confidence | None).
PoseProvider = Callable[[str], "ObservedPose"]


class ObservedPose:
    """Lightweight container for a perceived object pose."""

    __slots__ = ("translation", "frame_id", "confidence", "error")

    def __init__(
        self,
        translation: Optional[list[float]] = None,
        frame_id: Optional[str] = None,
        confidence: Optional[float] = None,
        error: Optional[str] = None,
    ) -> None:
        self.translation = translation
        self.frame_id = frame_id
        self.confidence = confidence
        self.error = error


def parse_object_pose_json(pose_json: str) -> ObservedPose:
    """@brief Parse a perception QueryObjectPose `pose_json` payload.

    The perception node returns the object fact built by
    `bt_planning.scene_facts.build_object_pose_fact`, which contains at least
    `frame_id`, `pose.translation`, and `pose_confidence`.

    @param pose_json JSON string from the service response.
    @return An ObservedPose; `error` is set when the payload is unusable.
    """
    if not pose_json:
        return ObservedPose(error="empty_pose_json")
    try:
        fact = json.loads(pose_json)
    except Exception as exc:  # noqa: BLE001
        return ObservedPose(error=f"invalid_json:{exc}")
    if not isinstance(fact, dict):
        return ObservedPose(error="pose_json_not_object")

    pose = fact.get("pose")
    translation = None
    if isinstance(pose, dict):
        raw = pose.get("translation")
        if isinstance(raw, (list, tuple)) and len(raw) == 3:
            try:
                translation = [float(v) for v in raw]
            except (TypeError, ValueError):
                translation = None

    frame_id = fact.get("frame_id")
    frame_id = str(frame_id) if frame_id is not None else None

    confidence = fact.get("pose_confidence")
    try:
        confidence = None if confidence is None else float(confidence)
    except (TypeError, ValueError):
        confidence = None

    if translation is None:
        return ObservedPose(frame_id=frame_id, confidence=confidence, error="no_translation")
    return ObservedPose(translation=translation, frame_id=frame_id, confidence=confidence)


class SpatialPriorGate:
    """Loads priors and evaluates the spatial-prior gate for gated skills."""

    def __init__(
        self,
        cfg: SpatialPriorGateConfig,
        *,
        package_dir: str | Path,
        logger: Any = None,
    ) -> None:
        """@brief Build the gate and eagerly load the configured priors.

        @param cfg The validated SpatialPriorGateConfig.
        @param package_dir Directory used to resolve relative prior paths.
        @param logger Optional object with info/warning/error methods.
        """
        self.cfg = cfg
        self.enabled = cfg.mode != "off"
        self.logger = logger
        self._priors: dict[str, SpatialPrior] = {}
        self._objects: dict[str, str] = {}
        package_dir = Path(package_dir)

        if not self.enabled:
            return

        priors_dir = Path(cfg.priors_dir)
        if not priors_dir.is_absolute():
            priors_dir = package_dir / priors_dir

        for skill_name, prior_file in cfg.skill_priors.items():
            prior_path = Path(prior_file)
            if not prior_path.is_absolute():
                prior_path = priors_dir / prior_path
            try:
                prior = SpatialPrior.load(prior_path)
            except Exception as exc:  # noqa: BLE001
                self._log(
                    "error",
                    f"spatial_prior_gate: failed to load prior for skill '{skill_name}' "
                    f"from {prior_path}: {exc}",
                )
                continue
            self._priors[skill_name] = prior
            self._objects[skill_name] = cfg.skill_objects.get(skill_name) or prior.object_name
            self._log(
                "info",
                f"spatial_prior_gate: loaded prior for skill '{skill_name}' "
                f"(object={self._objects[skill_name]!r}, n_demos={prior.n_demos}, "
                f"frame={prior.frame_id}, threshold={prior.mahalanobis_threshold:.3f}).",
            )

    def _log(self, level: str, message: str) -> None:
        """@brief Emit a log line through the injected logger if present."""
        if self.logger is None:
            return
        getattr(self.logger, level, None) and getattr(self.logger, level)(message)

    def gates_skill(self, skill_name: str) -> bool:
        """@brief Whether the gate is active and a prior exists for this skill."""
        return self.enabled and skill_name in self._priors

    def object_for_skill(self, skill_name: str) -> Optional[str]:
        """@brief Perception object name queried for a gated skill, if any."""
        return self._objects.get(skill_name)

    def evaluate(self, skill_name: str, pose_provider: PoseProvider) -> Optional[SpatialPriorVerdict]:
        """@brief Evaluate the gate for one skill.

        @param skill_name BT skill about to run.
        @param pose_provider Callable mapping object name -> ObservedPose.
        @return A verdict, or None when the skill is not gated.
        """
        if not self.gates_skill(skill_name):
            return None

        prior = self._priors[skill_name]
        object_name = self._objects[skill_name]
        try:
            observed = pose_provider(object_name)
        except Exception as exc:  # noqa: BLE001
            verdict = SpatialPriorVerdict(
                status=ABSTAIN,
                reason=f"pose_provider_error:{exc}",
                frame_id=None,
                n_demos=prior.n_demos,
            )
            self._log_verdict(skill_name, object_name, verdict)
            return verdict

        if observed.error:
            verdict = SpatialPriorVerdict(
                status=ABSTAIN,
                reason=f"perception:{observed.error}",
                frame_id=observed.frame_id,
                n_demos=prior.n_demos,
            )
            self._log_verdict(skill_name, object_name, verdict)
            return verdict

        verdict = prior.evaluate(
            observed_translation=observed.translation,
            frame_id=observed.frame_id,
            pose_confidence=observed.confidence,
        )
        self._log_verdict(skill_name, object_name, verdict)
        return verdict

    def should_block(self, verdict: Optional[SpatialPriorVerdict]) -> bool:
        """@brief Whether a verdict should block skill execution.

        Only an explicit FAIL blocks, and only in ENFORCE mode. SHADOW mode
        observes without ever blocking; ABSTAIN never blocks in any mode.
        """
        if verdict is None:
            return False
        if self.cfg.mode != "enforce":
            return False
        return verdict.blocks

    def _log_verdict(
        self, skill_name: str, object_name: str, verdict: SpatialPriorVerdict
    ) -> None:
        """@brief Structured, greppable log line for one gate evaluation."""
        level = "warning" if verdict.status == FAIL else "info"
        payload = verdict.as_dict()
        self._log(
            level,
            "event=spatial_prior_gate "
            f"mode={self.cfg.mode} skill={skill_name!r} object={object_name!r} "
            f"status={verdict.status} reason={verdict.reason!r} "
            f"distance={payload['distance']} threshold={payload['threshold']} "
            f"frame={verdict.frame_id!r} n_demos={verdict.n_demos}",
        )
