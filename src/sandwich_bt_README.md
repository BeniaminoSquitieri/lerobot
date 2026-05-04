# Sandwich BT Stack

This is the operational guide for the Sandwich Behavior Tree stack.

The goal is to run and test a long-horizon sandwich task with:

* a BehaviorTree.CPP runtime;
* ROS2 service boundaries;
* learned robot primitives, for example ACT or GR00T policies;
* scripted recoveries;
* an optional collaborative supervisor for robot-human task allocation;
* a mock/simulation path that works without Panda hardware.

Current validated status:

* BehaviorTree.CPP runner builds and runs.
* `sandwich_tree.xml` runs successfully against the mock ROS2 skill server.
* `place_first_toast_subtree.xml` runs successfully against the mock ROS2 skill server.
* `place_second_toast_subtree.xml` runs successfully against the mock ROS2 skill server.
* Collaborative supervisor server runs through ROS2 services.
* Collaborative runner reaches `DONE` in the positive mock path.
* Collaborative runner reaches `ABORT` in the negative human-confirmation path.
* The real Panda hardware path and full ACT execution loop are not yet validated.

Do not claim that the real robot makes the sandwich until the real Panda server, gripper, cameras, checkpoints, and ACT primitive execution have been tested.

---

## 1. Architecture

The stack is split into four packages.

### `sandwich_bt_runtime_cpp`

Owns:

* BehaviorTree.CPP orchestration;
* BT XML loading;
* retry and recovery logic inside the tree;
* optional Groot publication;
* the C++ `RunNamedCommand` BT leaf.

Does not own:

* learned policy loading;
* Panda control;
* task planning;
* human/robot allocation.

### `sandwich_bt_python`

Owns:

* the Python ROS2 skill server;
* learned policy execution;
* scripted recoveries;
* robot connection;
* command results;
* mock skill simulation.

Does not own:

* BT ordering;
* collaborative planning;
* VLM scene reasoning.

### `sandwich_bt_interfaces`

Owns the ROS2 service contracts:

* `RunNamedCommand.srv`
* `GetSkillVerification.srv`
* `ReportSkillVerification.srv`
* `PlanNextStep.srv`
* `VerifyStep.srv`

### `sandwich_bt_supervisor`

Owns the collaborative execution layer above the BT/runtime boundary:

* closed-set scene-state estimation;
* task allocation;
* human handoff;
* step verification;
* collaborative runner;
* ROS2 supervisor server.

The supervisor does not replace BehaviorTree.CPP. It decides the next closed-set step and actor. Robot-owned steps still execute through BT subtrees.

---

## 2. Runtime Flow

Robot-only runtime flow:

1. The C++ runner loads a BT XML file.
2. A `RunNamedCommand` BT leaf sends a ROS2 service request.
3. The Python skill server receives `kind`, `name`, and optional `timeout_s`.
4. The Python executor runs either one learned skill or one scripted recovery.
5. If the command is a skill and the rollout succeeds, the Python server opens a
   `PENDING` verification attempt for that skill name.
6. The Python server returns `success`, `status`, `elapsed_s`, and `message`.
7. A `VerifySkillOutcome` BT leaf polls `/sandwich_bt/get_skill_verification`
   until an external verifier reports `SUCCESS` or `FAILURE`.
8. The C++ BT uses that verdict to continue the tree or trigger another retry.

Collaborative runtime flow:

1. `sandwich_bt_supervisor` estimates or receives the current closed-set sandwich state.
2. The supervisor picks the next step.
3. The supervisor assigns the step to `robot`, `human`, `done`, or `abort`.
4. Robot-owned steps execute through small BT subtrees.
5. Human-owned steps require explicit confirmation and scene verification.
6. After each step, the supervisor verifies the scene and decides the next handoff.

The VLM, when added, should not command robot motion directly. It should produce closed-set observations such as:

* `first_toast_on_plate`
* `ingredient_poured`
* `second_toast_on_top`
* confidence
* failure reason

---

## 3. Simulation vs Real-Time Execution

The BT stack is intentionally designed so that simulation and real-time execution share the same orchestration path.

### What stays the same

The following components are the same in simulation and real-time execution:

