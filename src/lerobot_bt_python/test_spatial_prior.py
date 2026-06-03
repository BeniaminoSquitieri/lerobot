"""@file test_spatial_prior.py
@brief Unit tests for the spatial-prior OOD gate (checker, fitter, orchestrator).

These tests use only numpy and the standard library so they run without ROS2,
torch, or robot hardware.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from lerobot_bt_python.config import SpatialPriorGateConfig
from lerobot_bt_python.fit_spatial_prior import (
    extract_grasp_positions,
    fit_gaussian,
    leave_one_out_pass_rate,
)
from lerobot_bt_python.spatial_prior import (
    ABSTAIN,
    FAIL,
    PASS,
    SpatialPrior,
    chi_square_threshold,
)
from lerobot_bt_python.spatial_prior_gate import (
    ObservedPose,
    SpatialPriorGate,
    parse_object_pose_json,
)

PACKAGE_DIR = Path(__file__).resolve().parent
BUNDLED_PRIOR = PACKAGE_DIR / "spatial_priors" / "put_coffee.json"


def _make_prior(**overrides) -> SpatialPrior:
    """@brief Build a small, well-conditioned prior for tests."""
    params = dict(
        skill="pick",
        object_name="cup",
        frame_id="base_link",
        mu=[0.5, 0.0, 0.2],
        sigma=np.diag([0.0009, 0.0009, 0.0001]),
        n_demos=40,
        mahalanobis_threshold=chi_square_threshold(0.99, dof=3),
    )
    params.update(overrides)
    return SpatialPrior(**params)


# --------------------------------------------------------------------------- #
# SpatialPrior checker
# --------------------------------------------------------------------------- #


def test_mahalanobis_distance_at_mean_is_zero():
    prior = _make_prior()
    assert prior.mahalanobis_distance(prior.mu) == pytest.approx(0.0, abs=1e-9)


def test_pass_for_in_distribution_point():
    prior = _make_prior()
    verdict = prior.evaluate(observed_translation=[0.5, 0.0, 0.2], frame_id="base_link")
    assert verdict.status == PASS
    assert verdict.distance == pytest.approx(0.0, abs=1e-9)
    assert not verdict.blocks


def test_fail_for_far_out_of_distribution_point():
    prior = _make_prior()
    verdict = prior.evaluate(observed_translation=[1.5, 1.5, 1.5], frame_id="base_link")
    assert verdict.status == FAIL
    assert verdict.distance > verdict.threshold
    assert verdict.blocks


def test_abstain_on_frame_mismatch():
    prior = _make_prior()
    verdict = prior.evaluate(observed_translation=[0.5, 0.0, 0.2], frame_id="camera_color_optical_frame")
    assert verdict.status == ABSTAIN
    assert "frame_mismatch" in verdict.reason
    assert not verdict.blocks


def test_abstain_on_missing_pose():
    prior = _make_prior()
    verdict = prior.evaluate(observed_translation=None, frame_id="base_link")
    assert verdict.status == ABSTAIN
    assert verdict.reason == "no_observed_pose"


def test_abstain_on_low_confidence():
    prior = _make_prior(min_pose_confidence=0.5)
    verdict = prior.evaluate(
        observed_translation=[0.5, 0.0, 0.2], frame_id="base_link", pose_confidence=0.1
    )
    assert verdict.status == ABSTAIN
    assert "low_pose_confidence" in verdict.reason


def test_abstain_on_invalid_pose_values():
    prior = _make_prior()
    verdict = prior.evaluate(observed_translation=[float("nan"), 0.0, 0.2], frame_id="base_link")
    assert verdict.status == ABSTAIN
    assert verdict.reason == "invalid_observed_pose"


def test_none_frame_id_is_accepted():
    # When perception does not report a frame, we do not reject on frame; the
    # decision proceeds (the operator is responsible for consistent frames).
    prior = _make_prior()
    verdict = prior.evaluate(observed_translation=[0.5, 0.0, 0.2], frame_id=None)
    assert verdict.status == PASS


def test_near_singular_covariance_is_regularized():
    # A flat z-axis (zero variance) must not break inversion.
    prior = _make_prior(sigma=np.diag([0.0009, 0.0009, 0.0]))
    verdict = prior.evaluate(observed_translation=[0.5, 0.0, 0.2], frame_id="base_link")
    assert verdict.status == PASS


def test_invalid_mu_shape_raises():
    with pytest.raises(ValueError):
        _make_prior(mu=[0.0, 0.0])


def test_roundtrip_save_load(tmp_path):
    prior = _make_prior(notes="roundtrip")
    path = tmp_path / "prior.json"
    prior.save(path)
    loaded = SpatialPrior.load(path)
    assert loaded.skill == prior.skill
    assert loaded.frame_id == prior.frame_id
    assert np.allclose(loaded.mu, prior.mu)
    assert np.allclose(loaded.sigma, prior.sigma)
    assert loaded.mahalanobis_threshold == pytest.approx(prior.mahalanobis_threshold)


def test_from_dict_rejects_wrong_schema_version():
    with pytest.raises(ValueError):
        SpatialPrior.from_dict({"schema_version": 999, "skill": "x", "frame_id": "b",
                                "mu": [0, 0, 0], "sigma": np.eye(3).tolist(),
                                "n_demos": 2, "mahalanobis_threshold": 1.0})


def test_chi_square_threshold_known_value():
    # sqrt(chi2.ppf(0.99, 3)) ~= 3.3682
    assert chi_square_threshold(0.99, dof=3) == pytest.approx(3.3682, abs=1e-3)


# --------------------------------------------------------------------------- #
# Bundled put_coffee prior
# --------------------------------------------------------------------------- #


def test_bundled_put_coffee_prior_loads_and_accepts_mean():
    assert BUNDLED_PRIOR.exists(), "put_coffee prior must be generated and committed"
    prior = SpatialPrior.load(BUNDLED_PRIOR)
    assert prior.skill == "pick_and_insert_capsule"
    assert prior.frame_id == "base_link"
    assert prior.n_demos == 50
    verdict = prior.evaluate(observed_translation=prior.mu.tolist(), frame_id="base_link")
    assert verdict.status == PASS


# --------------------------------------------------------------------------- #
# Offline fitter
# --------------------------------------------------------------------------- #


def _fake_dataframe(positions_by_episode):
    """@brief Build a minimal DataFrame mimicking the dataset parquet schema."""
    import pandas as pd

    rows = []
    for episode_index, (approach, grasp_xyz) in enumerate(positions_by_episode):
        # Two open frames, then a closing frame at the grasp position. The state
        # vector mirrors the real schema: [x, y, z, ox, oy, oz, gripper].
        rows.append({"observation.state": np.array(approach + [0.0, 0.0, 0.0, 0.085]),
                     "episode_index": episode_index, "frame_index": 0})
        rows.append({"observation.state": np.array(grasp_xyz + [0.0, 0.0, 0.0, 0.01]),
                     "episode_index": episode_index, "frame_index": 1})
    return pd.DataFrame(rows)


def test_extract_grasp_positions_picks_closing_frame():
    df = _fake_dataframe([
        ([0.0, 0.0, 0.5], [0.5, -0.2, 0.1]),
        ([0.0, 0.0, 0.5], [0.52, -0.18, 0.11]),
    ])
    positions, episodes = extract_grasp_positions(df)
    assert episodes == [0, 1]
    assert np.allclose(positions[0], [0.5, -0.2, 0.1])
    assert np.allclose(positions[1], [0.52, -0.18, 0.11])


def test_fit_gaussian_recovers_mean():
    rng = np.random.default_rng(0)
    samples = rng.normal(loc=[0.5, -0.2, 0.1], scale=[0.02, 0.02, 0.005], size=(200, 3))
    mu, sigma = fit_gaussian(samples)
    assert np.allclose(mu, [0.5, -0.2, 0.1], atol=0.01)
    assert sigma.shape == (3, 3)


def test_fit_gaussian_requires_two_samples():
    with pytest.raises(ValueError):
        fit_gaussian(np.array([[0.1, 0.2, 0.3]]))


def test_leave_one_out_pass_rate_high_for_tight_cluster():
    rng = np.random.default_rng(1)
    samples = rng.normal(loc=[0.5, -0.2, 0.1], scale=[0.02, 0.02, 0.005], size=(50, 3))
    rate = leave_one_out_pass_rate(samples, threshold=chi_square_threshold(0.99), sigma_regularization_m2=1e-6)
    assert rate > 0.9


# --------------------------------------------------------------------------- #
# Pose JSON parsing
# --------------------------------------------------------------------------- #


def test_parse_object_pose_json_extracts_fields():
    payload = json.dumps({
        "name": "cup",
        "present": True,
        "frame_id": "base_link",
        "pose": {"translation": [0.5, -0.2, 0.1], "quaternion_xyzw": [0, 0, 0, 1]},
        "pose_confidence": 0.8,
    })
    observed = parse_object_pose_json(payload)
    assert observed.error is None
    assert observed.frame_id == "base_link"
    assert observed.confidence == pytest.approx(0.8)
    assert np.allclose(observed.translation, [0.5, -0.2, 0.1])


def test_parse_object_pose_json_handles_missing_translation():
    observed = parse_object_pose_json(json.dumps({"frame_id": "base_link", "pose": {}}))
    assert observed.error == "no_translation"


def test_parse_object_pose_json_handles_invalid_json():
    observed = parse_object_pose_json("{not json")
    assert observed.error is not None and observed.error.startswith("invalid_json")


# --------------------------------------------------------------------------- #
# Gate orchestrator (modes)
# --------------------------------------------------------------------------- #


def _gate(mode: str) -> SpatialPriorGate:
    cfg = SpatialPriorGateConfig(
        mode=mode,
        priors_dir=str(BUNDLED_PRIOR.parent),
        skill_priors={"pick_and_insert_capsule": "put_coffee.json"},
        skill_objects={"pick_and_insert_capsule": "coffee_capsule"},
    )
    return SpatialPriorGate(cfg, package_dir=PACKAGE_DIR)


def test_gate_off_is_inert():
    cfg = SpatialPriorGateConfig(mode="off", skill_priors={"pick_and_insert_capsule": "put_coffee.json"})
    gate = SpatialPriorGate(cfg, package_dir=PACKAGE_DIR)
    assert not gate.enabled
    assert gate.evaluate("pick_and_insert_capsule", lambda name: ObservedPose()) is None


def test_gate_shadow_never_blocks_even_on_fail():
    gate = _gate("shadow")

    def far_pose(_name):
        return ObservedPose(translation=[2.0, 2.0, 2.0], frame_id="base_link", confidence=0.9)

    verdict = gate.evaluate("pick_and_insert_capsule", far_pose)
    assert verdict.status == FAIL
    assert gate.should_block(verdict) is False


def test_gate_enforce_blocks_on_fail():
    gate = _gate("enforce")

    def far_pose(_name):
        return ObservedPose(translation=[2.0, 2.0, 2.0], frame_id="base_link", confidence=0.9)

    verdict = gate.evaluate("pick_and_insert_capsule", far_pose)
    assert verdict.status == FAIL
    assert gate.should_block(verdict) is True


def test_gate_enforce_does_not_block_on_abstain():
    gate = _gate("enforce")

    def camera_frame_pose(_name):
        return ObservedPose(translation=[0.68, -0.26, 0.15], frame_id="camera_color_optical_frame")

    verdict = gate.evaluate("pick_and_insert_capsule", camera_frame_pose)
    assert verdict.status == ABSTAIN
    assert gate.should_block(verdict) is False


def test_gate_abstains_when_pose_provider_raises():
    gate = _gate("enforce")

    def boom(_name):
        raise RuntimeError("perception down")

    verdict = gate.evaluate("pick_and_insert_capsule", boom)
    assert verdict.status == ABSTAIN
    assert "pose_provider_error" in verdict.reason
    assert gate.should_block(verdict) is False


def test_gate_skips_ungated_skill():
    gate = _gate("enforce")
    assert gate.evaluate("some_other_skill", lambda name: ObservedPose()) is None
