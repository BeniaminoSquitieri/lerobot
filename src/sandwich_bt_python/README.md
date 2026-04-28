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

## Python Files

- `__init__.py`: package export surface for the public config dataclasses
- `config.py`: draccus config dataclasses for skills, recoveries, and the server
- `conditions.py`: helpers that evaluate observation-based success and failure checks
- `executor.py`: learned skill and recovery dispatcher used by the server
- `recoveries.py`: deterministic recovery motions executed between BT attempts
- `server.py`: ROS2 service node for `/sandwich_bt/run_command`
- `simulation.py`: hardware-free mock robot plus an optional ROS2 service harness for local smoke tests

## Runtime Config

- `sandwich_bt_executor.yaml`: runtime config loaded by `server.py`