* the BT XML files;
* the C++ `sandwich_bt_runner` executable;
* the `RunNamedCommand` BT leaf;
* the ROS2 service name `/sandwich_bt/run_command`;
* the request fields: `kind`, `name`, `timeout_s`;
* the response fields: `success`, `status`, `elapsed_s`, `message`;
* the behavior-tree success/failure semantics;
* the retry and recovery logic inside the XML tree.

This means the BT does not know whether a command is handled by a mock skill server or by the real ACT/Panda skill server.

### What changes

Only the Python-side service implementation changes.

In simulation:

```text
sandwich_bt_runner
  -> RunNamedCommand
  -> /sandwich_bt/run_command
  -> lerobot-bt-skill-sim --ros2-service
  -> mock success/failure result
  -> VerifySkillOutcome
  -> /sandwich_bt/get_skill_verification
  -> mock verifier verdict
```

In real-time robot execution:

```text
sandwich_bt_runner
  -> RunNamedCommand
  -> /sandwich_bt/run_command
  -> lerobot-bt-skill-server
  -> ACT/BC policy or scripted recovery
  -> Panda / gripper / cameras
  -> VerifySkillOutcome
  -> /sandwich_bt/get_skill_verification
  -> external VLM or verifier
```

The BT orchestration is the same. The executor behind `/sandwich_bt/run_command` changes.

### Practical interpretation

If the simulated BT test passes, you have validated:

* BT XML structure;
* BehaviorTree.CPP execution;
* ROS2 service communication;
* command names;
* retry/recovery ordering;
* success/failure propagation.

You have not validated:

* Panda hardware control;
* ACT checkpoint quality;
* camera observations;
* gripper behavior;
* physical task robustness;
* action semantics on the real robot.

Correct claim after simulation passes:

```text
The BT orchestration works end-to-end over ROS2 using a mock skill server.
The next step is replacing the mock skill server with the real ACT/Panda skill server.
```

Incorrect claim:

```text
The robot can make a sandwich autonomously.
```

---

## 4. Key Files

BT files:

* Full tree: `src/sandwich_bt_runtime_cpp/trees/sandwich_tree.xml`
* First-primitive test tree: `src/sandwich_bt_runtime_cpp/trees/sandwich_tree_first_primitive_only.xml`
* First toast subtree: `src/sandwich_bt_runtime_cpp/trees/place_first_toast_subtree.xml`
* Pour subtree: `src/sandwich_bt_runtime_cpp/trees/pour_subtree.xml`
* Second toast subtree: `src/sandwich_bt_runtime_cpp/trees/place_second_toast_subtree.xml`

Python skill configs:

* Real robot config: `src/sandwich_bt_python/sandwich_bt_executor.yaml`
* Headless config: `src/sandwich_bt_python/sandwich_bt_executor_headless.yaml`

Supervisor config:

* `src/sandwich_bt_supervisor/sandwich_bt_supervisor.yaml`

ROS2 services:

* `src/sandwich_bt_interfaces/srv/RunNamedCommand.srv`
* `src/sandwich_bt_interfaces/srv/GetSkillVerification.srv`
* `src/sandwich_bt_interfaces/srv/ReportSkillVerification.srv`
* `src/sandwich_bt_interfaces/srv/PlanNextStep.srv`
* `src/sandwich_bt_interfaces/srv/VerifyStep.srv`

Runtime entry points:

* Python skill server: `src/sandwich_bt_python/server.py`
* Python skill executor: `src/sandwich_bt_python/executor.py`
* Python mock skill simulation: `src/sandwich_bt_python/simulation.py`
* C++ BT runner: `src/sandwich_bt_runtime_cpp/src/sandwich_bt_main.cpp`
* C++ BT leaf: `src/sandwich_bt_runtime_cpp/src/run_named_command_node.cpp`
* Supervisor ROS2 server: `src/sandwich_bt_supervisor/server.py`
* Collaborative runner: `src/sandwich_bt_supervisor/collaborative_runner.py`
* Supervisor service probe: `src/sandwich_bt_supervisor/service_probe.py`

Documentation:

