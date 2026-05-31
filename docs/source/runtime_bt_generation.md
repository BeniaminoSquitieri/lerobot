# Runtime BT Generation MVP

This document describes the first safe version of runtime Behavior Tree
generation for the BT-VLM tasks.

## Flow

`lerobot` owns validation, compilation, generated XML/YAML, and BT execution.
`panda_live_viewer` owns visual planning and VLM reasoning. When visual planning
is used, it must return Linear IR JSON only; it must never generate
BehaviorTree.CPP XML.

The default v1 flow is deterministic:

1. A known `task_name` selects a hard-coded template.
2. The template is expanded into a Linear IR JSON object.
3. The registry validator checks names, executors, timeouts, attempts, and
   verification links.
4. The plan validator checks the Linear IR against the registry and, when
   provided, the executor YAML.
5. The renderer writes BehaviorTree.CPP XML and ROS2 BT parameter YAML.
6. The generated XML/YAML pass a static blackboard key check.

The BT is generated once at episode start and then executed normally by
BehaviorTree.CPP. There is no hot-swap during execution and no runtime
replanning yet.

## Supported Static Tasks

The template planner supports all current static BT tasks:

| task_name | Static tree | Executor YAML |
|---|---|---|
| `make_sandwich` | `src/lerobot_bt_runtime_cpp/trees/make_sandwich.xml` | `src/lerobot_bt_python/make_sandwich_executor.yaml` |
| `set_breakfast_table` | `src/lerobot_bt_runtime_cpp/trees/set_breakfast_table.xml` | `src/lerobot_bt_python/set_breakfast_table_executor.yaml` |
| `make_coffee` | `src/lerobot_bt_runtime_cpp/trees/make_coffee.xml` | `src/lerobot_bt_python/make_coffee_executor.yaml` |
| `prepare_picnic_bag` | `src/lerobot_bt_runtime_cpp/trees/prepare_picnic_bag.xml` | `src/lerobot_bt_python/prepare_picnic_bag_executor.yaml` |
| `items_in_drawer` | `src/lerobot_bt_runtime_cpp/trees/items_in_drawer.xml` | `src/lerobot_bt_python/items_in_drawer_executor.yaml` |

The registry uses concrete names from the static BT YAML profiles and executor
YAML files. `DoSkill` leaves become `robot_skill`; human-operated
`AwaitScene` leaves become `human_step`; pure visual checkpoints become
`vlm_gate`.

`items_in_drawer` intentionally keeps `insert_next_drawer_item` under
`RetryUntilSuccessful`. The robot skill inserts the next object; if objects
remain, the VLM can report failure and BehaviorTree.CPP retries the same leaf
until the configured retry budget is exhausted or the VLM reports completion.

## Planner Modes

### Template Planner

The default planner is still the deterministic template planner:

```bash
--planner template
```

It runs entirely in `lerobot` and supports all five static tasks listed above.

### Model-response Planner Mode

An optional controlled planner mode reads a pre-generated model response from
disk:

```bash
--planner model-response
--model-response-file tests/assets/vlm_planner/make_sandwich_valid.json
```

This mode does not call any external VLM or LLM API. The model response is a
candidate Linear IR JSON object only. It must not contain BehaviorTree.CPP XML,
Markdown explanations, free-form actions, invented skill names, or arbitrary
human/robot assignments.

The safe flow is:

```text
task_name + optional scene_facts/model_response
  -> constrained model planner response
  -> Linear IR candidate JSON
  -> canonicalization
  -> strict validation
  -> existing XML/YAML renderer
  -> static XML/YAML blackboard check
  -> generated BT executed normally
```

The registry decides which names are `robot_skill`, `human_step`, and
`vlm_gate`. The validator rejects unknown names and wrong kinds, such as
`pour_ingredient` as a `robot_skill` or `place_first_toast` as a `human_step`.
For `make_sandwich`, strict validation also requires `initial_scene_ready` at
the start, `make_sandwich.task_complete` at the end, `second_toast_ready`
before `place_second_toast`, and `ingredient_poured` after `pour_ingredient`
when the human pouring step appears.

