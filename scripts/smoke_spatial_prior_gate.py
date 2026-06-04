#!/usr/bin/env python3
"""Offline smoke test for the spatial-prior OOD gate (no ROS, no GPU, no robot).

It builds the real ``SpatialPriorGate`` from the bundled ``put_coffee.json``
prior and feeds three synthetic perception payloads to exercise every verdict:

  - PASS    : an in-distribution capsule pose in ``base_link`` near the prior mean.
  - FAIL    : a far, out-of-distribution capsule pose in ``base_link``.
  - ABSTAIN : a capsule pose still in the camera frame (no hand-eye calibration),
              which must NOT be trusted -> the gate abstains (frame_mismatch).

Each evaluation prints the gate's structured ``event=spatial_prior_gate`` log
line so the verdicts are greppable, e.g.::

    python3 scripts/smoke_spatial_prior_gate.py | grep event=spatial_prior_gate

The script runs in ``enforce`` mode to also report whether each verdict would
block the skill (only FAIL blocks; PASS and ABSTAIN never block). It exits 0
when the three verdicts match expectations, non-zero otherwise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent / "src" / "lerobot_bt_python"
sys.path.insert(0, str(PACKAGE_DIR.parent))

from lerobot_bt_python.config import SpatialPriorGateConfig  # noqa: E402
from lerobot_bt_python.spatial_prior import ABSTAIN, FAIL, PASS  # noqa: E402
from lerobot_bt_python.spatial_prior_gate import (  # noqa: E402
    SpatialPriorGate,
    parse_object_pose_json,
)

SKILL = "pick_and_insert_capsule"
PRIOR = PACKAGE_DIR / "spatial_priors" / "put_coffee.json"


class _StdoutLogger:
    """Minimal logger that prints the gate's greppable log lines."""

    def info(self, message: str) -> None:
        print(f"[INFO] {message}")

    def warning(self, message: str) -> None:
        print(f"[WARN] {message}")

    def error(self, message: str) -> None:
        print(f"[ERROR] {message}")


def _payload(frame_id: str, x: float, y: float, z: float, confidence: float = 0.9) -> str:
    return json.dumps(
        {
            "name": "coffee_capsule",
            "present": True,
            "frame_id": frame_id,
            "pose": {
                "translation": {"x": x, "y": y, "z": z},
                "quaternion_xyzw": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
            },
            "pose_confidence": confidence,
        }
    )


def _provider(frame_id: str, x: float, y: float, z: float):
    return lambda _name: parse_object_pose_json(_payload(frame_id, x, y, z))


def main() -> int:
    if not PRIOR.exists():
        print(f"[ERROR] missing prior: {PRIOR}", file=sys.stderr)
        return 2

    cfg = SpatialPriorGateConfig(
        mode="enforce",
        priors_dir=str(PRIOR.parent),
        skill_priors={SKILL: "put_coffee.json"},
        skill_objects={SKILL: "coffee_capsule"},
    )
    gate = SpatialPriorGate(cfg, package_dir=PACKAGE_DIR, logger=_StdoutLogger())

    # PASS: in-distribution pose in base_link, near the fitted mean.
    # FAIL: far out-of-distribution pose in base_link.
    # ABSTAIN: pose still expressed in the camera frame (no calibration).
    cases = [
        ("PASS", PASS, _provider("base_link", 0.684, -0.260, 0.150)),
        ("FAIL", FAIL, _provider("base_link", 1.50, 0.90, 0.80)),
        ("ABSTAIN", ABSTAIN, _provider("panda_front_camera", 0.02, -0.01, 0.70)),
    ]

    ok = True
    for label, expected, provider in cases:
        print(f"\n=== expecting {label} ===")
        verdict = gate.evaluate(SKILL, provider)
        blocks = gate.should_block(verdict)
        status = verdict.status if verdict is not None else None
        print(f"--> status={status} blocks={blocks}")
        if status != expected:
            print(f"[ERROR] expected {expected}, got {status}")
            ok = False
        if label == "FAIL" and not blocks:
            print("[ERROR] FAIL must block in enforce mode")
            ok = False
        if label in ("PASS", "ABSTAIN") and blocks:
            print(f"[ERROR] {label} must never block")
            ok = False

    print("\nSMOKE TEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
