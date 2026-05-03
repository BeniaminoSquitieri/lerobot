# Sandwich BT Stack Documentation {#mainpage}

This documentation describes the sandwich Behavior Tree stack used to test long-horizon robot manipulation with simulated and real Behavior Cloning primitives.

## Current validated status

Validated:
- BehaviorTree.CPP runner against mock ROS2 skill server.
- Full sandwich XML tree against `/sandwich_bt/run_command`.
- Supervisor ROS2 server live.
- Collaborative runner live.
- Human success and abort paths.
- ROS2-backed `RunNamedCommand` backend.
- Mock skill server.

Not yet validated:
- Panda real hardware execution.
- Full sandwich loop with real ACT/BC checkpoints.
- Live VLM scene estimator.

## Runtime layers

- `sandwich_bt_runtime_cpp`: BehaviorTree.CPP orchestration, XML loading, retries, Groot publication.
- `sandwich_bt_python`: robot connection, learned policy execution, scripted recoveries, command results.
- `sandwich_bt_interfaces`: ROS2 service contracts.
- `sandwich_bt_supervisor`: collaborative task allocation, human handoff, scene verification.

## Main idea

The BT stays reactive and owns local retry/recovery.
The supervisor owns step selection and human/robot allocation.
The Python skill server owns policy execution.
The VLM, when added, should only produce closed-set scene observations.

The stack currently validates orchestration, ROS2 contracts, simulated robot skills, human handoff, and BehaviorTree.CPP execution against a mock skill server. It does not yet validate real Panda execution, real ACT policy performance, or live VLM perception.
