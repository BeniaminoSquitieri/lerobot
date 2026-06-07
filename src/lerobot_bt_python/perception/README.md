# perception

This package contains perception-facing support code for the BT Python runtime.
It produces or consumes metric scene information, but it does not decide task
semantics.

| File                    | Responsibility                                                                                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `camera_publisher.py`   | Republishes already-open robot RGB-D camera streams, CameraInfo, and optional static TF for external perception/VLM consumers. |
| `spatial_prior.py`      | Pure-numpy spatial prior checker for metric out-of-distribution poses.                                                         |
| `spatial_prior_gate.py` | Runtime spatial-prior gate that parses perception pose JSON and evaluates configured priors.                                   |
| `fit_spatial_prior.py`  | Offline CLI that fits prior JSON files from LeRobot datasets.                                                                  |
| `spatial_priors/`       | Bundled fitted prior JSON artifacts.                                                                                           |

Boundary: perception may publish/read camera frames and object poses. It should
not parse VLM result payloads, own verifier statuses, or make semantic
task-completion decisions.
