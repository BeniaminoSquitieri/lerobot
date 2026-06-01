# Runtime BT Generation Robot Runbook

## 0. Goal

This runbook tests the runtime BT generation path in robot-day order.
`panda_live_viewer` exposes camera/VLM planner service input and returns Linear
IR JSON only. `lerobot` validates that Linear IR, writes XML/YAML/manifest
artifacts, and starts the BehaviorTree.CPP runner. The runner ticks generated
`DoSkill` and `AwaitScene` leaves. During execution, the skill server bridges
robot skills and VLM verifier request/result topics.

Dry-run and offline checks are implemented; real robot validation still must be
performed.

## 1. Golden rule

Dry-run first. Live VLM planner last.

**STOP if dry-run ROS service or `--no-run` generation fails. Do not start live
VLM planning yet.**

## 2. Repository branches

```bash
cd ~/lerobot
git checkout runtime-bt-generation-mvp-c
git pull

cd ~/panda_live_viewer
git checkout after_lorenzo_meeting
git pull
```

## 3. Build and source lerobot workspace

```bash
cd ~/lerobot
source /opt/ros/$ROS_DISTRO/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Expected:

- no `colcon build` error
- `ros2` can find `lerobot_bt_interfaces`

Quick check:

```bash
ros2 interface show lerobot_bt_interfaces/srv/GenerateTaskPlan
```

**STOP if this fails.** Fix ROS sourcing or rebuild before starting Panda.

## 4. Terminal layout

| Terminal | Repo | Purpose | Must stay running? |
|---|---|---|---|
| T0 | `~/lerobot` | Build/source workspace once | No |
| T1 | `~/panda_live_viewer` | Panda dry-run planner service | Yes |
| T2 | any sourced shell | ROS service checks | No |
| T3 | `~/lerobot` | Generate artifacts with `--no-run` | No |
| T4 | `~/lerobot` | Skill server | Yes |
| T5 | `~/lerobot` | Generate and run BehaviorTree.CPP | Until test ends |
| T6 | `~/panda_live_viewer` | Optional live VLM planner after dry-run works | Yes |

## 5. Start panda_live_viewer in dry-run service mode

```bash
cd ~/panda_live_viewer
source /opt/ros/$ROS_DISTRO/setup.bash
source ~/lerobot/install/setup.bash

python3 -m vlm_live.cli \
  --ros-args \
  -p planner_dry_run:=true \
  -p lazy_load_model:=true \
  -p require_generate_plan_service:=true
```

In this mode Panda must not load Qwen or touch the GPU. It should create
`/lerobot_bt/generate_plan` and answer using `canonical_task_sequence` from the
planner registry payload.

If startup fails on `GenerateTaskPlan`, the `lerobot` ROS workspace is not
sourced correctly in this terminal.

**STOP if this fails.**

## 6. Check ROS service

```bash
ros2 service list | grep /lerobot_bt/generate_plan
ros2 service type /lerobot_bt/generate_plan
```

Expected:

```text
lerobot_bt_interfaces/srv/GenerateTaskPlan
```

STOP conditions:

- service missing
- wrong service type
- `GenerateTaskPlan` import error

Fix:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
source ~/lerobot/install/setup.bash
cd ~/lerobot
colcon build --symlink-install
source install/setup.bash
```

## 7. Generate BT through ROS service, no runner

```bash
cd ~/lerobot
source /opt/ros/$ROS_DISTRO/setup.bash
source install/setup.bash

PYTHONPATH=src python3 -m lerobot_bt_python.bt_generation.generate_and_run \
  --task make_sandwich \
  --planner ros-service \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --output-dir generated_bt \
  --no-run
```

Expected files:

```text
generated_bt/plans/make_sandwich_linear_ir.json
generated_bt/raw_model_responses/make_sandwich_raw_response.json
generated_bt/trees/make_sandwich.xml
generated_bt/config/make_sandwich_bt.yaml
generated_bt/manifests/make_sandwich_manifest.json
```

Expected meaning:

- Panda service answered.
- `lerobot` parsed Linear IR.
- strict validation passed.
- XML/YAML rendered.
- manifest written.
- runner command printed but not executed.

**STOP if this fails.** Do not start the skill server or live VLM planner yet.

## 8. Inspect artifacts quickly

```bash
cat generated_bt/plans/make_sandwich_linear_ir.json
cat generated_bt/manifests/make_sandwich_manifest.json
ls -lh generated_bt/trees generated_bt/config generated_bt/manifests
```

Look for:

- `task_name` is `make_sandwich`
- canonical step order is unchanged
- manifest hashes are present
- no XML in raw plan response; XML should exist only in `generated_bt/trees`

## 9. Start skill server

```bash
cd ~/lerobot
source /opt/ros/$ROS_DISTRO/setup.bash
source install/setup.bash

uv run lerobot-bt-skill-server \
  --config_path=src/lerobot_bt_python/make_sandwich_executor.yaml
```

