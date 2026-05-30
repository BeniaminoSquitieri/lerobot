# src

This directory contains the LeRobot library plus the ROS 2 / BehaviorTree.CPP
stack used to run Panda tasks.

Use this file for commands. The README files inside each package explain roles
and ownership, but operational commands are centralized here so a new reader
has one place to copy from.

## Package Map

| Path                      | Role                                                                                                                                                                                         |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lerobot/`                | Upstream LeRobot Python library: policies, datasets, processors, robot abstractions, training, evaluation, and custom manipulator backends.                                                  |
| `lerobot_bt_interfaces/`  | ROS 2 service definitions shared by the C++ BT runner and Python skill server.                                                                                                               |
| `lerobot_bt_python/`      | Python skill server, policy execution, Panda/Robotiq/camera config, VLM topics, executor YAML files, runtime BT generation registry/planner/validator/renderer, and fake BT executor server. |
| `lerobot_bt_runtime_cpp/` | C++ BehaviorTree.CPP runner, task XML trees, BT parameter YAML, launch files, and custom BT leaves.                                                                                          |
| `behaviortree_cpp/`       | Gitlink/reserved checkout for BehaviorTree.CPP. The active runtime expects BehaviorTree.CPP from the ROS/system environment.                                                                 |

Main runtime boundary:

```text
lerobot_bt_runtime_cpp
  -> ROS 2 RunNamedCommand service from lerobot_bt_interfaces
  -> lerobot_bt_python server
  -> lerobot policies/processors/robots
  -> VLM request/result topics when scene verification is needed