* Doxygen config: `docs/doxygen/Doxyfile`
* Architecture docs: `docs/doxygen/architecture.md`
* Runtime flows: `docs/doxygen/runtime_flows.md`
* Troubleshooting: `docs/doxygen/troubleshooting.md`

---

## 5. Recommended Environment Policy

Use one Python runtime policy and stick to it.

Recommended for this project:

* use the conda environment named `lerobot` for Python runtime;
* do not use `uv run` for runtime commands if you want everything inside conda;
* use `/usr/bin/python3` for ROS2 `colcon` builds when needed;
* always source ROS2 and the local workspace before running ROS2 nodes.

This avoids the common mismatch where `uv run` executes from `.venv`, while your dependencies are installed in conda.

Runtime rule:

```bash
conda activate lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

Then run entry points directly:

```bash
lerobot-bt-skill-server
lerobot-bt-skill-sim
lerobot-bt-supervisor-server
lerobot-bt-collaborative-runner
```

Avoid this unless you intentionally want to use the repo `.venv`:

```bash
uv run lerobot-bt-skill-server
```

---

## 6. Fresh Machine Setup

These steps assume Ubuntu with ROS2 Jazzy.

### 6.1 Install system packages

```bash
sudo apt update
sudo apt install -y \
  build-essential \
  cmake \
  git \
  pkg-config \
  python3-rosdep2 \
  python3-colcon-common-extensions \
  libzmq3-dev
```

Optional but useful:

```bash
sudo apt install -y ffmpeg doxygen graphviz
```

If `rosdep` has never been initialized on the machine:

```bash
sudo rosdep init
rosdep update
```

If `sudo rosdep init` says it was already initialized, just run:

```bash
rosdep update
```

### 6.2 Install and verify ROS2 Jazzy

Install ROS2 Jazzy using the official ROS2 installation instructions for your Ubuntu version.

Then verify:

```bash
source /opt/ros/jazzy/setup.bash
ros2 --help
```

### 6.3 Create the conda environment

```bash
conda create -n lerobot python=3.12 -y
conda activate lerobot
python -m pip install -U pip uv
```

From the repository root:

```bash
cd ~/lerobot
python -m pip install -e .
```

Install the Python packages that commonly break ROS2/BT bring-up in conda:

```bash
python -m pip install scipy catkin_pkg empy lark
```

Verify that Python is the conda Python:

```bash
which python
python -c "import sys; print(sys.executable)"
```

Expected shape:

```text
/home/<user>/miniforge3/envs/lerobot/bin/python
```

Verify that the entry points are also from conda:

```bash
which lerobot-bt-skill-server
which lerobot-bt-skill-sim
which lerobot-bt-supervisor-server
which lerobot-bt-collaborative-runner
```

Expected shape:

```text
/home/<user>/miniforge3/envs/lerobot/bin/<entrypoint>
```

If they point to `.venv/bin`, you are not using the environment you think you are using.

Fix:

```bash
deactivate 2>/dev/null || true
conda activate lerobot
hash -r
python -m pip install -e .
```

---

## 7. BehaviorTree.CPP

The C++ runner needs BehaviorTree.CPP.

### Option A: install the ROS package

First check the package name:

```bash
source /opt/ros/jazzy/setup.bash
apt-cache search "ros-${ROS_DISTRO}-behaviortree"
```

Then install the available package, usually one of:

```bash
sudo apt install ros-${ROS_DISTRO}-behaviortree-cpp
```

or:

```bash
sudo apt install ros-${ROS_DISTRO}-behaviortree-cpp-v3
```

### Option B: build BehaviorTree.CPP from source

Use this if the ROS package is not available.

```bash
cd ~/lerobot
source /opt/ros/jazzy/setup.bash

cd src
if [ ! -d behaviortree_cpp ]; then
  git clone https://github.com/BehaviorTree/BehaviorTree.CPP.git behaviortree_cpp
fi
cd ..
```

Install dependencies if `rosdep` is available:

```bash
rosdep install --from-paths src --ignore-src -r -y
```

If `rosdep` is not available, at minimum install:

```bash
sudo apt install -y libzmq3-dev
```

Then build:

```bash
colcon build --base-paths src \
  --packages-up-to behaviortree_cpp sandwich_bt_runtime_cpp \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3