This terminal must stay running. The skill server owns robot skills, policy
execution, camera publishing, and the VLM verification request/result bridge.

If `uv` is not available, use the project-supported `uv` command after
installing or activating the project environment. Do not guess a Python module
entrypoint on robot day.

**STOP if the skill server does not start or does not respond.**

## 10. Run generated BT

```bash
cd ~/lerobot
source /opt/ros/$ROS_DISTRO/setup.bash
source install/setup.bash

PYTHONPATH=src python3 -m lerobot_bt_python.bt_generation.generate_and_run \
  --task make_sandwich \
  --planner ros-service \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --output-dir generated_bt
```

Expected:

- it regenerates artifacts
- it prints generated plan/tree/config/manifest
- it starts `ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner`
- the BT ticks `AwaitScene` and `DoSkill`

## 11. Only after dry-run works: live VLM planner

Restart Panda with live planning only after service dry-run, no-run generation,
skill server, and runner have passed.

```bash
cd ~/panda_live_viewer
source /opt/ros/$ROS_DISTRO/setup.bash
source ~/lerobot/install/setup.bash

python3 -m vlm_live.cli \
  --ros-args \
  -p planner_dry_run:=false \
  -p lazy_load_model:=true \
  -p require_generate_plan_service:=true
```

This may load Qwen/GPU when the first VLM call needs the model. Camera streams
must be available. If this fails, debug model, camera, or viewer setup before
debugging `lerobot`.

**STOP if live planning returns prose, XML, empty `plan_json`, or invalid JSON.**

## 12. Troubleshooting table

| Symptom | Likely cause | Check | Fix |
|---|---|---|---|
| `/lerobot_bt/generate_plan` missing | Panda node not running or wrong sourcing | `ros2 service list` | Start T1 with ROS and `~/lerobot/install/setup.bash` sourced |
| service type unavailable | Interface package not built/sourced | `ros2 interface show lerobot_bt_interfaces/srv/GenerateTaskPlan` | Rebuild `~/lerobot`, source `install/setup.bash` |
| `ros2` command not found | ROS environment not sourced | `which ros2` | `source /opt/ros/$ROS_DISTRO/setup.bash` |
| `generate_and_run` says service unavailable | Panda service missing or wrong terminal setup | Repeat Section 6 | Restart dry-run service and re-source |
| `plan_json` empty | Panda service failed to build response | Check Panda logs | Keep dry-run on; fix registry payload/service error |
| planner response not valid JSON | Live VLM returned prose or fences | Inspect `generated_bt/raw_model_responses/...` | Stay in dry-run or tighten VLM prompt/service before robot run |
| strict validation canonical sequence mismatch | Planner reordered, skipped, or invented steps | Inspect Linear IR `steps` | Do not run; fix planner output |
| generated XML references missing YAML key | Renderer/static config mismatch | Run `python3 -m lerobot_bt_python.bt_generation.static_checks` | Fix generated artifacts before runner |
| runner command not found | Runtime package not built/sourced | `ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner --help` | Rebuild and source workspace |
| skill server not responding | T4 not running or wrong config | Check `/lerobot_bt/run` and server logs | Restart skill server with make_sandwich executor YAML |
| VLM says `WAIT_HUMAN` but `lerobot` only accepts `RUNNING`/`SUCCESS`/`FAILURE` | Current runtime does not support `WAIT_HUMAN` end-to-end | Inspect `allowed_statuses` in VLM request | Panda maps it to `RUNNING` unless explicitly allowed |
| missing camera streams | Camera publisher/viewer not connected | Panda logs, ROS image topics | Fix camera pipeline before live VLM planner |
| Qwen model path wrong | Model path or GPU environment issue | Panda model-load logs | Fix Panda model config; do not debug `lerobot` first |

## 13. Task variants

Generate `make_coffee` through the dry-run ROS service without running the BT:

```bash
cd ~/lerobot
source /opt/ros/$ROS_DISTRO/setup.bash
source install/setup.bash

PYTHONPATH=src python3 -m lerobot_bt_python.bt_generation.generate_and_run \
  --task make_coffee \
  --planner ros-service \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_coffee_executor.yaml \
  --output-dir generated_bt \
  --no-run
```

Run `make_coffee` after its no-run artifacts pass:

```bash
PYTHONPATH=src python3 -m lerobot_bt_python.bt_generation.generate_and_run \
  --task make_coffee \
  --planner ros-service \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_coffee_executor.yaml \
  --output-dir generated_bt
```

## 14. What not to test first

- do not start with `planner_dry_run:=false`
- do not test live VLM planner before service dry-run passes
- do not modify registry on robot day unless necessary
- do not debug model issues before ROS service contract passes
- do not enable future `allowed_variants`, skips, or replanning
