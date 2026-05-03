"""Closed-set scene state types and helpers for supervisor decisions."""

"""Minimal scene-state estimation for the collaborative sandwich task."""

from __future__ import annotations

from dataclasses import dataclass

from .planner_schema import SceneEstimate, StepVerification


@dataclass
class SandwichSceneObservation:
    first_toast_on_plate: bool = False
    ingredient_on_first_toast: bool = False
    second_toast_on_top: bool = False


class SandwichSceneEstimator:
    """Closed-set state estimator.

    This is intentionally deterministic. A future VLM can replace the boolean
    inputs, but the planner contract stays the same.
    """

    def estimate(self, observation: SandwichSceneObservation) -> SceneEstimate:
        if observation.second_toast_on_top:
            return SceneEstimate(
                phase="DONE",
                observed_state="sandwich complete",
                confidence=1.0,
            )
        if observation.ingredient_on_first_toast:
            return SceneEstimate(
                phase="NEED_SECOND_TOAST",
                observed_state="first toast and ingredient are present",
                confidence=1.0,
            )
        if observation.first_toast_on_plate:
            return SceneEstimate(
                phase="NEED_POURING",
                observed_state="first toast is on the plate",
                confidence=1.0,
            )
        return SceneEstimate(
            phase="NEED_FIRST_TOAST",
            observed_state="first toast is still missing",
            confidence=1.0,
        )

    def verify_step(self, step_name: str, observation: SandwichSceneObservation) -> StepVerification:
        scene_estimate = self.estimate(observation)

        if step_name == "place_first_toast":
            success = observation.first_toast_on_plate
            failure_reason = "first toast is not yet on the plate"
        elif step_name == "pour_ingredient":
            success = observation.ingredient_on_first_toast
            failure_reason = "ingredient is not visible on the first toast"
        elif step_name == "place_second_toast":
            success = observation.second_toast_on_top
            failure_reason = "second toast is not yet on top of the sandwich"
        else:
            return StepVerification(
                success=False,
                observed_state=scene_estimate.observed_state,
                failure_reason=f"unknown step '{step_name}'",
                confidence=0.0,
            )

        return StepVerification(
            success=success,
            observed_state=scene_estimate.observed_state,
            failure_reason="" if success else failure_reason,
            confidence=scene_estimate.confidence,
        )
