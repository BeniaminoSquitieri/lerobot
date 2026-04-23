# Sandwich BT Interfaces

This package contains the ROS2 interfaces used by the sandwich Behavior Tree stack.

It exists because the system is intentionally split into two runtime layers:

- a **Python skill server** that executes ACT skills and scripted recoveries on the real robot;
- a **C++ BehaviorTree.CPP runtime** that orchestrates retries, recoveries, and Groot visualization.

Those two layers need a clean and stable contract. This package provides that contract.

## Why This Package Exists

Without a dedicated interface package, the Python and C++ sides would need to share command definitions in an ad hoc way.

That would be fragile for three reasons:

1. Python and C++ would not have a single source of truth for requests and responses.
2. ROS2 code generation would not have a dedicated package boundary.
3. Evolving the BT command API would become harder and more error-prone.

This package solves that by defining the ROS2 service used between:

- [server.py](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_python/server.py)
- [sandwich_bt_main.cpp](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_runtime_cpp/src/sandwich_bt_main.cpp)

## What Is In This Package

### `srv/RunNamedCommand.srv`

This is the only interface currently defined.

Request fields:

- `kind`
- `name`
- `timeout_s`

Response fields:

- `success`
- `status`
- `elapsed_s`
- `message`

Expected request semantics:

- `kind="skill"` means "run the named learned primitive"
- `kind="recovery"` means "run the named scripted recovery"

The `name` must match an entry configured in the Python server config:

- [sandwich_bt_executor.yaml](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_python/sandwich_bt_executor.yaml)

## What This Package Does Not Do

This package does **not**:

- execute any policy;
- connect to the robot;
- define any BT logic;
- talk to Groot directly.

It only defines the ROS2 service contract.

## How To Build It

From the repository root:

```bash
colcon build --packages-select sandwich_bt_interfaces
source install/setup.bash
```

In practice, you will usually build it together with the C++ BT runtime:

```bash
colcon build --packages-select sandwich_bt_interfaces sandwich_bt_runtime_cpp
source install/setup.bash
```

## How To Use It

You do not run this package directly.

It is used indirectly by:

- the Python ROS2 skill server in [server.py](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_python/server.py)
- the C++ BT runtime in [run_named_command_node.cpp](/home/bsquitieri-iit.local/lerobot/src/sandwich_bt_runtime_cpp/src/run_named_command_node.cpp)

The only operational requirement is:

- this package must be built;
- the ROS2 workspace must be sourced before launching the server or the BT runtime.

## Typical Failure If It Is Missing

If this package is not built or the workspace is not sourced:

- the Python server will fail to import `sandwich_bt_interfaces.srv`
- the C++ BT runtime will not build or run correctly

## Summary

This package exists to keep the Python execution layer and the C++ BT layer decoupled and cleanly integrated through one ROS2 service definition.
