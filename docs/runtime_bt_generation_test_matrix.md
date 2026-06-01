# Runtime BT Generation Test Matrix

This matrix isolates the runtime BehaviorTree generation path into four failure
domains:

- **Planner contract**: `lerobot` accepts only Linear IR JSON with registered
  `kind`/`name` pairs and the canonical task order.
- **VLM live planner**: `panda_live_viewer` returns the ROS service response
  `plan_json`; it must be JSON only, with no XML or prose.
- **BehaviorTree.CPP runner**: generated XML/YAML are handed to
  `lerobot_bt_runner`.
- **Skill server / verifier**: Python skill execution and VLM verification used
  while the BT is ticking.

Run commands from the `lerobot` repository root unless stated otherwise.

## Common Setup

```bash
cd /home/bsquitieri/lerobot
git switch runtime-bt-generation-mvp-c
export PYTHONPATH=src:${PYTHONPATH:-}
```

For ROS tests, source ROS and the built workspace first:

```bash
source /opt/ros/<distro>/setup.bash
source install/setup.bash
```

Use the matching `panda_live_viewer` branch for live service tests:

```bash
cd /home/bsquitieri/panda_live_viewer
git switch after_lorenzo_meeting
```

If your checkout is nested under `lerobot/panda_live_viewer`, use that path
instead.

## Known Contract Checks Before Robot

Run these checks before moving from laptop/service tests to any robot execution:

- `registry_contract_hash` is stable and excludes derived hash fields; its
  schema-version semantics are covered by
  `tests/lerobot_bt/test_export_planner_registry.py`.
- `panda_live_viewer` rejects extra Linear IR step fields such as `confidence`
  or `reason`; only `kind`, `name`, `object`, and `objects` are accepted before
  `lerobot` performs final validation.
- `WAIT_HUMAN` support is not present in current `lerobot`
  `GetSkillVerification` runtime: the Python verifier and C++ polling node use
  `RUNNING`, `SUCCESS`, and `FAILURE`. Panda may publish `WAIT_HUMAN` only if
  the request explicitly includes it in `allowed_statuses`; otherwise it maps
  the verdict to `RUNNING` and prefixes the message with `WAIT_HUMAN: `.
- The Panda dry-run planning service is tested without model load:
  `build_generate_plan_response(..., dry_run=True)` must not call the VLM
  backend, and `lazy_load_model=True` must not call `load_model` in node init.
- `generate_and_run --planner ros-service --no-run` must produce plan, tree,
  config, and manifest artifacts.

## Test A - Offline LeRobot Template

Purpose: validates deterministic `lerobot` template planning, rendering,
manifest generation, and static XML/YAML blackboard keys. This does not touch
ROS, `panda_live_viewer`, a VLM, the C++ runner, or the skill server.

```bash
PYTHONPATH=src python -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --planner template \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --output-dir generated_bt

PYTHONPATH=src python -m lerobot_bt_python.bt_generation.static_checks \
  --xml generated_bt/trees/make_sandwich.xml \
  --yaml generated_bt/config/make_sandwich_bt.yaml
```

Expected:

```text
task_name: make_sandwich
robot_skill: 2
human_step: 1
vlm_gate: 4
wrote tree: generated_bt/trees/make_sandwich.xml
wrote config: generated_bt/config/make_sandwich_bt.yaml
wrote manifest: generated_bt/manifests/make_sandwich_manifest.json
BT static check OK: generated_bt/trees/make_sandwich.xml <-> generated_bt/config/make_sandwich_bt.yaml
```

Required artifacts:

```text
generated_bt/trees/make_sandwich.xml
generated_bt/config/make_sandwich_bt.yaml
generated_bt/manifests/make_sandwich_manifest.json
```

If this fails, treat it as a `lerobot` planner/registry/renderer/static-check
problem.

## Test B - Offline Valid Model Response

Purpose: validates that a valid model-produced Linear IR candidate is accepted
and compiled by `lerobot`.