Example:

```bash
PYTHONPATH=src python -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --planner model-response \
  --model-response-file tests/assets/vlm_planner/make_sandwich_valid.json \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --output-dir generated_bt
```

This writes the validated Linear IR to
`generated_bt/plans/make_sandwich_linear_ir.json`, XML to
`generated_bt/trees/make_sandwich.xml`, YAML to
`generated_bt/config/make_sandwich_bt.yaml`, and the raw response to
`generated_bt/raw_model_responses/make_sandwich_raw_response.json`.

### ROS-service Planner Mode

`ros-service` is the intended live integration path with `panda_live_viewer`,
but it is not implemented in this repository yet. The intended contract is:

```text
lerobot
  -> asks a remote panda_live_viewer/VLM ROS service for Linear IR JSON
  -> validates and canonicalizes that JSON
  -> renders BehaviorTree.CPP XML/YAML
  -> executes the generated BT normally
```

The VLM server may already receive camera images over ROS. It still returns
Linear IR JSON only; `lerobot` remains the component that validates and
compiles BT artifacts.

Keep the model-response planner and the runtime VLM verifier separate:

```text
Current VLM verifier:
  input: one condition/check
  output: STATUS + REASON

Model-response planner mode:
  input: task + registry + optional scene facts
  output: Linear IR JSON candidate
```

The verifier still runs during BT execution through `DoSkill` and
`AwaitScene`. The planner runs only once before the BT is generated.

## Generated Output Directory

The preferred visible output folder is repository-local:

```text
generated_bt/
  plans/
  trees/
  config/
  raw_model_responses/
```

Use `--output-dir generated_bt` for normal development:

```bash
PYTHONPATH=src python -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --planner template \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --output-dir generated_bt
```

This writes:

```text
generated_bt/trees/make_sandwich.xml
generated_bt/config/make_sandwich_bt.yaml
```

`/tmp` can still be used for quick one-off tests with explicit `--out-tree` and
`--out-config`, but `generated_bt/` is the recommended path for normal
inspection and handoff.

## C++ Runtime Contract

The active C++ runtime registers two merged BehaviorTree.CPP leaves:

| Node | Calls service | Uses blackboard keys | Waits/polls | Returns SUCCESS when | Notes |
|---|---|---|---|---|---|
| `DoSkill` | `RunNamedCommand(kind="skill")`, then `GetSkillVerification` | `{*_skill}`, `{*_timeout_s}` | Yes, polls `GetSkillVerification(skill_name)` | command succeeds and VLM status becomes `SUCCESS` | The node already includes skill verification. |
| `AwaitScene` | `RunNamedCommand(kind="vlm_gate_pending")`, then `GetSkillVerification` | `{*_gate}` | Yes, polls `GetSkillVerification(scene_name)` | gate command succeeds and VLM status becomes `SUCCESS` | Used for VLM gates and human steps. |
| `RunNamedCommandNode` | `RunNamedCommand` only | `kind`, `command_name`, optional `timeout_s` | Waits for command future only | service response has `success=true` | Legacy/base wrapper, not used by generated XML. |

There is no active separate `WaitForVLMVerdict` XML node. The current
`AwaitScene` and `DoSkill` nodes replace the old open-gate plus wait-verdict
pairs.

Because `DoSkill` already waits for `GetSkillVerification`, generated BTs do
not add robot `verify_after` gates by default. The CLI supports
`--explicit-postcondition-gates` for manual experiments, but the safe default
avoids duplicated verification after robot skills. The current static-task
templates render human stages as one merged `AwaitScene` leaf, matching the
hand-written XML files.

## Retry Policy

The generator does not choose retry counts on its own. It preserves
`max_attempts` from the registry and writes the same value into generated BT
YAML. The generated XML keeps `RetryUntilSuccessful` and reads
`num_attempts` from the blackboard, for example
`num_attempts="{place_first_toast_max_attempts}"`.

