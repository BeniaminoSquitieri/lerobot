# Robot Runtime Code Map

Read this file first to know **what actually runs on the real robot** versus what
is support tooling, fake/smoke-test code, or offline evaluation. This is a study
and navigation aid. It does not change any behavior.

The safe runtime path is unchanged:

```
panda_live_viewer /lerobot_bt/generate_plan
  -> Linear IR JSON
  -> lerobot strict validation (strict_generated=True)
  -> XML/YAML generation
  -> BehaviorTree.CPP runner
  -> real Python skill server (server.py)
  -> real robot skills / VLM verifier
```

Study priority legend:

- **P0**: must study before robot day (real runtime path).
- **P1**: useful for operation/debug on robot day.
- **P2**: support/logging, not control.
- **P3**: fake/offline/evaluation only, ignore for runtime study.
- **Ignore**: tests/docs/generated outputs.

---

## Section 1: Real robot execution path

These run, or are directly consumed, during a real robot trial.

### Generation side (produces the BT that will execute)

| Category | File                                                                                                                                | Purpose                                                                                                                                                                     | Run on robot? | Study priority | Notes                     |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | -------------- | ------------------------- |
| A        | [src/lerobot_bt_python/bt_generation/generate_and_run.py](../src/lerobot_bt_python/bt_generation/generate_and_run.py)               | Generate BT once, then launch the C++ runner                                                                                                                                | Yes           | P0             | Robot-day entry point     |
| A        | [src/lerobot_bt_python/bt_generation/generate.py](../src/lerobot_bt_python/bt_generation/generate.py)                               | Orchestrates plan -> validate -> render -> log                                                                                                                              | Yes           | P0             | Core CLI                  |
| A        | [src/lerobot_bt_python/bt_generation/planner.py](../src/lerobot_bt_python/bt_generation/planner.py)                                 | Template-mode Linear IR builder and compatibility exports for the task contract; in ros-service mode, Linear IR comes from Panda and is validated against the same contract | Yes           | P0             | Re-exports task contracts |
| A        | [src/lerobot_bt_python/bt_generation/task_contracts.py](../src/lerobot_bt_python/bt_generation/task_contracts.py)                   | Loads/validates canonical task templates                                                                                                                                    | Yes           | P0             | Source of truth loader    |
| A        | [src/lerobot_bt_python/bt_generation/task_templates.yaml](../src/lerobot_bt_python/bt_generation/task_templates.yaml)               | Canonical task order data                                                                                                                                                   | Yes           | P0             | Repo-owned contract       |
| A        | [src/lerobot_bt_python/bt_generation/registry.py](../src/lerobot_bt_python/bt_generation/registry.py)                               | Typed capability registry load/validate                                                                                                                                     | Yes           | P0             | Capability boundary       |
| A        | [src/lerobot_bt_python/bt_generation/skills_registry.yaml](../src/lerobot_bt_python/bt_generation/skills_registry.yaml)             | Registered skills/gates/steps                                                                                                                                               | Yes           | P0             | Capability data           |
| A        | [src/lerobot_bt_python/bt_generation/validator.py](../src/lerobot_bt_python/bt_generation/validator.py)                             | Strict Linear IR validation                                                                                                                                                 | Yes           | P0             | Safety boundary           |
| A        | [src/lerobot_bt_python/bt_generation/vlm_planner.py](../src/lerobot_bt_python/bt_generation/vlm_planner.py)                         | Parse/canonicalize model Linear IR; reject XML/prose                                                                                                                        | Yes           | P0             | First ingestion guard     |
| A        | [src/lerobot_bt_python/bt_generation/export_planner_registry.py](../src/lerobot_bt_python/bt_generation/export_planner_registry.py) | Build constrained planner payload sent to Panda                                                                                                                             | Yes           | P0             | ros-service contract      |
| A        | [src/lerobot_bt_python/bt_generation/ros_plan_client.py](../src/lerobot_bt_python/bt_generation/ros_plan_client.py)                 | Call `/lerobot_bt/generate_plan`                                                                                                                                            | Yes           | P0             | ros-service planner       |
| A        | [src/lerobot_bt_python/bt_generation/renderer.py](../src/lerobot_bt_python/bt_generation/renderer.py)                               | Render BT.CPP XML + ROS2 params YAML                                                                                                                                        | Yes           | P0             | Robot-owned compile       |
| A        | [src/lerobot_bt_python/bt_generation/static_checks.py](../src/lerobot_bt_python/bt_generation/static_checks.py)                     | XML blackboard keys ⊆ generated YAML params                                                                                                                                 | Yes           | P0             | Pre-run guard             |
| A        | [src/lerobot_bt_python/bt_generation/manifest.py](../src/lerobot_bt_python/bt_generation/manifest.py)                               | SHA-256 + provenance manifest                                                                                                                                               | Yes           | P1             | Artifact traceability     |