```

## Task Matrix

| Task                | BT launch                       | BT config                                                   | Python executor config                                |
| ------------------- | ------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------- |
| Make sandwich       | `make_sandwich.launch.py`       | `lerobot_bt_runtime_cpp/config/make_sandwich_bt.yaml`       | `lerobot_bt_python/make_sandwich_executor.yaml`       |
| Make coffee         | `make_coffee.launch.py`         | `lerobot_bt_runtime_cpp/config/make_coffee_bt.yaml`         | `lerobot_bt_python/make_coffee_executor.yaml`         |
| Set breakfast table | `set_breakfast_table.launch.py` | `lerobot_bt_runtime_cpp/config/set_breakfast_table_bt.yaml` | `lerobot_bt_python/set_breakfast_table_executor.yaml` |
| Prepare picnic bag  | `prepare_picnic_bag.launch.py`  | `lerobot_bt_runtime_cpp/config/prepare_picnic_bag_bt.yaml`  | `lerobot_bt_python/prepare_picnic_bag_executor.yaml`  |
| Items in drawer     | `items_in_drawer.launch.py`     | `lerobot_bt_runtime_cpp/config/items_in_drawer_bt.yaml`     | `lerobot_bt_python/items_in_drawer_executor.yaml`     |

Static task XML/YAML files remain the source of truth for existing hand-written
BTs. Generated BTs are created on demand by
`lerobot_bt_python.bt_generation.generate` and written to the paths passed
through `--out-tree` and `--out-config`.

Name alignment rule:

1. BT XML nodes read blackboard keys such as `{place_first_toast_skill}`.
2. `lerobot_bt_runtime_cpp/config/*_bt.yaml` assigns those keys to concrete
   names such as `place_first_toast`.
3. `lerobot_bt_python/*_executor.yaml` must list the same names under
   `expected_skill_names` and `skills`.

## Runtime BT Generation MVP

This repository supports deterministic runtime BT generation for selected
BT-VLM tasks.

The generator does **not** use an LLM or VLM to write XML directly. It uses a
small controlled pipeline:

```text
task name
  -> deterministic template planner
  -> Linear IR
  -> registry validation
  -> XML/YAML rendering
  -> BehaviorTree.CPP runner
```

The generated BTs reproduce known task structures while avoiding manual
XML/YAML duplication.

### Generated BT Output Location

Generated BT files are written wherever `--out-tree` and `--out-config` point.

Example writing to `/tmp`:

```bash
PYTHONPATH=src uv run python -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --out-tree /tmp/generated_make_sandwich.xml \
  --out-config /tmp/generated_make_sandwich_bt.yaml
```

This creates:

```text
/tmp/generated_make_sandwich.xml
/tmp/generated_make_sandwich_bt.yaml
```

For persistent generated files, use a repository-local output directory:

```bash
mkdir -p generated_bt/trees generated_bt/config

PYTHONPATH=src uv run python -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --out-tree generated_bt/trees/generated_make_sandwich.xml \
  --out-config generated_bt/config/generated_make_sandwich_bt.yaml
```

Recommended layout:

```text
generated_bt/
  trees/
    generated_make_sandwich.xml
    generated_set_breakfast_table.xml
  config/
    generated_make_sandwich_bt.yaml
    generated_set_breakfast_table_bt.yaml
```

`/tmp` is useful for quick testing. A repository-local folder is better when the
generated BT must be inspected, committed, copied to another machine, or passed
to the ROS 2 runner.

### Runtime Generation Components

| Path                                                   | Role                                                                                              |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| `lerobot_bt_python/bt_generation/skills_registry.yaml` | Registry of known `robot_skill`, `human_step`, and `vlm_gate` entries.                            |
| `lerobot_bt_python/bt_generation/planner.py`           | Deterministic template planner that creates a Linear IR from a known task name.                   |
| `lerobot_bt_python/bt_generation/validator.py`         | Validates names, step kinds, retry values, timeouts, executor YAML alignment, and VLM gate tasks. |
| `lerobot_bt_python/bt_generation/renderer.py`          | Renders BehaviorTree.CPP XML and BT parameter YAML.                                               |
| `lerobot_bt_python/bt_generation/static_checks.py`     | Verifies generated XML blackboard keys are present in the generated YAML.                         |
| `lerobot_bt_python/bt_generation/generate.py`          | CLI entry point for generating XML/YAML.                                                          |
| `lerobot_bt_python/fakes/fake_bt_executor_server.py`   | Fake ROS 2 server for testing generated BTs without robot, camera, policy, or VLM.                |

### Step Kinds

The generator supports three explicit step kinds.

| Kind          | Executor                         | Meaning                                                                                           |
| ------------- | -------------------------------- | ------------------------------------------------------------------------------------------------- |
| `robot_skill` | Robot / Python skill server      | A real robot policy/skill executed through `DoSkill`.                                             |
| `human_step`  | Human, verified through VLM/gate | A task step expected to be performed by a human, represented as `AwaitScene`, never as `DoSkill`. |
| `vlm_gate`    | VLM verifier                     | A visual condition or task milestone checked through `AwaitScene`.                                |

Example from `make_sandwich`:

```text
initial_scene_ready          -> vlm_gate
place_first_toast            -> robot_skill
pour_ingredient              -> human_step
ingredient_poured            -> vlm_gate
second_toast_ready           -> vlm_gate
place_second_toast           -> robot_skill
make_sandwich.task_complete  -> vlm_gate
```

`pour_ingredient` is intentionally a `human_step` because it is not a robot
policy in the existing repository state. It is treated as a human/manual action
verified by the BT-VLM gate flow.

### Retry Policy

Generated XML uses `RetryUntilSuccessful`.

Retry counts are not chosen by the renderer. They are read from the registry and
written into the generated BT YAML.

In this repository:

```text
max_attempts: -1  means infinite retry
max_attempts: N   means retry up to N attempts
max_attempts: 0   is invalid
```

Even when retry is infinite, each individual attempt must still have a positive
timeout:

```yaml
place_first_toast_timeout_s: 120.0
place_first_toast_max_attempts: -1
```

Do not remove per-attempt timeouts. Infinite retry only makes sense if each
attempt can terminate.

### Generate Known Tasks

Generate `make_sandwich`:

```bash
PYTHONPATH=src uv run python -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --out-tree /tmp/generated_make_sandwich.xml \
  --out-config /tmp/generated_make_sandwich_bt.yaml
```

Generate `set_breakfast_table`:

```bash
PYTHONPATH=src uv run python -m lerobot_bt_python.bt_generation.generate \
  --task set_breakfast_table \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/set_breakfast_table_executor.yaml \
  --out-tree /tmp/generated_set_breakfast_table.xml \
  --out-config /tmp/generated_set_breakfast_table_bt.yaml
```

Inspect generated files:

```bash
cat /tmp/generated_make_sandwich.xml
cat /tmp/generated_make_sandwich_bt.yaml
```

### Offline Validation Without ROS 2

Use this on a laptop without ROS 2, robot, cameras, RealSense, or VLM.

```bash
PYTHONPATH=src PYTHON_BIN=python scripts/check_generated_bt_offline.sh
```

The offline script validates:

```text
generated make_sandwich OK
generated set_breakfast_table OK
XML/YAML blackboard keys OK
pytest OK
```

You can also run the full BT Python test suite:

```bash
uv run pytest tests/lerobot_bt -svv
```

or, inside the conda environment:

```bash
conda run -n lerobot python -m pytest tests/lerobot_bt -svv
```

### XML/YAML Blackboard Key Check

Generated XML uses blackboard keys such as:

```xml
<DoSkill skill_name="{place_first_toast_skill}" timeout_s="{place_first_toast_timeout_s}" />
```

Every `{...}` key in the XML must exist under:

```yaml
lerobot_bt_runner:
  ros__parameters:
    bt:
```

in the generated YAML.

The generator runs this static check before writing output. If a generated XML
references a missing YAML key, generation fails.

### ROS 2 / C++ Integration Test Without Robot

This test requires ROS 2, `rclpy`, the built C++ runtime package, and a sourced
workspace. It still does **not** require the robot, cameras, policy checkpoints,
or a real VLM.

Setup:

```bash
source /opt/ros/${ROS_DISTRO}/setup.bash
colcon build --base-paths src --packages-up-to lerobot_bt_runtime_cpp --symlink-install
source install/setup.bash
```

Run fake integration scenarios:

```bash
PYTHONPATH=src scripts/test_generated_bt_with_fake_server.sh success_all success
PYTHONPATH=src scripts/test_generated_bt_with_fake_server.sh initial_scene_failed failure
PYTHONPATH=src scripts/test_generated_bt_with_fake_server.sh robot_first_toast_failed failure
PYTHONPATH=src scripts/test_generated_bt_with_fake_server.sh human_pouring_timeout failure
PYTHONPATH=src scripts/test_generated_bt_with_fake_server.sh unknown_status failure
```

If ROS 2 is not available, the script exits during preflight with a clear error:

```text
ERROR: ROS2 not found. Source ROS2 before running C++ integration test.
Example: source /opt/ros/<distro>/setup.bash
```

No fake server is started when preflight fails.

### Fake BT Executor Server

The fake server simulates the ROS 2 services used by the BT runtime:

```text
RunNamedCommand.srv
GetSkillVerification.srv
```

Run manually:

```bash
PYTHONPATH=src python -m lerobot_bt_python.fakes.fake_bt_executor_server \
  --scenario success_all
```

It does not load:

```text
Panda robot
LeRobot policies
RealSense cameras
transformers
real VLM
```

Use it only to validate BT/ROS/VLM control contracts.

### Current Runtime Generation Limits

The MVP intentionally does not support:

```text
LLM planner
VLM-generated XML
runtime hot-swap while the tree is ticking
Parallel nodes
automatic human/robot allocation
automatic human fallback branches
symbolic preconditions/effects
```

The VLM verifies scene gates. It does not generate the BT.

The current safe extension path is:

```text
1. deterministic templates
2. generated XML/YAML validation
3. fake ROS 2 integration
4. real robot run
5. optional VLM scene facts
6. optional LLM/VLM planner that outputs Linear IR, not raw XML
```

## One-Time Setup

From the repository root:

```bash
cd /home/bsquitieri/lerobot
uv sync --locked --extra all
```

Source ROS 2. Use the distribution installed on the machine:

```bash
source /opt/ros/jazzy/setup.bash
```

or:

```bash
source /opt/ros/humble/setup.bash
```

Install ROS dependencies and build the BT packages:

```bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --packages-up-to lerobot_bt_runtime_cpp --symlink-install
source install/setup.bash
```

If BehaviorTree.CPP headers are missing during build, install the ROS package
for the active distro and rebuild:

```bash
sudo apt install ros-${ROS_DISTRO}-behaviortree-cpp-v3
colcon build --base-paths src --packages-up-to lerobot_bt_runtime_cpp --symlink-install
```

## Preflight Before Robot Rollout

Dry run, no hardware checks:

```bash
uv run python scripts/bt_preflight_check.py --task make_sandwich
```

With robot/camera checks:

```bash
uv run python scripts/bt_preflight_check.py --task make_sandwich --real
```

Validate every known BT task:

```bash
uv run python scripts/bt_preflight_check.py --all
```

## Run A BT Task

Open one terminal per process. In every terminal:

```bash
cd /home/bsquitieri/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

Use `/opt/ros/humble/setup.bash` instead if this machine uses Humble.

Terminal 1: start the Python skill server.

```bash
uv run lerobot-bt-skill-server \
  --config_path=src/lerobot_bt_python/make_sandwich_executor.yaml
```

Terminal 2: start the VLM verifier. It should read `/lerobot_bt/vlm_request`
and write `/lerobot_bt/vlm_result`.

Terminal 3: start the C++ BehaviorTree.CPP runner.

```bash
ros2 launch lerobot_bt_runtime_cpp make_sandwich.launch.py
```

Optional: open Groot2 monitoring.

```bash
uv run lerobot-bt-groot2
```

## Run A Generated BT Task

Generate the task XML/YAML first. Example for `make_sandwich`:

```bash
mkdir -p generated_bt/trees generated_bt/config

PYTHONPATH=src uv run python -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --out-tree generated_bt/trees/generated_make_sandwich.xml \
  --out-config generated_bt/config/generated_make_sandwich_bt.yaml
```

Then pass the generated paths to the C++ runner or launch file, depending on the
available runtime entry point on the machine.

Example pattern:

```bash
ros2 launch lerobot_bt_runtime_cpp make_sandwich.launch.py \
  tree_xml_path:=generated_bt/trees/generated_make_sandwich.xml \
  bt_params_path:=generated_bt/config/generated_make_sandwich_bt.yaml
```

If the task launch file does not expose `tree_xml_path` or `bt_params_path`,
use the runner executable or update the launch file to forward those parameters.

## Run Another Task

Set the task name and use the matching Python executor YAML and C++ launch
file:

```bash
TASK=items_in_drawer
uv run lerobot-bt-skill-server \
  --config_path=src/lerobot_bt_python/${TASK}_executor.yaml
```

In another terminal:

```bash
ros2 launch lerobot_bt_runtime_cpp ${TASK}.launch.py
```

For generated BTs, generate the matching XML/YAML first and pass those generated
paths to the runner.

## Useful ROS Interface Commands

After building and sourcing `install/setup.bash`:

```bash
ros2 interface show lerobot_bt_interfaces/srv/RunNamedCommand
ros2 interface show lerobot_bt_interfaces/srv/GetSkillVerification
ros2 interface show lerobot_bt_interfaces/srv/ReportSkillVerification
```

Disable Groot publishing for one run:

```bash
ros2 launch lerobot_bt_runtime_cpp make_sandwich.launch.py \
  enable_groot_publisher:=false
```

## Manual VLM Verdict

The Python server publishes JSON requests on `/lerobot_bt/vlm_request`. A
verifier responds on `/lerobot_bt/vlm_result` with the same `skill_name` and
`attempt_id`.

Use the `attempt_id` printed by the server banner:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":1,\"status\":\"SUCCESS\",\"message\":\"Scene check passed.\"}'}"
```

Terminal statuses are `SUCCESS` and `FAILURE`. `RUNNING` keeps the gate open.

## Generic LeRobot Commands

Inspect the local LeRobot environment:

```bash
uv run lerobot-info
```

Find connected cameras:

```bash
uv run lerobot-find-cameras
```

Train a generic LeRobot policy:

```bash
uv run lerobot-train \
  --policy=act \
  --dataset.repo_id=lerobot/aloha_mobile_cabinet
```

Evaluate a generic LeRobot policy:

```bash
uv run lerobot-eval \
  --policy.path=lerobot/pi0_libero_finetuned \
  --env.type=libero \
  --env.task=libero_object \
  --eval.n_episodes=10
```

## Tests And Lightweight Checks

Run the BT Python tests:

```bash
uv run pytest tests/lerobot_bt -q
```

Run all tests:

```bash
uv run pytest tests -svv --maxfail=10
```

Run generated BT offline validation without ROS 2:

```bash
PYTHONPATH=src PYTHON_BIN=python scripts/check_generated_bt_offline.sh
```

When dependencies are unavailable, at least syntax-check the BT Python files:

```bash
python3 -m py_compile src/lerobot_bt_python/*.py
```