In this repository, infinite retry is represented as `max_attempts: -1`.
BehaviorTree.CPP's `RetryNode` documents `-1` as the infinite loop value and
its tick logic keeps retrying while `max_attempts_ == -1`.

| value | meaning |
|---|---|
| `-1` | retry indefinitely until the child returns `SUCCESS` |
| `0` | not an infinite value; rejected by the generator validator |
| positive `N` | retry at most `N` failing attempts |
| other negative value | invalid |

Every single attempt still needs `timeout_s > 0`. Infinite external retry is
therefore different from a `DoSkill` without timeout: the child must be able to
return `SUCCESS` or `FAILURE` so `RetryUntilSuccessful` can decide whether to
stop or try again. A robot policy may also retry internally during its own
execution window, while the outer `RetryUntilSuccessful` repeats the BT node
after a failed attempt.

## Step Kinds

`robot_skill` is a robot action backed by an executor YAML skill and
`expected_skill_names`.

`human_step` is a planned human action. It is not a fallback. In the current
runtime it is rendered with the existing `AwaitScene` node so the operator can
perform the action and the VLM/manual verifier can resolve it.

`vlm_gate` is a visual verification gate. It is rendered with `AwaitScene` and
must have a non-empty task description.

## Inference

The registry is built from the existing BT XML, BT parameter YAML, and executor
YAML:

- Names in executor YAML `skills` or `expected_skill_names` are robot skills.
- Names used as `AwaitScene` gates and VLM gate tasks are VLM gates.
- Physical actions described as human/manual gates, but absent from robot
  skills, are human steps.

For the sandwich task, `place_first_toast` and `place_second_toast` are robot
skills because they appear in `make_sandwich_executor.yaml` under both
`expected_skill_names` and `skills`. `pour_ingredient` is a human step because
the existing XML renders it as an `AwaitScene` manual/VLM gate and it is not a
robot skill in the executor YAML.

## No Automatic Fallback

The generator never emits an automatic human fallback branch. A `human_step`
means that the human action is part of the task contract.

## Why The V1 Is Small

The v1 intentionally avoids:

- external LLM/VLM API calls
- VLM-generated XML or BehaviorTree.CPP nodes
- automatic human/robot allocation
- fallback branches
- `Parallel` nodes
- hot-swap while a tree is ticking
- `risk_level`
- symbolic preconditions/effects

This keeps the generated tree reversible, auditable, and close to the existing
BehaviorTree.CPP runtime.

## Adding Entries

To add a robot skill:

1. Add the skill to the executor YAML `skills`.
2. Add it to `expected_skill_names`.
3. Add a `robot_skills` entry in
   `src/lerobot_bt_python/bt_generation/skills_registry.yaml`.
4. Point `verify_after` to an existing `vlm_gate`, or set it explicitly to
   `null`.

To add a human step:

1. Confirm the existing task treats it as a human/manual/VLM gate rather than a
   robot policy.
2. Add a `human_steps` entry with a non-empty `instruction`.
3. Point `verify_after` to an existing `vlm_gate`, or set it explicitly to
   `null`.
4. Add the human step name to executor YAML `vlm_gate_tasks` when that file
   declares gate tasks, because the current runtime renders it as `AwaitScene`.

To add a VLM gate:

1. Add a `vlm_gates` entry with a non-empty `task`.
2. Add the same gate to executor YAML `vlm_gate_tasks` when that file declares
   gate tasks.
3. Reference it from a deterministic template or from a `verify_after` link.

## CLI

Example using the preferred visible output directory:

```bash
PYTHONPATH=src python -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --planner template \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --output-dir generated_bt
```

Generate the other static tasks by changing the task and executor YAML:

