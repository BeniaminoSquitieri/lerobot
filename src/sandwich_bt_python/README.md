# Sandwich BT Python Package

This package is the Python side of a hybrid runtime for the real Panda.

The other created packages now have their own dedicated READMEs:

- [sandwich_bt_interfaces/README.md](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_interfaces/README.md)
- [sandwich_bt_runtime_cpp/README.md](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_runtime_cpp/README.md)

This README focuses on the Python package only.

The full system is:

- **Behavior Tree orchestration in C++**
- **skill execution in Python**
- **Groot visualization for the BT**

The previous linear Python sequence runner has been removed. The current architecture is built around:

1. a Python ROS2 server that can execute:
   - one ACT skill at a time,
   - one scripted recovery at a time;
2. a C++ ROS2 package using BehaviorTree.CPP;
3. a BT XML tree that retries skills and runs recoveries between attempts;
4. Groot visualization on the C++ BT side.

Important terminology:

- **`groot` policy in LeRobot** is the GR00T policy family.
- **Groot GUI** here means the BehaviorTree.CPP visualization tool.

They are unrelated.

## Architecture

The runtime is split in two layers.

### Python Layer

The Python layer owns:

- `CustomManipulator`
- skill checkpoints
- LeRobot pre/post-processors
- dataset metadata
- scripted recoveries

It exposes a ROS2 service:

- `/sandwich_bt/run_command`

The service accepts commands of two kinds:

- `skill`
- `recovery`

Examples:

- run skill `place_first_toast`
- run recovery `recover_place_first_toast`

### C++ Layer

The C++ layer owns:

- the Behavior Tree
- retry and fallback logic
- integration with Groot

The BT never runs ACT directly. It calls the Python service, waits for the result, and transitions the tree according to:

- `SUCCESS`
- `FAILURE`

This is the key separation of concerns:

- Python handles robot-facing policy execution
- C++ handles orchestration and recovery logic

## File Overview

### Python package: `src/sandwich_bt_python`

#### `config.py`

Defines the server-side configuration model.

Main classes:

- `ObservationConditionConfig`
  Condition definition for skill completion and failure checks.

- `SkillTransitionConfig`
  Transition policy for a single skill:
  - `timeout`
  - `all_conditions`
  - `all_conditions_or_timeout`

- `PrimitiveSkillConfig`
  Defines one ACT skill:
  - dataset metadata source
  - checkpoint
  - task string
  - transition rule

- `RecoveryStepConfig`
  Defines one scripted recovery step.
  Supported step kinds:
  - `pause`
  - `robot_reset`
  - `cartesian_delta`
  - `set_gripper`

- `RecoveryConfig`
  Defines a named recovery as a sequence of recovery steps.

- `SkillCommandServerConfig`
  Root configuration for the Python ROS2 server.

#### `conditions.py`

Evaluates observation-based conditions on processed observations.

Used by the Python skill executor to decide whether a skill is:

- `RUNNING`
- `SUCCESS`
- `FAILURE`

#### `recoveries.py`

Implements scripted recoveries.

Current supported primitives:

- pause for a fixed duration
- reset the robot
- send a Cartesian delta motion
- set the gripper command directly

This layer is intentionally deterministic. It is meant to change the context before retrying a learned primitive.

#### `executor.py`

Implements the core execution backend.

Responsibilities:

- preload all skills
- load dataset metadata and processor stats
- reset policy state before each attempt
- execute one named skill
- execute one named recovery
- serialize access to the robot with a command lock

This file contains the actual robot-facing ACT execution loop.

#### `server.py`

Runs the Python ROS2 service server.

Responsibilities:

- parse [sandwich_bt_executor.yaml](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_python/sandwich_bt_executor.yaml)
- initialize `CustomManipulator`
- build robot processors
- instantiate the execution backend
- expose the ROS2 service `/sandwich_bt/run_command`

This is the entrypoint you launch before starting the BT.

### Python config: `src/sandwich_bt_python/sandwich_bt_executor.yaml`

This is the Python server configuration.

It defines:

- robot configuration
- skill list
- recovery list
- processor configuration
- service name

The three skills currently configured are:

