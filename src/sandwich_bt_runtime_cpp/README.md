# Sandwich BT Runtime C++

This package contains the BehaviorTree.CPP runtime for the sandwich task.

It exists because the requirement is not just "run three skills in order", but:

- use a real Behavior Tree;
- support retries and recoveries;
- keep the BT visible in Groot.

That combination is why the BT layer is implemented in C++ with BehaviorTree.CPP, while the
robot-facing ACT execution remains in Python.

## Why This Package Exists

The Python side already has everything needed to execute ACT skills on the real Panda:

- robot connection;
- policy loading;
- pre/post-processing;
- action execution;
- scripted recovery motions.

What Python does not give you naturally in this repo is a standard BT runtime integrated with
Groot.

This package solves that by providing:

- a BehaviorTree.CPP executable;
- a custom BT node that calls the Python ROS2 service;
- a default XML tree for the sandwich task;
- optional Groot publisher support when the installed BehaviorTree.CPP version provides it.

## What Is In This Package

### `include/sandwich_bt_runtime_cpp/run_named_command_node.hpp`

Declares the custom BT action node used by the tree.

This node is a thin wrapper around the ROS2 service defined in:

- [`../sandwich_bt_interfaces/srv/RunNamedCommand.srv`](../sandwich_bt_interfaces/srv/RunNamedCommand.srv)

### `src/run_named_command_node.cpp`

Implements the BT node.

Behavior:

1. on first tick, it sends a ROS2 service request;
2. while waiting, it returns `RUNNING`;
3. when the service finishes, it returns:
   - `SUCCESS` if the Python server reports success
   - `FAILURE` otherwise

This is the bridge between the BT and the Python skill server.

### `src/sandwich_bt_main.cpp`

Main executable for the BT runtime.

Responsibilities:

- initialize ROS2;
- load the BT XML file;
- register `RunNamedCommand`;
- start Groot publishing if supported by the installed BT.CPP version;
- tick the tree until it returns `SUCCESS` or `FAILURE`.

### `trees/sandwich_tree.xml`

Default tree for the sandwich task.

Current structure:

- retry `place_first_toast` up to 3 times;
- retry `pour` up to 2 times;
- retry `place_second_toast` up to 3 times;
- before each skill attempt, run the corresponding recovery action.

This gives you a minimal but useful recovery strategy from day one.

## What This Package Does Not Do

This package does not:

- load ACT checkpoints;
- control the Panda directly;
- evaluate skill success from raw robot observations;
- implement the actual recoveries.

Those responsibilities stay on the Python side in:

- [`../sandwich_bt_python/server.py`](../sandwich_bt_python/server.py)
- [`../sandwich_bt_python/executor.py`](../sandwich_bt_python/executor.py)
- [`../sandwich_bt_python/recoveries.py`](../sandwich_bt_python/recoveries.py)

This separation is intentional:

- C++ owns BT orchestration
- Python owns learned skill execution

## Dependencies

This package depends on:

- ROS2
- `rclcpp`
- `ament_index_cpp`
- `sandwich_bt_interfaces`
- `BehaviorTree.CPP`

The CMake is written to accept either:

- `behaviortree_cpp`
- or `behaviortree_cpp_v3`

depending on what your ROS2 distribution ships.

If your system only provides the `v3` package name, you may need to align the dependency name in:

- [`package.xml`](package.xml)

## How To Build It

From the repository root:

```bash
colcon build --packages-select sandwich_bt_interfaces sandwich_bt_runtime_cpp
source install/setup.bash
```

## How To Run It

This package is not standalone. The Python skill server must already be running.

### 1. Start the Python skill server

In one terminal:

```bash
source install/setup.bash
lerobot-bt-skill-server
```

### 2. Start the BT runtime

In another terminal:

```bash
source install/setup.bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner
```

## Groot Visibility

This package is the one responsible for Groot visibility.

If the installed BehaviorTree.CPP version provides a compatible publisher header, the executable
will create a publisher automatically.

The code handles both common header layouts:

- `groot2_publisher.h`
- `bt_zmq_publisher.h`

If neither is available, the BT still runs, but Groot visualization is disabled and a warning is
logged.