```bash
PYTHONPATH=src python -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --planner model-response \
  --model-response-file tests/assets/vlm_planner/make_sandwich_valid.json \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --output-dir generated_bt

PYTHONPATH=src python -m lerobot_bt_python.bt_generation.static_checks \
  --xml generated_bt/trees/make_sandwich.xml \
  --yaml generated_bt/config/make_sandwich_bt.yaml
```

Expected:

```text
wrote plan: generated_bt/plans/make_sandwich_linear_ir.json
wrote tree: generated_bt/trees/make_sandwich.xml
wrote config: generated_bt/config/make_sandwich_bt.yaml
wrote raw response: generated_bt/raw_model_responses/make_sandwich_raw_response.json
wrote manifest: generated_bt/manifests/make_sandwich_manifest.json
BT static check OK: generated_bt/trees/make_sandwich.xml <-> generated_bt/config/make_sandwich_bt.yaml
```

If Test A passes and Test B fails, the issue is the model-response parser,
canonicalizer, or strict validator.

## Test C - Offline Malicious Model Responses

Purpose: proves `lerobot` refuses planner contract violations before rendering
or execution.

Run the scripted offline suite:

```bash
scripts/run_runtime_bt_generation_checks.sh
```

It covers:

```text
XML instead of JSON
prose + JSON
invented skill
wrong kind
changed order
missing step
extra step
extra raw_xml field
```

Expected: every malicious case exits non-zero and prints `rejected ... OK`.

Representative error fragments:

```text
Planner response must be JSON only; XML-like content is not allowed.
Planner response is not valid JSON
not present in the registry
in the registry, not
Generated plan does not match canonical task sequence
forbidden fields ['raw_xml']
```

If any malicious case is accepted, stop before ROS tests. That is a planner
contract bug in `lerobot`.

## Test D - Panda Dry-Run Pure Service

Purpose: validates only the ROS service contract exposed by `panda_live_viewer`.
No `lerobot` generation or BT runner is involved.

Start `panda_live_viewer` on branch `after_lorenzo_meeting` with these
parameters:

```bash
planner_dry_run:=true
lazy_load_model:=true
require_generate_plan_service:=true
```

Use the launch or node entrypoint provided by that branch. The command usually
has one of these shapes:

```bash
ros2 launch panda_live_viewer <launch_file>.launch.py \
  planner_dry_run:=true \
  lazy_load_model:=true \
  require_generate_plan_service:=true
```

or:

```bash
ros2 run panda_live_viewer <node_executable> --ros-args \
  -p planner_dry_run:=true \
  -p lazy_load_model:=true \
  -p require_generate_plan_service:=true
```

Then verify the service:

```bash
ros2 service list | grep /lerobot_bt/generate_plan
ros2 service type /lerobot_bt/generate_plan
```

Expected:

```text
/lerobot_bt/generate_plan
lerobot_bt_interfaces/srv/GenerateTaskPlan
```

You can also use the preflight helper:

```bash
python scripts/bt_preflight_check.py --task make_sandwich --check-plan-service
```

If this fails, the issue is in `panda_live_viewer` service startup, ROS
sourcing, package build/sourcing, or the service type contract.

## Test E - LeRobot ROS-Service No-Run

Purpose: validates the integration boundary from `lerobot` to the
`panda_live_viewer` dry-run service, while keeping the C++ runner and skill
server out of scope.

With `panda_live_viewer` still running in dry-run mode:

```bash
PYTHONPATH=src python -m lerobot_bt_python.bt_generation.generate_and_run \
  --task make_sandwich \
  --planner ros-service \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --output-dir generated_bt \
  --no-run
```

Expected:

```text
wrote plan: generated_bt/plans/make_sandwich_linear_ir.json
wrote tree: generated_bt/trees/make_sandwich.xml
wrote config: generated_bt/config/make_sandwich_bt.yaml
wrote raw response: generated_bt/raw_model_responses/make_sandwich_raw_response.json
wrote manifest: generated_bt/manifests/make_sandwich_manifest.json
generated plan: generated_bt/plans/make_sandwich_linear_ir.json
generated tree: generated_bt/trees/make_sandwich.xml
generated config: generated_bt/config/make_sandwich_bt.yaml
generated manifest: generated_bt/manifests/make_sandwich_manifest.json
runner command: ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner ...
```