- `place_first_toast`
- `pour`
- `place_second_toast`

The three recoveries currently configured are:

- `recover_place_first_toast`
- `recover_pour`
- `recover_place_second_toast`

## Why These Python Files Still Exist

Yes, the Python files are still necessary.

They are not the old sequence runner anymore. They now serve a different role:

- `server.py`
  Exposes a ROS2 service for the BT.

- `executor.py`
  Runs one ACT primitive on the real robot.

- `recoveries.py`
  Runs deterministic recoveries between BT attempts.

- `config.py` and `conditions.py`
  Define the configuration and success/failure logic used by the skill server.

So the separation is now:

- **BT logic**: separate ROS2 packages
  - [sandwich_bt_interfaces](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_interfaces/package.xml)
  - [sandwich_bt_runtime_cpp](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_runtime_cpp/package.xml)
- **robot-facing skill execution**: this Python package
  - [sandwich_bt_python](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_python/server.py)

This split is intentional. The BT should decide *what* to run and *when* to retry. The Python package should execute the actual learned skill on the robot.

### ROS2 interface package: `src/sandwich_bt_interfaces`

This package defines the ROS2 service interface used between C++ and Python.

#### `srv/RunNamedCommand.srv`

Request:

- `kind`
- `name`
- `timeout_s`

Response:

- `success`
- `status`
- `elapsed_s`
- `message`

This is the only contract needed between the BT and the Python executor.

### ROS2 C++ package: `src/sandwich_bt_runtime_cpp`

This package contains the BehaviorTree.CPP runtime.

#### `include/sandwich_bt_runtime_cpp/run_named_command_node.hpp`

Declares the custom BT action node that calls the ROS2 service.

#### `src/run_named_command_node.cpp`

Implements the asynchronous BT action node.

The node:

1. starts a service call on first tick;
2. returns `RUNNING` while waiting;
3. returns `SUCCESS` or `FAILURE` when the service completes.

#### `src/sandwich_bt_main.cpp`

Main entrypoint for the C++ BT runner.

Responsibilities:

- initialize ROS2
- load the BT XML
- register the custom node type
- start the Groot publisher if available
- tick the tree until completion

#### `trees/sandwich_tree.xml`

Default sandwich tree.

The current tree structure is:

- retry `place_first_toast` up to 3 times, with a recovery before each attempt;
- retry `pour` up to 2 times, with a recovery before each attempt;
- retry `place_second_toast` up to 3 times, with a recovery before each attempt.

This is intentionally minimal but already useful:

- it retries failed ACT primitives;
- it inserts scripted recoveries between attempts;
- it stays visible in Groot.

## Why This Architecture

This design was chosen because the requirement is:

- real BT logic
- recovery support
- retry support
- Groot visualization

If you only needed a fixed sequence, Python alone would be enough.

Once recovery logic becomes a real requirement, BT orchestration is the right level for:

- retry policies
- fallback logic
- future branching
- GUI visibility in Groot

At the same time, re-implementing ACT execution in C++ would be unnecessary and fragile, because the entire policy stack already exists in Python.

So the architecture is deliberately hybrid.

## Preconditions

Before running this stack on the real Panda, all of the following must be true.

### Robot And ROS2

- The Panda ROS2 services used by the manipulator client must be available.
- The Robotiq gripper topics must be active:
  - `/gripper/stat`
  - `/gripper/cmd`
- The RealSense cameras configured in [sandwich_bt_executor.yaml](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_python/sandwich_bt_executor.yaml) must be connected with the correct serial numbers.
- The workspace must be safe for repeated retries and scripted recoveries.

### Skill Checkpoints

Each configured skill must have:

- a valid `dataset_repo_id`
- a valid `policy.pretrained_path`

These must match semantically.

In particular, the action semantics must match the runtime setup.

The current robot config uses:

- `arm.use_delta_actions: true`

So the ACT checkpoints should have been trained with compatible delta-action semantics. If they were trained on absolute actions, runtime behavior will be semantically wrong even if tensor shapes still match.

### ROS2 Build

Before launching the system, the ROS2 packages in this repository must be built:

