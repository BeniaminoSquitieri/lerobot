# Sandwich BT Stack

This is the single operational guide for the sandwich Behavior Tree stack.

## Ownership

The base stack has three runtime packages with separate responsibilities:

- `sandwich_bt_runtime_cpp`: owns BehaviorTree.CPP orchestration, XML loading, retries, and Groot publication.
- `sandwich_bt_python`: owns robot connection, learned policy execution, scripted recoveries, and command results.
- `sandwich_bt_interfaces`: owns the ROS2 service contract between the two runtime layers.

The Python package does not implement BT ordering. The C++ package does not load policies or command the robot directly.

For collaborative execution there is now a fourth Python package:

- `sandwich_bt_supervisor`: owns closed-set scene-state estimation, task allocation, human handoff, and step verification above the BT/runtime boundary.

## Runtime Flow

1. The C++ runner loads a BT XML file.
2. A `RunNamedCommand` BT leaf sends a ROS2 service request.
3. The Python server receives `kind`, `name`, and optional `timeout_s`.
4. The Python executor runs either one learned skill or one scripted recovery.
5. The Python server returns `success`, `status`, `elapsed_s`, and `message`.
6. The C++ BT converts that reply into BT `SUCCESS` or `FAILURE`.

## Collaborative Flow

The collaborative path keeps the BT reactive and moves step selection above it:

1. `sandwich_bt_supervisor` estimates the current sandwich state.
2. The supervisor picks the next closed-set step and assigns it to `robot` or `human`.
3. Robot-owned steps execute through small BT subtrees, which keep recovery and retry logic below the supervisor.
4. Human-owned steps require explicit confirmation and then scene verification.
5. After each step, the supervisor checks the scene again and decides the next handoff.

## Key Files

- Full tree: `src/sandwich_bt_runtime_cpp/trees/sandwich_tree.xml`
- First-primitive test tree: `src/sandwich_bt_runtime_cpp/trees/sandwich_tree_first_primitive_only.xml`
- Robot step subtrees:
  - `src/sandwich_bt_runtime_cpp/trees/place_first_toast_subtree.xml`
  - `src/sandwich_bt_runtime_cpp/trees/pour_subtree.xml`
  - `src/sandwich_bt_runtime_cpp/trees/place_second_toast_subtree.xml`
- Python config: `src/sandwich_bt_python/sandwich_bt_executor.yaml`
- Supervisor config: `src/sandwich_bt_supervisor/sandwich_bt_supervisor.yaml`
- ROS2 service: `src/sandwich_bt_interfaces/srv/RunNamedCommand.srv`
- Supervisor services:
  - `src/sandwich_bt_interfaces/srv/PlanNextStep.srv`
  - `src/sandwich_bt_interfaces/srv/VerifyStep.srv`
- Python server: `src/sandwich_bt_python/server.py`
- Python executor: `src/sandwich_bt_python/executor.py`
- Supervisor planner: `src/sandwich_bt_supervisor/vlm_supervisor.py`
- Supervisor server: `src/sandwich_bt_supervisor/server.py`
- C++ runner: `src/sandwich_bt_runtime_cpp/src/sandwich_bt_main.cpp`
- C++ BT leaf: `src/sandwich_bt_runtime_cpp/src/run_named_command_node.cpp`

## Build

From the repository root:

Quick bootstrap (recommended on fresh machines after `conda activate <env>`):

```bash
bash useful_scripts/bootstrap_sandwich_bt.sh
```

Useful variants:

```bash
# no apt step (if system deps already present)
bash useful_scripts/bootstrap_sandwich_bt.sh --skip-apt

# full Python stack from requirements-ubuntu.txt
bash useful_scripts/bootstrap_sandwich_bt.sh --full-python
```

Install BehaviorTree.CPP for your ROS distro if it is not already available:

```bash
apt-cache search "ros-${ROS_DISTRO}-behaviortree"
sudo apt install ros-${ROS_DISTRO}-behaviortree-cpp
```

