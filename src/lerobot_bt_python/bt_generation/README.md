# bt_generation

This package builds and validates the Behavior Tree (BT) that the robot runs.
It contains **no robot, policy, camera, or torch imports**: it only reads YAML,
validates Linear IR, and renders text artifacts (XML + ROS2 params YAML).

See [../../../docs/robot_runtime_code_map.md](../../../docs/robot_runtime_code_map.md)
for the full study-priority map.

## Runtime generation (P0 — runs/produces what the robot executes)

| File | Purpose |
|---|---|
| `generate_and_run.py` | Robot-day entry point: generate then launch the C++ runner. |
| `generate.py` | Orchestrates plan -> validate -> render -> log. |
| `planner.py` | Builds deterministic Linear IR from the task contract. |
| `task_contracts.py` | Loads and strictly validates canonical task templates. |
| `task_templates.yaml` | Repo-owned canonical task ordering (source of truth). |
| `registry.py` | Typed capability registry load/validate. |
| `skills_registry.yaml` | Registered skills, gates, and human steps. |
| `validator.py` | Strict Linear IR validation (the safety boundary). |
| `vlm_planner.py` | Parses/canonicalizes model Linear IR; rejects XML/prose. |
| `export_planner_registry.py` | Builds the constrained payload sent to Panda. |
| `ros_plan_client.py` | Calls `/lerobot_bt/generate_plan`. |
| `renderer.py` | Renders BT.CPP XML and ROS2 params YAML. |
| `static_checks.py` | Verifies XML blackboard keys ⊆ generated YAML params. |
| `manifest.py` | SHA-256 + provenance manifest for generated artifacts. |

## Robot-day support (P2 — observe-only, never controls)

| File | Purpose |
|---|---|
| `experiment_log.py` | Append-only generation/runner/annotation event log. |
| `env_snapshot.py` | Git/host/ROS provenance for logs; fails soft. |

## Offline evaluation (P3 — never runs on the robot)

| File | Purpose |
|---|---|
| `eval_ablation.py` | Offline validator-ablation tool for the paper. Runs the same strict validator without weakening it; classifies errors post-hoc. |