### Execution side (runs the BT against the real robot)

| Category | File                                                                                                                | Purpose                                                | Run on robot? | Study priority | Notes                                                    |
| -------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------- | -------------- | -------------------------------------------------------- |
| A        | [src/lerobot_bt_runtime_cpp/](../src/lerobot_bt_runtime_cpp/)                                                       | BehaviorTree.CPP runner + nodes                        | Yes           | P0             | C++ runtime; do not change                               |
| A        | [src/lerobot_bt_interfaces/](../src/lerobot_bt_interfaces/)                                                         | `.srv` interface definitions                           | Yes           | P0             | Frozen contract                                          |
| A        | [src/lerobot_bt_python/server.py](../src/lerobot_bt_python/server.py)                                               | ROS2 skill-command server (real robot)                 | Yes           | P0             | Real skill server                                        |
| A        | [src/lerobot_bt_python/executor.py](../src/lerobot_bt_python/executor.py)                                           | Runs one learned skill end-to-end                      | Yes           | P0             | Policy + robot backend                                   |
| A        | [src/lerobot_bt_python/skill_runtime_loader.py](../src/lerobot_bt_python/skill_runtime_loader.py)                   | Loads policies / runtime feature metadata              | Yes           | P0             | Startup                                                  |
| A        | [src/lerobot_bt_python/config.py](../src/lerobot_bt_python/config.py)                                               | Executor YAML dataclasses                              | Yes           | P0             | Config schema                                            |
| A        | [src/lerobot_bt_python/processor_factory.py](../src/lerobot_bt_python/processor_factory.py)                         | Builds observation/action processor pipelines          | Yes           | P0             | Safety processors                                        |
| A        | [src/lerobot_bt_python/vlm/verification.py](../src/lerobot_bt_python/vlm/verification.py)                           | VLM/gate attempt state machine                         | Yes           | P0             | Verifier state                                           |
| A        | [src/lerobot_bt_python/vlm/protocol.py](../src/lerobot_bt_python/vlm/protocol.py)                                   | Verifier request/result JSON helpers                   | Yes           | P1             | Topic payloads                                           |
| A        | [src/lerobot_bt_python/perception/spatial_prior.py](../src/lerobot_bt_python/perception/spatial_prior.py)           | Spatial-prior OOD checker (Mahalanobis)                | Yes           | P1             | See [spatial_prior_gating.md](./spatial_prior_gating.md) |
| A        | [src/lerobot_bt_python/perception/spatial_prior_gate.py](../src/lerobot_bt_python/perception/spatial_prior_gate.py) | Runtime gate orchestrator (loads priors, queries pose) | Yes           | P1             | Shadow/enforce modes                                     |
| C        | [src/lerobot_bt_python/perception/fit_spatial_prior.py](../src/lerobot_bt_python/perception/fit_spatial_prior.py)   | Offline fitter: dataset → prior JSON                   | No            | P2             | Run once per skill                                       |
| A        | [src/lerobot_bt_python/perception/camera_publisher.py](../src/lerobot_bt_python/perception/camera_publisher.py)     | Publish robot camera frames for verifier               | Yes           | P1             | Perception bridge                                        |
| A        | [src/lerobot_bt_python/bt_interface_paths.py](../src/lerobot_bt_python/bt_interface_paths.py)                       | Resolve generated ROS2 bindings on `sys.path`          | Yes           | P1             | Import fix                                               |
| A        | [src/lerobot_bt_python/\*\_executor.yaml](../src/lerobot_bt_python/)                                                | Task-specific robot/camera/policy/skill config         | Yes           | P0             | One per task                                             |