source install/setup.bash
```

If you need Groot support and BehaviorTree.CPP is built from source, make sure the Groot interface is enabled:

```bash
colcon build --base-paths src \
  --packages-up-to behaviortree_cpp sandwich_bt_runtime_cpp \
  --cmake-args \
    -DPython3_EXECUTABLE=/usr/bin/python3 \
    -DBTCPP_GROOT_INTERFACE=ON

source install/setup.bash
```

If ZeroMQ cannot be found inside a conda-heavy environment, install conda ZeroMQ packages and expose them:

```bash
conda activate lerobot
conda install -y -c conda-forge zeromq cppzmq pkg-config
export PKG_CONFIG_PATH="$CONDA_PREFIX/lib/pkgconfig:$CONDA_PREFIX/share/pkgconfig:$PKG_CONFIG_PATH"
export CMAKE_PREFIX_PATH="$CONDA_PREFIX:$CMAKE_PREFIX_PATH"
```

Then rebuild.

---

## 8. Build ROS2 Sandwich Packages

Use system Python for `colcon`. This avoids conda `catkin_pkg` and `ament` issues.

From the repository root:

```bash
cd ~/lerobot
source /opt/ros/jazzy/setup.bash

colcon build --base-paths src \
  --packages-select sandwich_bt_interfaces sandwich_bt_runtime_cpp \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3

source install/setup.bash
```

If BehaviorTree.CPP is in the same workspace as source checkout, use:

```bash
colcon build --base-paths src \
  --packages-up-to behaviortree_cpp sandwich_bt_runtime_cpp \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3

source install/setup.bash
```

Ignore warnings about old paths in `AMENT_PREFIX_PATH` or `CMAKE_PREFIX_PATH` immediately after deleting `build`, `install`, or `log`. Open a fresh terminal or re-source:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

---

## 9. Configurations

### Real robot config

Use:

```text
src/sandwich_bt_python/sandwich_bt_executor.yaml
```

Check before running on hardware:

* arm type and robot config;
* gripper type;
* camera serial numbers;
* dataset repository IDs;
* `policy.pretrained_path` for each primitive;
* recovery names;
* recovery motions;
* gripper values;
* XML retry counts;
* action semantics.

### Headless config

Use:

```text
src/sandwich_bt_python/sandwich_bt_executor_headless.yaml
```

This is for server startup without physical Panda hardware.

It should be used for:

* CI;
* headless development;
* checking that the Python server starts;
* checking that ROS2 service creation works;
* avoiding hardware-only imports during early bring-up.

Important: the headless config must still contain the same command names that the BT XML asks for. If the BT calls `recover_place_first_toast`, the config must define `recover_place_first_toast`. If it only defines `recover_test`, the C++ runner will correctly fail with `Unknown recovery 'recover_place_first_toast'`.

---

## 10. BT XML Naming Rule

In BT XML files, use `command_name`.

Correct:

```xml
<RunNamedCommand kind="skill" command_name="place_first_toast"/>
```

Wrong:

```xml
<RunNamedCommand kind="skill" name="place_first_toast"/>
```

Newer BehaviorTree.CPP versions reserve the port `name`.

---

## 11. Action Semantics

The current Panda/Robotiq config follows `cfgs/rollout_panda_robotiq.yaml`.

Current assumption:

* `arm.use_delta_actions` is not enabled;
* ACT output is interpreted as an absolute Cartesian end-effector target;
* the Panda client converts the Cartesian target to joint positions before calling the robot server.

Only enable `arm.use_delta_actions` if the checkpoint was trained with compatible delta-action semantics.

Wrong action semantics can make a valid checkpoint move the robot incorrectly.

---

## 12. Test The BT In Simulation

Use this when you want to prove that the BT orchestration works without Panda, Robotiq, cameras, or real checkpoints.

This is the fastest and safest test.

### What this test validates

It validates:

* the C++ `sandwich_bt_runner`;
* the selected BT XML file;
* `RunNamedCommand` nodes;
* `VerifySkillOutcome` nodes;
* the ROS2 `/sandwich_bt/run_command` service boundary;
* the ROS2 verification service boundary;
* command name matching;
* retry/recovery sequence;
* propagation of command `SUCCESS` / `FAILURE` back to the BT.

It does not validate:

* Panda hardware;
* gripper hardware;
* cameras;
* ACT checkpoint loading;
* learned policy quality;
* real-world motion safety.

### Terminal 1: start the mock ROS2 skill server

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash

lerobot-bt-skill-sim --ros2-service
```

