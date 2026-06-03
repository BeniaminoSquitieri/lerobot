"""@file fit_spatial_prior.py
@brief Offline fitter that turns a LeRobot dataset into a spatial-prior JSON.

This is the offline half of the spatial-prior gating feature. It reads a
demonstration dataset, extracts a position sample per episode at the grasp
instant, fits a 3D Gaussian N(mu, Sigma), and writes a prior JSON consumed at
runtime by `spatial_prior.SpatialPrior` and the BT server gate.

Why the grasp instant?
The LeRobot datasets used here store the end-effector Cartesian pose plus a
gripper opening value in `observation.state`
(`[x, y, z, ox, oy, oz, gripper]`). The frame where the gripper transitions
from open to closed is the moment the end-effector is at the object, so the EE
position there is the best available PROXY for the object position. The dataset
contains no explicit 6D object pose label, which is why we use this proxy.

This script intentionally reads the parquet data files directly (pandas +
pyarrow) instead of going through `LeRobotDataset`, so it does not pull video
frames or require torch. It only needs the small per-frame state vectors.

Usage:
    python3 -m lerobot_bt_python.fit_spatial_prior \\
        --dataset-repo-id Squitieri/put_coffee \\
        --skill pick_and_insert_capsule \\
        --object coffee_capsule \\
        --output src/lerobot_bt_python/spatial_priors/put_coffee.json

The frame_id defaults to "base_link" and MUST match the perception node's
`target_frame_id`. The two positions are only comparable when expressed in the
same physical base frame.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .spatial_prior import SpatialPrior, chi_square_threshold

# Default index of the gripper opening value inside observation.state for the
# custom_manipulator datasets: [x, y, z, ox, oy, oz, gripper].
DEFAULT_GRIPPER_INDEX = 6
# Indices of the translation (x, y, z) inside observation.state.
TRANSLATION_INDICES = (0, 1, 2)


def _resolve_dataset_dir(dataset_repo_id: str, local_root: str | None, download: bool) -> Path:
    """@brief Resolve a local directory holding the dataset parquet + meta.

    @param dataset_repo_id Hugging Face dataset id, e.g. "Squitieri/put_coffee".
    @param local_root Optional path to an already-downloaded dataset snapshot.
    @param download When True and no local_root is given, fetch parquet + meta
        (NOT videos) via huggingface_hub snapshot_download.
    @return Path to a directory containing meta/info.json and data/chunk-*/.
    """
    if local_root:
        root = Path(local_root).expanduser()
        if not (root / "meta" / "info.json").exists():
            raise FileNotFoundError(
                f"--dataset-root {root} does not contain meta/info.json."
            )
        return root

    if not download:
        raise ValueError(
            "No --dataset-root provided and --no-download set. Either point to a "
            "local snapshot or allow downloading."
        )

    from huggingface_hub import snapshot_download  # local import keeps deps optional

    snapshot = snapshot_download(
        dataset_repo_id,
        repo_type="dataset",
        # Pull only the small state parquet + metadata, never the videos.
        allow_patterns=["data/**", "meta/**", "*.json", "*.parquet"],
    )
    return Path(snapshot)


def _load_state_frames(dataset_dir: Path):
    """@brief Load all data parquet files concatenated into a single DataFrame.

    @param dataset_dir Directory containing data/chunk-*/file-*.parquet.
    @return A pandas DataFrame with at least observation.state, episode_index,
        and frame_index columns.
    """
    import pandas as pd  # local import keeps deps optional

    files = sorted(glob.glob(str(dataset_dir / "data" / "chunk-*" / "file-*.parquet")))
    if not files:
        raise FileNotFoundError(f"No data parquet files found under {dataset_dir / 'data'}.")
    frames = [pd.read_parquet(f) for f in files]
    df = pd.concat(frames, ignore_index=True)
    for column in ("observation.state", "episode_index", "frame_index"):
        if column not in df.columns:
            raise KeyError(
                f"Dataset is missing required column '{column}'. Found: {list(df.columns)}."
            )
    return df


def extract_grasp_positions(
    df,
    *,
    gripper_index: int = DEFAULT_GRIPPER_INDEX,
    closed_fraction: float = 0.5,
) -> tuple[np.ndarray, list[int]]:
    """@brief Extract one grasp-instant EE position per episode.

    For each episode the grasp instant is the first frame where the gripper
    opening drops to at most `open - closed_fraction * (open - min)`, i.e. the
    first sustained closing event. If the gripper never closes, the episode's
    minimum-opening frame is used as a conservative fallback.

    @param df DataFrame with observation.state, episode_index, frame_index.
    @param gripper_index Column index of the gripper opening in the state vector.
    @param closed_fraction Fraction of the open->min span that counts as closed.
    @return (positions Nx3 array, episode_index list aligned with positions).
    """
    if not 0.0 < closed_fraction < 1.0:
        raise ValueError("closed_fraction must be in the open interval (0, 1).")

    positions: list[np.ndarray] = []
    episodes: list[int] = []
    for episode_index in sorted(df["episode_index"].unique()):
        episode = df[df["episode_index"] == episode_index].sort_values("frame_index")
        state = np.stack(episode["observation.state"].to_numpy())
        if state.ndim != 2 or state.shape[1] <= max(gripper_index, *TRANSLATION_INDICES):
            raise ValueError(
                f"Episode {episode_index} state has unexpected shape {state.shape}."
            )
        gripper = state[:, gripper_index]
        gripper_open = float(gripper[0])
        gripper_min = float(gripper.min())
        if gripper_open <= gripper_min:
            # Gripper never closed during the episode; fall back to the minimum.
            grasp_idx = int(np.argmin(gripper))
        else:
            threshold = gripper_open - closed_fraction * (gripper_open - gripper_min)
            below = np.where(gripper <= threshold)[0]
            grasp_idx = int(below[0]) if below.size else int(np.argmin(gripper))
        positions.append(state[grasp_idx, list(TRANSLATION_INDICES)])
        episodes.append(int(episode_index))

    return np.asarray(positions, dtype=float), episodes


def fit_gaussian(positions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """@brief Fit a 3D Gaussian to grasp positions.

    Uses the unbiased sample covariance (ddof=1). Requires at least 2 samples.

    @param positions Nx3 array of grasp positions.
    @return (mu 3-vector, sigma 3x3 covariance).
    """
    positions = np.asarray(positions, dtype=float)
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError(f"positions must be Nx3, got shape {positions.shape}.")
    if positions.shape[0] < 2:
        raise ValueError("Need at least 2 demonstrations to estimate a covariance.")
    mu = positions.mean(axis=0)
    sigma = np.cov(positions.T, ddof=1)
    return mu, sigma


def leave_one_out_pass_rate(
    positions: np.ndarray,
    *,
    threshold: float,
    sigma_regularization_m2: float,
) -> float:
    """@brief Sanity check: fraction of held-out demos accepted by the gate.

    For each demo we refit the Gaussian on the remaining demos and check whether
    the held-out demo's Mahalanobis distance is within `threshold`. A healthy,
    unimodal prior should accept close to `confidence_level` of its own demos.

    @param positions Nx3 grasp positions.
    @param threshold Mahalanobis acceptance threshold.
    @param sigma_regularization_m2 Covariance regularization used at runtime.
    @return Fraction in [0, 1] of held-out demos that PASS.
    """
    positions = np.asarray(positions, dtype=float)
    n = positions.shape[0]
    if n < 3:
        return float("nan")
    passes = 0
    for i in range(n):
        rest = np.delete(positions, i, axis=0)
        mu = rest.mean(axis=0)
        sigma = np.cov(rest.T, ddof=1) + np.eye(3) * sigma_regularization_m2
        delta = positions[i] - mu
        distance = float(np.sqrt(max(delta @ np.linalg.inv(sigma) @ delta, 0.0)))
        if distance <= threshold:
            passes += 1
    return passes / n


def build_parser() -> argparse.ArgumentParser:
    """@brief Build the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Fit a spatial-prior JSON from a LeRobot dataset.")
    parser.add_argument("--dataset-repo-id", required=True, help="HF dataset id, e.g. Squitieri/put_coffee.")
    parser.add_argument("--skill", required=True, help="BT skill name the prior gates.")
    parser.add_argument("--object", default="", help="Canonical object name the prior describes.")
    parser.add_argument("--output", required=True, help="Output JSON path for the prior.")
    parser.add_argument("--dataset-root", default=None, help="Local dataset snapshot dir (skips download).")
    parser.add_argument("--no-download", action="store_true", help="Forbid downloading; require --dataset-root.")
    parser.add_argument("--frame-id", default="base_link", help="Robot base frame the positions live in.")
    parser.add_argument("--confidence-level", type=float, default=0.99, help="Chi-square acceptance level.")
    parser.add_argument("--closed-fraction", type=float, default=0.5, help="Gripper open->min fraction for grasp.")
    parser.add_argument("--gripper-index", type=int, default=DEFAULT_GRIPPER_INDEX, help="Gripper col in state.")
    parser.add_argument("--min-pose-confidence", type=float, default=0.0, help="Runtime min perception confidence.")
    parser.add_argument("--sigma-regularization", type=float, default=1e-6, help="Isotropic covariance floor (m^2).")
    return parser