---

## Section 2: Robot-day commands and files involved

| Step                    | Command                                                                                                         | Primary files                                                     |
| ----------------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Build/source            | `colcon build --symlink-install && source install/setup.bash`                                                   | `lerobot_bt_runtime_cpp`, `lerobot_bt_interfaces`                 |
| Preflight               | `python3 scripts/bt_preflight_check.py --task make_sandwich`                                                    | [scripts/bt_preflight_check.py](../scripts/bt_preflight_check.py) |
| Start skill server      | `uv run lerobot-bt-skill-server --config_path=src/lerobot_bt_python/make_sandwich_executor.yaml`                | `server.py`, `executor.py`, `config.py`                           |
| Dry-run generate        | `PYTHONPATH=src python3 -m lerobot_bt_python.bt_generation.generate_and_run --planner ros-service --no-run ...` | `generate_and_run.py`, `generate.py`, `ros_plan_client.py`        |
| Robot live              | `scripts/run_icra_runtime_bt_trial.sh make_sandwich robot_live`                                                 | `run_icra_runtime_bt_trial.sh`, `generate_and_run.py`, runner     |
| Annotate                | `python3 scripts/annotate_runtime_bt_trial.py ...`                                                              | `annotate_runtime_bt_trial.py`, `experiment_log.py`               |
| Summarize/report/bundle | `summarize_runtime_bt_experiments.py` / `make_icra_runtime_bt_report.py` / `bundle_runtime_bt_trial.py`         | support scripts                                                   |

---

## Section 3: Files to study first (P0)

1. [generate_and_run.py](../src/lerobot_bt_python/bt_generation/generate_and_run.py) — robot-day entry point.
2. [generate.py](../src/lerobot_bt_python/bt_generation/generate.py) — generation orchestration.
3. [validator.py](../src/lerobot_bt_python/bt_generation/validator.py) — strict safety boundary.
4. [renderer.py](../src/lerobot_bt_python/bt_generation/renderer.py) — XML/YAML compilation.
5. [registry.py](../src/lerobot_bt_python/bt_generation/registry.py) + [task_contracts.py](../src/lerobot_bt_python/bt_generation/task_contracts.py) — capability + ordering contract.
6. [ros_plan_client.py](../src/lerobot_bt_python/bt_generation/ros_plan_client.py) + [export_planner_registry.py](../src/lerobot_bt_python/bt_generation/export_planner_registry.py) — Panda planner bridge.
7. [server.py](../src/lerobot_bt_python/server.py) + [executor.py](../src/lerobot_bt_python/executor.py) — real skill execution.
8. The relevant `*_executor.yaml` for the task being run.

---

## Section 4: Support tools used during robot-day (P1/P2)

These help running, logging, and troubleshooting but never make control
decisions.

| Category | File                                                                                                              | Purpose                                         | Study priority |
| -------- | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | -------------- |
| B        | [src/lerobot_bt_python/bt_generation/experiment_log.py](../src/lerobot_bt_python/bt_generation/experiment_log.py) | Append-only generation/runner/annotation events | P2             |
| B        | [src/lerobot_bt_python/bt_generation/env_snapshot.py](../src/lerobot_bt_python/bt_generation/env_snapshot.py)     | Git/host/ROS provenance, fail-soft              | P2             |
| B        | [scripts/run_icra_runtime_bt_trial.sh](../scripts/run_icra_runtime_bt_trial.sh)                                   | Standardized trial wrapper                      | P1             |
| B        | [scripts/annotate_runtime_bt_trial.py](../scripts/annotate_runtime_bt_trial.py)                                   | Operator outcome annotation                     | P1             |
| B        | [scripts/summarize_runtime_bt_experiments.py](../scripts/summarize_runtime_bt_experiments.py)                     | Build trial/event/summary CSVs                  | P2             |
| B        | [scripts/bundle_runtime_bt_trial.py](../scripts/bundle_runtime_bt_trial.py)                                       | Archive trial artifacts                         | P2             |
| B        | [scripts/make_icra_runtime_bt_report.py](../scripts/make_icra_runtime_bt_report.py)                               | Render Markdown report from logs                | P2             |
| B        | [src/lerobot_bt_python/vlm/operator_console.py](../src/lerobot_bt_python/vlm/operator_console.py)                 | Terminal banners for verifier events            | P1             |
| B        | [src/lerobot_bt_python/groot2_monitor.py](../src/lerobot_bt_python/groot2_monitor.py)                             | Optional Groot2 visualization                   | P2             |