```bash
PYTHONPATH=src python -m lerobot_bt_python.bt_generation.generate \
  --task make_coffee \
  --planner template \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_coffee_executor.yaml \
  --output-dir generated_bt

PYTHONPATH=src python -m lerobot_bt_python.bt_generation.generate \
  --task prepare_picnic_bag \
  --planner template \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/prepare_picnic_bag_executor.yaml \
  --output-dir generated_bt

PYTHONPATH=src python -m lerobot_bt_python.bt_generation.generate \
  --task items_in_drawer \
  --planner template \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/items_in_drawer_executor.yaml \
  --output-dir generated_bt
```

The CLI writes no outputs if registry or plan validation fails.

## Offline Validation Without ROS2

The laptop workflow does not require ROS2, Panda, camera, VLM, or the C++
runner. It validates Python generation, fake Linear IR execution, generated
XML/YAML blackboard consistency, and safety checks:

```bash
conda run -n lerobot python -m pytest tests/lerobot_bt -svv
```

Generate a sandwich BT:

```bash
PYTHONPATH=src conda run -n lerobot python -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --planner template \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --output-dir generated_bt
```

The offline helper generates and checks all five supported tasks:

```text
generated make_sandwich OK
generated set_breakfast_table OK
generated make_coffee OK
generated prepare_picnic_bag OK
generated items_in_drawer OK
XML/YAML blackboard keys OK
pytest OK
```

Run the offline helper:

```bash
PYTHONPATH=src PYTHON_BIN=python GENERATED_BT_DIR=generated_bt scripts/check_generated_bt_offline.sh
```

The generator performs a static blackboard check before writing output: every
`{key}` referenced by generated XML must exist under
`lerobot_bt_runner.ros__parameters.bt` in generated YAML. Extra YAML keys are
allowed.

## ROS2/C++ Integration Validation

The C++ integration test requires a ROS2 environment. Before running it, make
sure these are available:

- `ros2`
- `rclpy`
- `colcon`
- a built workspace containing `lerobot_bt_runtime_cpp`
- sourced ROS2 and workspace setup files

Setup and build:

```bash
source /opt/ros/<distro>/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Run the generated tree with the fake server and C++ runner:

```bash
PYTHONPATH=src scripts/test_generated_bt_with_fake_server.sh success_all success
PYTHONPATH=src scripts/test_generated_bt_with_fake_server.sh initial_scene_failed failure
```

If ROS2 is missing, `scripts/test_generated_bt_with_fake_server.sh` fails in
preflight with exit code `2` and a clear message instead of starting the fake
server or producing an `rclpy` traceback.

The script runs the equivalent C++ command after preflight passes:

```bash
ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner \
  --ros-args \
  --params-file generated_bt/config/make_sandwich_bt.yaml \
  -p tree_xml_path:=generated_bt/trees/make_sandwich.xml \
  -p enable_groot_publisher:=false
```

Fake scenarios:

| Scenario | Behavior | Expected result |
|---|---|---|
| `success_all` | every command and VLM check succeeds | BT success |
| `initial_scene_failed` | `initial_scene_ready` VLM check fails | BT failure before robot skills |
| `robot_first_toast_failed` | `place_first_toast` command fails | BT failure before human pour |
| `human_pouring_timeout` | `pour_ingredient` remains `RUNNING` until fake timeout | BT failure before second toast |
| `vlm_postcondition_failed` | `place_first_toast` VLM check fails | BT failure before human pour |
| `unknown_status` | fake VLM typo such as `DONE`/`SUCESS` is normalized | failure, never infinite running |

The fake server validates BT/ROS/VLM contracts only. It does not test Panda
hardware, policy inference, camera publishing, physical safety, or real VLM
quality.

## Known Limits

- Templates are deterministic and must be edited in code.
- The current renderer uses existing `AwaitScene` for `human_step`.
- The current `DoSkill` node is a merged action-plus-verification node, so
  robot `verify_after` gates are not rendered by default.
- Model-response mode reads a pre-generated JSON response only; no live
  external LLM/VLM API call is included.
- No VLM-generated XML is accepted.
- No automatic human fallback is emitted.
- No `Parallel` nodes are emitted.
- No hot-swap of a running BT is implemented.