def main(argv: list[str] | None = None) -> int:
    """@brief CLI entry point. Returns a process exit code."""
    args = build_parser().parse_args(argv)

    dataset_dir = _resolve_dataset_dir(
        args.dataset_repo_id, args.dataset_root, download=not args.no_download
    )
    info = json.loads((dataset_dir / "meta" / "info.json").read_text(encoding="utf-8"))
    df = _load_state_frames(dataset_dir)
    positions, episodes = extract_grasp_positions(
        df, gripper_index=args.gripper_index, closed_fraction=args.closed_fraction
    )
    mu, sigma = fit_gaussian(positions)
    threshold = chi_square_threshold(args.confidence_level, dof=3)
    pass_rate = leave_one_out_pass_rate(
        positions, threshold=threshold, sigma_regularization_m2=args.sigma_regularization
    )

    prior = SpatialPrior(
        skill=args.skill,
        object_name=args.object,
        frame_id=args.frame_id,
        mu=mu,
        sigma=sigma,
        n_demos=len(episodes),
        mahalanobis_threshold=threshold,
        source_dataset=args.dataset_repo_id,
        proxy="grasp_ee_position",
        min_pose_confidence=args.min_pose_confidence,
        sigma_regularization_m2=args.sigma_regularization,
        confidence_level=args.confidence_level,
        notes=(
            "mu/sigma are fitted from the end-effector position at the grasp instant, "
            "a PROXY for the object position. Expect a fixed grasp offset relative to a "
            "perception object centroid; calibrate in SHADOW mode before enforcing."
        ),
        metadata={
            "generator": "fit_spatial_prior.py",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "dataset_fps": info.get("fps"),
            "dataset_total_episodes": info.get("total_episodes"),
            "closed_fraction": args.closed_fraction,
            "gripper_index": args.gripper_index,
            "translation_std_m": [float(v) for v in positions.std(axis=0)],
            "leave_one_out_pass_rate": None if np.isnan(pass_rate) else round(float(pass_rate), 4),
        },
    )
    prior.save(args.output)

    print(f"Fitted spatial prior for skill '{args.skill}' from {args.dataset_repo_id}")
    print(f"  demos      : {len(episodes)}")
    print(f"  mu (m)     : {np.round(mu, 4).tolist()}")
    print(f"  std (m)    : {np.round(positions.std(axis=0), 4).tolist()}")
    print(f"  threshold  : {threshold:.4f} (Mahalanobis, level={args.confidence_level})")
    if not np.isnan(pass_rate):
        print(f"  LOO accept : {pass_rate:.2%} of held-out demos PASS (expected ~{args.confidence_level:.0%})")
    print(f"  frame_id   : {args.frame_id}")
    print(f"  written to : {args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