Expected log:

```text
Serving mock BT commands on '/sandwich_bt/run_command'.
```

Optional check:

```bash
ros2 service list | grep sandwich
```

Expected:

```text
/sandwich_bt/run_command
```

### Terminal 2: test one BT subtree

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner --ros-args \
  -p tree_xml_path:="$(pwd)/src/sandwich_bt_runtime_cpp/trees/place_first_toast_subtree.xml"
```

Expected command path:

```text
recover_place_first_toast
place_first_toast
Behavior tree completed with SUCCESS.
```

### Terminal 2: test the full sandwich BT

```bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner
```

Expected full-tree command path:

```text
recover_place_first_toast
place_first_toast
recover_pour
pour
recover_place_second_toast
place_second_toast
Behavior tree completed with SUCCESS.
```

If this succeeds, the correct statement is:

```text
The BT works in simulation: BehaviorTree.CPP calls the ROS2 RunNamedCommand service and receives successful mock command results.
```

---

## 13. Test The BT In Real Time With The Robot Skill Server

Use this when you want the same BT orchestration to call the real Python skill server instead of the mock server.

This is the first step toward real robot execution.

### What stays the same compared to simulation

The following are unchanged:

* the C++ `sandwich_bt_runner`;
* the BT XML tree;
* `RunNamedCommand`;
* the `/sandwich_bt/run_command` service name;
* command names such as `place_first_toast` and `recover_place_first_toast`;
* BT success/failure behavior.

### What changes compared to simulation

In simulation, the service is:

```bash
lerobot-bt-skill-sim --ros2-service
```

In real-time execution, the service is:

```bash
lerobot-bt-skill-server --config_path "$(pwd)/src/sandwich_bt_python/sandwich_bt_executor.yaml"
```

The BT does not change. The backend behind `/sandwich_bt/run_command` changes.

### Required preconditions

Before starting the real skill server, verify:

* Panda server is running;
* Panda services are available;
* gripper driver is running, if configured;
* camera drivers are running, if configured;
* camera serial numbers match the YAML config;
* checkpoint paths or Hugging Face repo IDs are reachable;
* recovery motions are safe;
* robot workspace is clear;
* the YAML config contains the same skill/recovery names used in the BT XML.

### Terminal 1: start the real skill server

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash

lerobot-bt-skill-server \
  --config_path "$(pwd)/src/sandwich_bt_python/sandwich_bt_executor.yaml"
```

Expected service:

```bash
ros2 service list | grep sandwich
```

Expected output:

```text
/sandwich_bt/run_command
```

### Terminal 2: start with the smallest safe BT

Do not start with the full tree on real hardware.

Start with the first primitive tree:

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner --ros-args \
  -p tree_xml_path:="$(pwd)/src/sandwich_bt_runtime_cpp/trees/sandwich_tree_first_primitive_only.xml"
```

This requests only:

```text
recover_place_first_toast
place_first_toast
```

If this succeeds and the robot behavior is safe, then test the corresponding subtree:

```bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner --ros-args \
  -p tree_xml_path:="$(pwd)/src/sandwich_bt_runtime_cpp/trees/place_first_toast_subtree.xml"
```

Only after single-step tests are safe should you run the full tree:

```bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner
```

### Real-time success criteria

A real-time BT test is successful only if:

* the BT reaches `SUCCESS`;
* the real skill server reports command success;
* the robot motion is physically safe;
* the expected object-level effect actually happens;
* recovery motions do not create unsafe states.

A BT-level `SUCCESS` alone is not enough to claim physical task success.

---

## 14. Headless Server Startup Test

Use this to check that the real Python server can start without physical hardware.

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash

lerobot-bt-skill-server \
  --config_path "$(pwd)/src/sandwich_bt_python/sandwich_bt_executor_headless.yaml"
```