Some ROS distributions package it as `behaviortree-cpp-v3` instead:

```bash
sudo apt install ros-${ROS_DISTRO}-behaviortree-cpp-v3
```

If `apt-cache search` returns no BehaviorTree.CPP package for your ROS/Ubuntu combination,
build BehaviorTree.CPP from source in the same workspace:

```bash
sudo apt install libzmq3-dev
cd src
git clone https://github.com/BehaviorTree/BehaviorTree.CPP.git behaviortree_cpp
cd ..
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --packages-up-to behaviortree_cpp sandwich_bt_runtime_cpp
source install/setup.bash
```

If `rosdep` is not installed, this stack can still be built by installing the missing system
dependencies manually. For BehaviorTree.CPP with Groot support, the important one is:

```bash
sudo apt install libzmq3-dev
```

When building from a conda environment (for example `lerobot_ben`), CMake may fail to resolve
ZeroMQ even if `libzmq3-dev` is installed system-wide. In that case, install and expose the
conda-provided artifacts before running `colcon`:

```bash
conda activate lerobot_ben
conda install -y -c conda-forge zeromq cppzmq pkg-config
export PKG_CONFIG_PATH="$CONDA_PREFIX/lib/pkgconfig:$CONDA_PREFIX/share/pkgconfig:$PKG_CONFIG_PATH"
export CMAKE_PREFIX_PATH="$CONDA_PREFIX:$CMAKE_PREFIX_PATH"
colcon build --base-paths src --packages-up-to behaviortree_cpp sandwich_bt_runtime_cpp --cmake-clean-cache
```

If you only need to execute the BT and do not need Groot support, ZeroMQ can be avoided by
disabling the BehaviorTree.CPP Groot interface:

```bash
colcon build --base-paths src --packages-up-to behaviortree_cpp sandwich_bt_runtime_cpp \
  --cmake-clean-cache \
  --cmake-args -DBTCPP_GROOT_INTERFACE=OFF -DBTCPP_BUILD_TOOLS=OFF -DBTCPP_EXAMPLES=OFF -DBUILD_TESTING=OFF
```

Then build the BT packages:

```bash
colcon build --base-paths src --packages-select sandwich_bt_interfaces sandwich_bt_runtime_cpp
source install/setup.bash
```

The Python package must be importable in the active environment. If needed:

```bash
pip install -e .
```

## Configuration

Edit `src/sandwich_bt_python/sandwich_bt_executor.yaml` before running on the real robot.

Check:

- camera serial numbers
- `dataset_repo_id` for each trained primitive
- `policy.pretrained_path` for each trained primitive
- recovery motions and gripper values
- retry counts in the XML tree

In BT XML files, `RunNamedCommand` uses `command_name` for the skill or recovery name.
Do not use a BT port called `name`, because newer BehaviorTree.CPP versions reserve it.

Skills are loaded lazily when the BT first requests them. This means unused placeholders for later sandwich primitives do not block a first-primitive bring-up run.

## Action Semantics

The current Panda/Robotiq config follows `cfgs/rollout_panda_robotiq.yaml`:

- `arm.use_delta_actions` is not enabled
- the ACT output is interpreted as an absolute Cartesian end-effector target
- the Panda client converts the Cartesian target to joint positions before calling the robot server

Only enable `arm.use_delta_actions` if the checkpoint was trained with compatible delta-action semantics.

## Runtime Presteps

Before starting the sandwich BT stack on the real robot, these processes/devices must already be available:

- the Panda robot server must be running and providing `panda_interface` services:
  - `/connect`
  - `/get_sensors`
  - `/apply_commands`
  - `/close`
- the Robotiq driver must be running if `robot.gripper.type: robotiq` is used:
  - publishes `/gripper/stat`
  - accepts commands on `/gripper/cmd`
- the RealSense cameras listed in `sandwich_bt_executor.yaml` must be connected with the configured serial numbers
- the conda env must be active, the repo editable install must be current, and `install/setup.bash` must be sourced
- the trained policy checkpoint must be reachable locally or from Hugging Face Hub
- the robot workspace must be safe for the startup reset and retry/recovery motions