---

## Section 5: Fake/offline/evaluation files, safe to ignore for runtime study (P3)

These never run on the real robot. They are for non-robot smoke tests, offline
evaluation, or developer debug.

| Category | File                                                                                                                | Purpose                                  | Run on robot? | Study priority |
| -------- | ------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ------------- | -------------- |
| C        | [src/lerobot_bt_python/fakes/fake_bt_executor_server.py](../src/lerobot_bt_python/fakes/fake_bt_executor_server.py) | Fake skill server for smoke tests        | No            | P3             |
| C        | [scripts/test_generated_bt_with_fake_server.sh](../scripts/test_generated_bt_with_fake_server.sh)                   | Fake-executor smoke harness              | No            | P3             |
| C        | [scripts/check_generated_bt_offline.sh](../scripts/check_generated_bt_offline.sh)                                   | Offline generation smoke                 | No            | P3             |
| C        | [scripts/simulate_vlm_test.py](../scripts/simulate_vlm_test.py)                                                     | BT↔VLM comm debug                       | No            | P3             |
| C        | [scripts/comm_test.py](../scripts/comm_test.py)                                                                     | ROS network debug                        | No            | P3             |
| C        | [scripts/test_vlm_protocol.py](../scripts/test_vlm_protocol.py)                                                     | Protocol debug util                      | No            | P3             |
| C        | [scripts/legacy/](../scripts/legacy/)                                                                               | Quarantined legacy utilities             | No            | P3             |
| D        | [src/lerobot_bt_python/bt_generation/eval_ablation.py](../src/lerobot_bt_python/bt_generation/eval_ablation.py)     | Offline validator ablation for the paper | No            | P3             |
| Ignore   | [tests/lerobot_bt/](../tests/lerobot_bt/)                                                                           | Required tests, not runtime              | No            | Ignore         |
| Ignore   | [generated_bt/](../generated_bt/)                                                                                   | Generated outputs (gitignored)           | No            | Ignore         |

---

## Section 6: Dependency boundaries

- The generation side (`bt_generation/`) imports **no robot/policy/camera/torch
  code**. It only reads YAML, validates, and renders text artifacts.
- `tests/lerobot_bt/test_architecture_boundaries.py` enforces the package
  boundaries: no static task BT sources in the C++ runtime, no perception/VLM
  cross-imports, and no robot runtime imports at `bt_generation/` import time.
- The execution side (`server.py`, `executor.py`) owns hardware and policy. The
  C++ runner never imports policy/robot code; it talks to `server.py` via
  `RunNamedCommand` and VLM state services/topics only.
- `experiment_log.py` and `env_snapshot.py` are **observe-only**: they never
  change control decisions or BT semantics. `env_snapshot.py` fails soft.
- `eval_ablation.py` runs the **same** strict validator without weakening it; it
  only classifies errors post-hoc. It is import-only by offline/paper tooling.
- `fakes/fake_bt_executor_server.py` deliberately avoids robot/policy/camera/VLM
  imports and must never be used as the real skill server.

---

## Section 7: Common PI questions about production vs test

- **What actually runs on the robot?** Section 1 (Category A). Generation side
  produces the BT; execution side runs it via `server.py`/`executor.py` and the
  C++ runner.
- **Is the fake executor part of the robot path?** No. It is P3 smoke-test only
  and avoids all hardware imports.
- **Does logging affect control?** No. `experiment_log.py`/`env_snapshot.py` are
  observe-only and fail soft.
- **Is `eval_ablation.py` ever on the robot?** No. It is offline-only and does
  not modify the validator.
- **Are tests part of runtime?** No. They are required for confidence but never
  execute on the robot.
- **What is the single safety boundary?** `validator.py` with
  `strict_generated=True`, backed by `registry.py` and the canonical
  `task_templates.yaml` ordering contract.