This test validates:

* Python imports;
* config parsing;
* ROS2 service creation;
* server startup path.

It does not validate:

* the BT XML;
* Panda control;
* real ACT execution;
* command names unless you actually call the server.

If you run a BT against the headless server, the headless config must define all command names requested by the BT. Otherwise the BT will correctly fail with `Unknown skill` or `Unknown recovery`.

---

## 15. Collaborative Simulation

### 15.1 Supervisor server live

Terminal 1:

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash

lerobot-bt-supervisor-server \
  --config_path "$(pwd)/src/sandwich_bt_supervisor/sandwich_bt_supervisor.yaml"
```

Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 service list | grep sandwich_supervisor
```

Expected:

```text
/sandwich_supervisor/next_action
/sandwich_supervisor/verify_step
```

### 15.2 Probe supervisor services

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash

lerobot-bt-supervisor-probe
```

Expected initial decision:

```text
step_name=place_first_toast
actor=robot
```

### 15.3 Collaborative runner with in-process robot backend

Terminal 1:

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash

lerobot-bt-supervisor-server \
  --config_path "$(pwd)/src/sandwich_bt_supervisor/sandwich_bt_supervisor.yaml"
```

Terminal 2:

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash

lerobot-bt-collaborative-runner --mock-scene
```

Expected:

```text
DONE
exit code 0
```

Negative path:

```bash
lerobot-bt-collaborative-runner --mock-scene --deny-human-confirmation
```

Expected:

```text
ABORT
exit code 1
```

### 15.4 Collaborative runner with ROS2 robot backend

Terminal 1, supervisor:

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash

lerobot-bt-supervisor-server \
  --config_path "$(pwd)/src/sandwich_bt_supervisor/sandwich_bt_supervisor.yaml"
```

Terminal 2, mock skill server:

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash

lerobot-bt-skill-sim --ros2-service
```

Terminal 3, collaborative runner:

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash

lerobot-bt-collaborative-runner --mock-scene --robot-backend ros2
```

Expected:

```text
DONE
exit code 0
```

Negative path:

```bash
lerobot-bt-collaborative-runner \
  --mock-scene \
  --robot-backend ros2 \
  --deny-human-confirmation
```

Expected:

```text
ABORT
exit code 1
```

If `/sandwich_bt/run_command` is not running, expected:

```text
exit code 2
```

---

## 16. Collaborative Runner Exit Codes

The collaborative runner uses explicit exit codes:

* `0`: task reached `DONE`;
* `1`: task aborted, failed verification, or human step denied;
* `2`: ROS2 service unavailable or timeout;
* `3`: invalid config, stale generated interfaces, invalid actor, or invalid step.

These codes are intended for CI and operator debugging.

---

## 17. Doxygen Documentation

Build docs:

```bash
bash useful_scripts/build_sandwich_bt_docs.sh
```

Output:

```text
docs/doxygen/build/html/index.html
```

If `doxygen` is missing:

```bash
sudo apt install -y doxygen graphviz
```

or:

```bash
conda install -c conda-forge doxygen graphviz
```

---

## 18. Git Hygiene

Do not commit generated build/install artifacts.

These should not be committed:

* `build/`
* `install/`
* `log/`
* `src/behaviortree_cpp/` if it is only a local dependency checkout
* generated ROS2 interface files under `install/`

If `git status` shows modified files under `install/`, ignore them.

If needed:

```bash
git restore install log
```

If local BehaviorTree.CPP checkout appears as untracked:

```bash
git status
```

Do not add it unless the project intentionally vendors BehaviorTree.CPP.

---

## 19. Common Failures

### `ModuleNotFoundError: No module named 'scipy'`

Cause:

* `scipy` is missing in the Python environment that actually runs the server.

Fix if using conda runtime:

```bash
conda activate lerobot
python -m pip install scipy
python -c "import scipy; print(scipy.__version__)"
```

Do not install into conda and then run with `uv run` if `uv run` uses `.venv`.

### `uv run python` cannot import a package that conda can import