- [package.xml](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_interfaces/package.xml)
- [package.xml](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_runtime_cpp/package.xml)

From the repository root:

```bash
colcon build --packages-select sandwich_bt_interfaces sandwich_bt_runtime_cpp
source install/setup.bash
```

This step is required so that:

- the Python server can import `sandwich_bt_interfaces.srv`
- the C++ BT runner can link against the service interface package

The C++ package CMake is written to accept either `behaviortree_cpp` or `behaviortree_cpp_v3`. If your ROS2 distribution only ships the `v3` package name, you may need to adjust the dependency name in [package.xml](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_runtime_cpp/package.xml) to match your system.

### Python Environment

The Python environment must have the LeRobot repo installed and the runtime dependencies available, including:

- `draccus`
- `rclpy`
- ACT policy dependencies
- robot-specific dependencies

If needed:

```bash
pip install -e .
```

## Configuration

Edit [sandwich_bt_executor.yaml](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_python/sandwich_bt_executor.yaml) before the first real test.

At minimum, replace:

- the three `dataset_repo_id` placeholders
- the three `policy.pretrained_path` values
- camera serial numbers if needed

You should also review the recoveries.

The current recoveries are only default placeholders. They are useful for bring-up, but they are not guaranteed to be optimal for your task.

In particular, check:

- `gripper_value` semantics for your setup
- Cartesian backoff magnitudes
- retry counts in [sandwich_tree.xml](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_runtime_cpp/trees/sandwich_tree.xml)

## How To Run

The runtime requires two processes.

### 1. Start the Python skill server

After building the ROS2 packages and sourcing the workspace:

```bash
source install/setup.bash
lerobot-bt-skill-server
```

This starts the Python ROS2 service server and connects to the real robot.

### 2. Start the C++ BT runner

In another shell:

```bash
source install/setup.bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner
```

This starts the BehaviorTree.CPP runtime and executes the XML tree.

### 3. Open Groot

If BehaviorTree.CPP in your environment provides a compatible Groot publisher, the BT will be visible in Groot.

The C++ runner already attempts to enable the publisher automatically when the relevant BT.CPP publisher header is available.

## What Happens During Execution

For one BT leaf node:

1. the BT node sends a ROS2 service request;
2. the Python server receives a command like:
   - `kind=skill`, `name=place_first_toast`
   - or `kind=recovery`, `name=recover_place_first_toast`
3. the Python backend executes the command on the robot;
4. the backend returns:
   - success/failure
   - elapsed time
   - message
5. the BT node converts that into:
   - `SUCCESS`
   - `FAILURE`
6. the tree proceeds according to the retry/fallback structure.

## Current BT Behavior

The default BT is conservative and simple.

For each primitive:

- run a recovery first;
- run the ACT skill;
- if the skill fails, retry according to the XML.

This means the BT does not tell ACT how to act differently. Instead it changes the context before each new attempt.

That is exactly the intended use:

- the policy remains learned;
- the BT handles orchestration and recovery.

## Common Failure Modes

### ROS2 packages not built

Symptom:

- the Python server cannot import `sandwich_bt_interfaces.srv`
- `ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner` is not available

Cause:

- `colcon build` was not run, or `install/setup.bash` was not sourced

### Checkpoint and dataset mismatch

Symptom:

- the skill server starts, but policy execution behaves incorrectly or fails in processor setup

Cause:

- checkpoint and dataset metadata do not match

### Wrong action semantics

Symptom:

- the robot moves, but in a clearly wrong or unstable way

Cause:

- the checkpoint was trained on absolute actions while runtime expects delta actions, or vice versa

### Recovery is ineffective

Symptom:

- retries keep reproducing the same failure

Cause:

- the recovery does not sufficiently change the context before the next ACT attempt

This is the main reason to keep recovery logic explicit and editable in the YAML and XML.

## Recommended Next Steps

Once the basic stack is running, the next useful improvements are:

1. refine the recovery scripts for each primitive;
2. replace timeout-only success logic with observation-based success checks where possible;
3. add fallback branches in the BT instead of only retries;
4. add dedicated recoveries for different failure categories instead of a single recovery per skill.