Launch order:

1. Start the Panda server and gripper/camera drivers.
2. Start `lerobot-bt-skill-server`; this connects to the robot and exposes `/sandwich_bt/run_command`.
3. Start `sandwich_bt_runner`; this ticks the BT and calls the Python service.

With `reset_robot_on_startup: true`, the Python skill server resets the robot as soon as it connects.

## Run The Full Tree

Terminal 1:

```bash
source install/setup.bash
lerobot-bt-skill-server --config_path "$(pwd)/src/sandwich_bt_python/sandwich_bt_executor.yaml"
```

Terminal 2:

```bash
source install/setup.bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner
```

This runs `sandwich_tree.xml`, which executes:

1. `recover_place_first_toast`, then `place_first_toast`
2. `recover_pour`, then `pour`
3. `recover_place_second_toast`, then `place_second_toast`

## Run Only The First Primitive

Use this when only `place_first_toast` is trained and available.

Terminal 1:

```bash
source install/setup.bash
lerobot-bt-skill-server --config_path "$(pwd)/src/sandwich_bt_python/sandwich_bt_executor.yaml"
```

Terminal 2:

```bash
source install/setup.bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner --ros-args \
  -p tree_xml_path:="$(pwd)/src/sandwich_bt_runtime_cpp/trees/sandwich_tree_first_primitive_only.xml"
```

This tree requests only:

1. `recover_place_first_toast`
2. `place_first_toast`

## Hardware-Free Simulation

If you only want to exercise the named-command flow without ROS2 hardware, use the in-process mock
service:

```bash
uv run lerobot-bt-skill-sim
```

You can also pass explicit commands:

```bash
uv run lerobot-bt-skill-sim \
  --command recovery:recover_place_first_toast \
  --command skill:place_first_toast
```

This path does not talk to Panda, Robotiq, or the C++ BT runner. It is meant for smoke-testing the
Python command dispatch and recovery logic.

To exercise the minimal collaborative loop on top of that same mock execution backend:

```bash
uv run lerobot-bt-supervisor-sim
```

That simulation runs the closed-set sequence:

1. robot subtree `place_first_toast_subtree.xml`
2. human `pour_ingredient`
3. robot subtree `place_second_toast_subtree.xml`

and exits when the supervisor reaches `DONE`.

For the negative path:

```bash
uv run lerobot-bt-supervisor-sim --deny-human-confirmation
```

Recommended validation order:

1. `uv run lerobot-bt-skill-sim`
2. `uv run lerobot-bt-supervisor-sim`
3. `uv run lerobot-bt-supervisor-sim --deny-human-confirmation`
4. `colcon build --base-paths src --packages-select sandwich_bt_interfaces && source install/setup.bash`
5. `uv run lerobot-bt-supervisor-server` plus `uv run lerobot-bt-supervisor-probe`
6. `uv run lerobot-bt-supervisor-server` plus `uv run lerobot-bt-collaborative-runner --mock-scene`
7. `uv run lerobot-bt-supervisor-server` plus `uv run lerobot-bt-skill-sim --ros2-service` plus `uv run lerobot-bt-collaborative-runner --mock-scene --robot-backend ros2`
8. `lerobot-bt-skill-sim --ros2-service` plus `ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner`

If the interfaces build fails in a conda environment with `ModuleNotFoundError: catkin_pkg`, rerun step 4 as:

```bash
colcon build --base-paths src --packages-select sandwich_bt_interfaces \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

The collaborative runner uses these exit codes:

- `0`: `DONE`
- `1`: task abort / verification failure
- `2`: ROS2 supervisor service or `/sandwich_bt/run_command` unavailable
- `3`: invalid config or stale generated interfaces

## BT Simulation

To run the C++ BT runner against the mock ROS2 service, first build the workspace from the
repository root. On a fresh machine, the bootstrap script is the shortest path:

```bash
conda activate lerobot
bash useful_scripts/bootstrap_sandwich_bt.sh
```

That step creates `install/setup.bash` and installs `lerobot-bt-skill-sim` into the active conda
environment.

Then start the simulated service in one terminal:

```bash
source install/setup.bash
lerobot-bt-skill-sim --ros2-service
```

Then start the runner in another terminal:

```bash
source install/setup.bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner --ros-args \
  -p tree_xml_path:="$(pwd)/src/sandwich_bt_runtime_cpp/trees/sandwich_tree_first_primitive_only.xml"