Cause:

* `uv run` is using the repo `.venv`, not your conda env.

Fix:

```bash
conda activate lerobot
python -m pip install -e .
```

Then run entry points directly:

```bash
lerobot-bt-skill-server
```

not:

```bash
uv run lerobot-bt-skill-server
```

### `catkin_pkg` missing during `colcon build`

Cause:

* `colcon` is using conda Python, where `catkin_pkg` is missing.

Preferred fix:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --base-paths src \
  --packages-select sandwich_bt_interfaces sandwich_bt_runtime_cpp \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
```

Alternative:

```bash
conda activate lerobot
python -m pip install catkin_pkg
```

### `ModuleNotFoundError: No module named 'em'`

Cause:

* `empy` is missing.

Fix:

```bash
conda activate lerobot
python -m pip install empy
```

### `ModuleNotFoundError: No module named 'lark'`

Cause:

* ROS2 interface generation needs `lark`.

Fix:

```bash
conda activate lerobot
python -m pip install lark
```

### `install/setup.bash` is missing

Cause:

* workspace has not been built.

Fix:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --base-paths src \
  --packages-select sandwich_bt_interfaces sandwich_bt_runtime_cpp \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

### Python import error for `sandwich_bt_interfaces.srv`

Cause:

* ROS2 interfaces have not been built or sourced.

Fix:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --base-paths src --packages-select sandwich_bt_interfaces \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

### Stale generated ROS2 interfaces

Cause:

* `.srv` files changed, but the workspace was not rebuilt.

Fix:

```bash
rm -rf build/sandwich_bt_interfaces install/sandwich_bt_interfaces
source /opt/ros/jazzy/setup.bash
colcon build --base-paths src --packages-select sandwich_bt_interfaces \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

### Colcon tries to parse repository root as a Python package

Cause:

* build command was launched without limiting package discovery.

Fix:

```bash
colcon build --base-paths src ...
```

### `behaviortree_cpp` not found

Cause:

* BehaviorTree.CPP is not installed and not present in the workspace.

Fix with apt:

```bash
sudo apt install ros-${ROS_DISTRO}-behaviortree-cpp
```

or build from source:

```bash
cd ~/lerobot/src
git clone https://github.com/BehaviorTree/BehaviorTree.CPP.git behaviortree_cpp
cd ..
source /opt/ros/jazzy/setup.bash
colcon build --base-paths src \
  --packages-up-to behaviortree_cpp sandwich_bt_runtime_cpp \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

### BehaviorTree.CPP source build cannot find ZeroMQ

Fix:

```bash
sudo apt install -y libzmq3-dev
```

If building inside conda and CMake still cannot find ZeroMQ:

```bash
conda install -y -c conda-forge zeromq cppzmq pkg-config
export PKG_CONFIG_PATH="$CONDA_PREFIX/lib/pkgconfig:$CONDA_PREFIX/share/pkgconfig:$PKG_CONFIG_PATH"
export CMAKE_PREFIX_PATH="$CONDA_PREFIX:$CMAKE_PREFIX_PATH"
```

### BehaviorTree.CPP reports that port `name` is reserved

Cause:

* BT XML uses `name` as a port.

Fix:

Use `command_name`:

```xml
<RunNamedCommand kind="skill" command_name="place_first_toast"/>
```

### C++ compile warning about `async_send_request`

Warning shape:

```text
FutureAndRequestId implicit conversion is deprecated
```

This is not a blocker.

Future-safe fix in C++:

```cpp
auto future_and_request_id = client_->async_send_request(request);
future_ = future_and_request_id.future.share();
```

### C++ compile error: `request for member 'sleep' in 'rate'`

Cause:

* C++ vexing parse.

Fix:

Use brace initialization:

```cpp
rclcpp::WallRate rate{std::chrono::milliseconds(tick_ms)};
```

### `Unknown recovery 'recover_place_first_toast'`

Cause:

* the BT XML requests `recover_place_first_toast`, but the active Python config does not define it.

Fix:

Either run a config that defines it:

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/sandwich_bt_python/sandwich_bt_executor.yaml"
```

or add the recovery to the active config.

The same applies to unknown skills.

