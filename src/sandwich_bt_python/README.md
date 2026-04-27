# Sandwich BT Python

Python execution layer for the sandwich BT stack.

For build/run instructions and the architecture overview, use the shared guide:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md)

## Responsibility

This package executes commands requested by the C++ BehaviorTree.CPP runtime.

It owns:

- loading skill configs from `sandwich_bt_executor.yaml`
- lazy-loading learned policy runtimes on first use
- running ACT inference on the robot
- executing scripted recoveries
- returning command results to the BT through `RunNamedCommand`

It does not own:

- BT node ordering
- retry structure
- Groot publication

Those belong to `sandwich_bt_runtime_cpp`.

## Files

- `server.py`: ROS2 service node for `/sandwich_bt/run_command`
- `executor.py`: learned skill and recovery dispatcher
- `recoveries.py`: deterministic recovery motions
- `conditions.py`: observation condition helpers for skill termination
- `config.py`: draccus config dataclasses
- `sandwich_bt_executor.yaml`: runtime config for the skill server