Run the static check too:

```bash
PYTHONPATH=src python -m lerobot_bt_python.bt_generation.static_checks \
  --xml generated_bt/trees/make_sandwich.xml \
  --yaml generated_bt/config/make_sandwich_bt.yaml
```

If Test D passes but Test E fails, the problem is the ROS service payload,
service response content, `lerobot` ROS client, or strict planner validation.
It is not a BehaviorTree.CPP runner or skill-server problem yet.

## Test F - Runner Without Live VLM Planner

Purpose: validates generated BT execution through BehaviorTree.CPP while
planning remains deterministic through the dry-run service.

Keep `panda_live_viewer` in:

```bash
planner_dry_run:=true
lazy_load_model:=true
require_generate_plan_service:=true
```

Run the same command as Test E but remove `--no-run`:

```bash
PYTHONPATH=src python -m lerobot_bt_python.bt_generation.generate_and_run \
  --task make_sandwich \
  --planner ros-service \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --output-dir generated_bt
```

Expected planning signals are the same as Test E, followed by the C++ runner
starting:

```text
runner command: ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner ...
```

If generation succeeds but execution fails, the problem is runner,
skill server, verifier topic/service wiring, executor YAML, robot hardware, or
runtime policy execution. It is not the VLM planner.

## Test G - VLM Planner Live

Purpose: validates live VLM planning after A-F pass.

Restart `panda_live_viewer` with live planning:

```bash
planner_dry_run:=false
lazy_load_model:=false
require_generate_plan_service:=true
```

Then rerun Test E first:

```bash
PYTHONPATH=src python -m lerobot_bt_python.bt_generation.generate_and_run \
  --task make_sandwich \
  --planner ros-service \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --output-dir generated_bt \
  --no-run
```

Required checks:

```bash
python -m json.tool generated_bt/raw_model_responses/make_sandwich_raw_response.json >/dev/null
python -m json.tool generated_bt/plans/make_sandwich_linear_ir.json >/dev/null
! grep -E '<[A-Za-z]|BehaviorTree|```|Here is|Here are' \
  generated_bt/raw_model_responses/make_sandwich_raw_response.json
```

Expected:

```text
wrote raw response: generated_bt/raw_model_responses/make_sandwich_raw_response.json
wrote plan: generated_bt/plans/make_sandwich_linear_ir.json
```

The saved raw response must be parseable JSON, the saved Linear IR must be
parseable JSON, and the generator must complete strict validation. There must
be no XML, Markdown fences, or prose in `plan_json`.

Only after this no-run check passes should you run without `--no-run`.

## Troubleshooting Map

| Failing test | Likely domain | First checks |
|---|---|---|
| A | `lerobot` template/registry/renderer | Registry names, executor YAML, static blackboard keys |
| B | `lerobot` model-response parser/validator | JSON shape, strict fields, canonical task sequence |
| C | `lerobot` planner contract | Parser rejection, strict validator, forbidden fields |
| D | `panda_live_viewer` service | Branch, launch params, ROS sourcing, service type |
| E | ROS service integration | Request payload, dry-run `plan_json`, `rclpy`, interface package |
| F | Runner / skill server / verifier | `lerobot_bt_runner`, executor YAML, VLM verifier topics, skill server |
| G | Live VLM planner | Raw response format, XML/prose leakage, invalid or reordered Linear IR |

Useful quick checks:

```bash
ros2 service type /lerobot_bt/generate_plan
ros2 interface show lerobot_bt_interfaces/srv/GenerateTaskPlan
PYTHONPATH=src python -m json.tool generated_bt/plans/make_sandwich_linear_ir.json
PYTHONPATH=src python -m lerobot_bt_python.bt_generation.static_checks \
  --xml generated_bt/trees/make_sandwich.xml \
  --yaml generated_bt/config/make_sandwich_bt.yaml
```