### `draccus` error: choice class for `panda` not found

Error shape:

```text
Couldn't find a choice class for 'panda' in ArmConfig
```

Cause:

* the Panda arm config class has not been registered/imported in the current runtime;
* or the YAML uses an arm type that this environment does not know;
* or the real hardware config is being used in an environment that only supports dummy/headless configs.

Immediate workaround for non-hardware testing:

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/sandwich_bt_python/sandwich_bt_executor_headless.yaml"
```

Real fix:

* make sure the Panda/CustomManipulator config module is imported before draccus parses choices;
* verify that the YAML `robot.arm.type` matches a registered `ArmConfig` choice;
* verify that the package containing the Panda config is installed in the active conda env.

### Python startup error: `No module named 'lerobot.utils.control_utils'`

Cause:

* old import path.

Fix:

Use:

```python
from lerobot.common.control_utils import is_headless
```

### Python startup error: `cannot import name 'is_offline_mode' from 'huggingface_hub'`

Cause:

* incompatible `huggingface_hub` version.

Fix:

Re-sync the Python environment using the repo dependency setup, or install the version required by this branch.

### Policy load failure

Cause:

* checkpoint path is missing;
* Hugging Face repo is unavailable;
* policy config does not match checkpoint;
* dataset metadata does not match policy expectations.

Fix:

Check:

* `dataset_repo_id`
* `policy.pretrained_path`
* local checkpoint availability
* Hugging Face credentials/network
* action and observation feature schema

### Wrong robot motion

Cause:

* checkpoint action semantics do not match runtime interpretation.

Check:

* absolute vs delta actions;
* gripper convention;
* dataset metadata;
* camera ordering;
* state normalization;
* action normalization.

---

## 20. Minimal Validation Checklist

Run these in order.

### Python imports and entry points

```bash
conda activate lerobot
cd ~/lerobot
python -m pip install -e .
which lerobot-bt-skill-server
python -c "import scipy; import catkin_pkg; import lark; print('python deps ok')"
```

### ROS2 build

```bash
source /opt/ros/jazzy/setup.bash
colcon build --base-paths src \
  --packages-select sandwich_bt_interfaces sandwich_bt_runtime_cpp \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

### Simulated BT

Terminal 1:

```bash
lerobot-bt-skill-sim --ros2-service
```

Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner
```

Expected:

```text
Behavior tree completed with SUCCESS.
```

### Real-time BT, first primitive only

Terminal 1:

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/sandwich_bt_python/sandwich_bt_executor.yaml"
```

Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner --ros-args \
  -p tree_xml_path:="$(pwd)/src/sandwich_bt_runtime_cpp/trees/sandwich_tree_first_primitive_only.xml"
```

Only after this is safe should you run the full real-time tree.

### Supervisor live

```bash
lerobot-bt-supervisor-server \
  --config_path "$(pwd)/src/sandwich_bt_supervisor/sandwich_bt_supervisor.yaml"
```

### Collaborative runner

```bash
lerobot-bt-collaborative-runner --mock-scene --robot-backend ros2
```

If all simulated tests pass, the simulated orchestration stack is working.

If real-time first-primitive tests pass safely, you can proceed toward real robot integration one primitive at a time.

---

## 21. What Is Proven And What Is Not

Proven by the current simulated setup:

* BT XML structure is valid.
* BehaviorTree.CPP runner can tick the sandwich tree.
* `RunNamedCommand` calls the ROS2 skill service.
* Mock skill server returns expected command results.
* Supervisor server exposes live ROS2 planning and verification services.
* Collaborative runner can execute robot/human/robot flow.
* Failure paths are visible through exit codes.

Not proven yet:

* Panda real hardware execution.
* Robotiq real gripper execution.
* Real camera observation processing.
* Real ACT/BC primitive performance inside the full sandwich loop.
* VLM scene estimation.
* Physical robustness of the sandwich task.

Correct claim:

```text
The simulated BT orchestration stack works end-to-end over ROS2 contracts.
The next step is replacing mock skills with real BC primitives, starting from the first ACT primitive.
```

Incorrect claim:

```text
The robot can make a sandwich autonomously.
```
