# lerobot

This directory is the LeRobot Python library. It contains the reusable robot
learning stack: datasets, policies, processors, robot abstractions, scripts,
training, evaluation, and hardware integrations.

Keep this directory focused on reusable LeRobot functionality. The behavior
tree orchestration for the Panda tasks lives in sibling packages:

- `../lerobot_bt_python` owns the ROS 2 Python skill server and task executor
  YAML files.
- `../lerobot_bt_runtime_cpp` owns BehaviorTree.CPP XML trees, launch files,
  and the C++ runner.
- `../lerobot_bt_interfaces` owns the ROS 2 service contracts between the C++
  runner and Python server.

## What Lives Here

| Area | Purpose |
| --- | --- |
| `policies/` | Policy implementations and configs such as ACT, Diffusion, SmolVLA, GROOT, Pi0, and others. |
| `datasets/` | `LeRobotDataset`, metadata handling, video/image decoding, and dataset tooling. |
| `processor/` | Processor pipelines and registry used to transform observations/actions before policy or robot calls. |
| `robots/` | Robot backends. The Panda/Robotiq custom manipulator used by the BT stack lives under `robots/custom_manipulator/`. |
| `scripts/` | Generic LeRobot CLI entrypoints such as record, train, eval, replay, teleoperate, and camera discovery. |
| `configs/` | Dataclass configs parsed by draccus. |

## Relationship With The BT Stack

The BT stack should call LeRobot through public APIs instead of duplicating
robot-learning logic.

The current Panda task path is:

```text
lerobot_bt_runtime_cpp
  -> ROS 2 RunNamedCommand
  -> lerobot_bt_python.server
  -> lerobot_bt_python.executor
  -> lerobot policies/processors/robots
```

Important integration points:

- `robots/custom_manipulator/custom_manipulator.py` exposes the Panda +
  Robotiq robot object used by the Python skill server.
- `robots/custom_manipulator/arms/panda.py` sends Cartesian targets through
  IK to the Panda service backend.
- `robots/custom_manipulator/processor/safety_processor.py` provides
  `cartesian_action_safety_processor`, used by BT executor YAML to reject or
  clip large Cartesian jumps before hardware commands.
- `processor/` provides `RobotProcessorPipeline` and the processor registry
  used by `../lerobot_bt_python/processor_factory.py`.

## Commands

Operational commands for setup, generic LeRobot tools, and the BT/Panda stack
are centralized in `../README.md`.
