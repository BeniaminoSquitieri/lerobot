#!/usr/bin/env python

"""Safety wiring for BT robot action processors."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

from lerobot.processor.converters import robot_action_observation_to_transition, transition_to_robot_action
from lerobot_bt_python.processor_factory import build_robot_processor_pipeline, instantiate_processor_step

REPO_ROOT = Path(__file__).resolve().parents[2]
MAKE_SANDWICH_EXECUTOR_CONFIG = REPO_ROOT / "src/lerobot_bt_python/make_sandwich_executor.yaml"
SAFETY_PROCESSOR_NAME = "cartesian_action_safety_processor"
SCIPY_AVAILABLE = importlib.util.find_spec("scipy") is not None


def _pose(
    *,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    rx: float = 0.0,
    ry: float = 0.0,
    rz: float = 0.0,
) -> dict[str, float]:
    return {
        "position.x": x,
        "position.y": y,
        "position.z": z,
        "orientation.x": rx,
        "orientation.y": ry,
        "orientation.z": rz,
    }


def _build_safety_pipeline(*, mode: str, max_translation_m: float = 0.015, max_rotation_rad: float = 0.12):
    return build_robot_processor_pipeline(
        {
            "steps": [
                {
                    "registry_name": SAFETY_PROCESSOR_NAME,
                    "config": {
                        "max_translation_m": max_translation_m,
                        "max_rotation_rad": max_rotation_rad,
                        "mode": mode,
                    },
                }
            ]
        },
        to_transition=robot_action_observation_to_transition,
        to_output=transition_to_robot_action,
    )


def test_processor_factory_instantiates_registered_cartesian_safety_step() -> None:
    step = instantiate_processor_step(
        {
            "registry_name": SAFETY_PROCESSOR_NAME,
            "config": {
                "max_translation_m": 0.02,
                "max_rotation_rad": 0.2,
                "mode": "error",
            },
        }
    )

    from lerobot.robots.custom_manipulator.processor.safety_processor import CartesianActionSafetyProcessor

    assert isinstance(step, CartesianActionSafetyProcessor)
    assert step.max_translation_m == pytest.approx(0.02)
    assert step.max_rotation_rad == pytest.approx(0.2)
    assert step.mode == "error"


@pytest.mark.skipif(not SCIPY_AVAILABLE, reason="CartesianActionSafetyProcessor requires scipy.")
def test_cartesian_safety_rejects_large_absolute_target_through_bt_pipeline() -> None:
    pipeline = _build_safety_pipeline(mode="error")

    with pytest.raises(ValueError, match="Unsafe skill action rejected"):
        pipeline((_pose(x=0.03), _pose()))


@pytest.mark.skipif(not SCIPY_AVAILABLE, reason="CartesianActionSafetyProcessor requires scipy.")
def test_cartesian_safety_clips_large_absolute_target_through_bt_pipeline() -> None:
    pipeline = _build_safety_pipeline(mode="clip", max_translation_m=0.01, max_rotation_rad=0.1)
    action = _pose(x=0.03, rz=0.3)

    clipped_action = pipeline((action, _pose()))

    assert clipped_action["position.x"] == pytest.approx(0.01)
    assert clipped_action["position.y"] == pytest.approx(0.0)
    assert clipped_action["position.z"] == pytest.approx(0.0)
    assert clipped_action["orientation.z"] == pytest.approx(0.1)
    assert action["position.x"] == pytest.approx(0.03)
    assert action["orientation.z"] == pytest.approx(0.3)


def test_make_sandwich_executor_enables_cartesian_action_safety() -> None:
    cfg = yaml.safe_load(MAKE_SANDWICH_EXECUTOR_CONFIG.read_text())

    steps = cfg["robot_action_processor"]["steps"]
    safety_steps = [
        step
        for step in steps
        if isinstance(step, dict) and step.get("registry_name") == SAFETY_PROCESSOR_NAME
    ]

    assert len(safety_steps) == 1
    assert safety_steps[0]["config"] == {
        "max_translation_m": 0.015,
        "max_rotation_rad": 0.12,
        "mode": "error",
    }