```

If you want the full tree instead of the one-primitive smoke test, omit `tree_xml_path` and keep the
default `sandwich_tree.xml`.

The BT XML, service name, and request fields are the same as in the real-robot flow. What changes is
the Python side: `lerobot-bt-skill-sim --ros2-service` exposes a mock command handler, while
`lerobot-bt-skill-server` connects to the actual robot, cameras, and trained checkpoints. So the BT
orchestration is the same, but the underlying robot behavior is not a physics-level guarantee.

## Groot

The C++ runner enables a Groot publisher when the installed BehaviorTree.CPP version provides a compatible publisher header.

If no compatible publisher is available, the BT still runs and the runner logs a warning.

## Common Failures

- `ModuleNotFoundError: No module named 'em'` while building `sandwich_bt_interfaces`: install `empy` in the active conda env, or rerun `bash useful_scripts/bootstrap_sandwich_bt.sh` so it installs the missing ROS interface dependency automatically.
- `Package 'behaviortree_cpp' specified with --packages-up-to was not found`: rerun the updated bootstrap script; it now builds only the local sandwich packages and includes a BehaviorTree.CPP source checkout only if one exists in `src/`.
- `install/setup.bash` is missing: build the workspace first with `bash useful_scripts/bootstrap_sandwich_bt.sh`, then source the overlay.
- `lerobot-bt-skill-sim` is not found: make sure the conda env is active and the bootstrap script has been run, or use `uv run lerobot-bt-skill-sim --ros2-service`.
- Service unavailable: start `lerobot-bt-skill-server` before the C++ runner.
- Python import error for `sandwich_bt_interfaces.srv`: build and source the ROS2 workspace.
- Colcon tries to parse the repository root as a Python package: build with `--base-paths src`.
- CMake cannot find `behaviortree_cpp` or `behaviortree_cpp_v3`: install the BehaviorTree.CPP ROS package for your distro, or build BehaviorTree.CPP from source if apt has no package for your ROS/Ubuntu combination.
- BehaviorTree.CPP source build cannot find `ZeroMQ`: install `libzmq3-dev`, or disable `BTCPP_GROOT_INTERFACE` if Groot is not needed.
- CMake reports `Could NOT find ZeroMQ (missing: ZeroMQ_LIBRARIES)` in conda builds: install `zeromq`, `cppzmq`, and `pkg-config` in the active conda env, then export `PKG_CONFIG_PATH` and `CMAKE_PREFIX_PATH` from `CONDA_PREFIX` before `colcon build`.
- BehaviorTree.CPP reports that port `name` is reserved: use `command_name` in `RunNamedCommand` XML nodes.
- C++ compile error `request for member 'sleep' in 'rate'`: use brace initialization in the runner (`rclcpp::WallRate rate{std::chrono::milliseconds(tick_ms)};`) to avoid vexing-parse issues.
- Python startup error `ModuleNotFoundError: No module named 'lerobot.utils.control_utils'`: import `is_headless` from `lerobot.common.control_utils`.
- Python startup error `cannot import name 'is_offline_mode' from 'huggingface_hub'`: the Python env has incompatible package versions; re-sync dependencies with the repository lock setup (`uv sync --locked ...`) before running the server.
- Unknown skill or recovery: the XML `command_name` does not match an entry in `sandwich_bt_executor.yaml`.
- Policy load failure: the requested skill points to a missing or incompatible checkpoint.
- Wrong robot motion: action semantics or dataset metadata do not match the checkpoint.
