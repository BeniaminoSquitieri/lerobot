# lerobot_bt_python

This package is the Python execution layer for the LeRobot behavior-tree stack.
It connects the C++ BT runner to LeRobot policies, the Panda/Robotiq robot
backend, cameras, action/observation processors, and VLM or human verification.

The C++ runner decides what should happen next. This package executes the named
command and reports the result.

For the full runtime-vs-test classification of every file (with study
priorities), see
[../../docs/robot_runtime_code_map.md](../../docs/robot_runtime_code_map.md).
The `Priority` column below mirrors it: P0 real runtime, P2 robot-day support,
P3 fake/offline/eval.

## Main Files

| File | Responsibility | Priority |
| --- | --- | --- |
| `server.py` | ROS 2 node that exposes `RunNamedCommand`, VLM state services, verifier topics, robot startup, and optional camera publishing. | P0 |
| `executor.py` | Runs one learned skill: observation, policy action selection, processor pipeline, robot command, transition conditions, and result mapping. | P0 |
| `skill_runtime_loader.py` | Loads policies and builds runtime feature metadata for configured skills. | P0 |
| `config.py` | Draccus dataclasses matching the executor YAML schema. | P0 |
| `processor_factory.py` | Builds LeRobot `RobotProcessorPipeline` instances from YAML processor step declarations. | P0 |
| `conditions.py` | Observation-based termination predicates consulted each control loop. | P0 |
| `verification.py` | In-memory state machine for VLM/gate attempts and statuses. | P0 |
| `vlm_protocol.py` | JSON payload helpers for verifier request/result messages. | P1 |
| `bt_interface_paths.py` | Resolves generated ROS2 interface bindings on `sys.path`. | P1 |
| `camera_publisher.py` | Publishes already-open robot camera frames to ROS topics for an external verifier. | P1 |
| `operator_console.py` | Human-readable terminal banners for VLM request/result events. | P1 |
| `groot2_monitor.py` | Optional Groot2 monitor launcher for live BT visualization. | P2 |
| `*_executor.yaml` | Task-specific robot, camera, policy, skill, processor, and VLM config. | P0 |
| `bt_generation/` | Runtime BT generation (P0) + robot-day logging (P2) + offline `eval_ablation.py` (P3). See [bt_generation/README.md](bt_generation/README.md). | mixed |
| `fakes/` | Smoke-test-only fake server. Never on the robot. See [fakes/README.md](fakes/README.md). | P3 |

## Runtime Flow

```text
BT leaf in lerobot_bt_runtime_cpp
  -> RunNamedCommand service
  -> server.py
  -> executor.py
  -> LeRobot policy and robot backend in ../lerobot
  -> VLM request/result topics when a gate or skill needs scene verification
```

The Python server owns hardware and policy execution. The C++ BT runner owns
tree structure, retry logic, and sequencing.

## Executor YAML Files

| Task | Executor YAML |
| --- | --- |
| Make sandwich | `make_sandwich_executor.yaml` |
| Make coffee | `make_coffee_executor.yaml` |
| Set breakfast table | `set_breakfast_table_executor.yaml` |
| Prepare picnic bag | `prepare_picnic_bag_executor.yaml` |
| Items in drawer | `items_in_drawer_executor.yaml` |

Each executor YAML defines:

- ROS service and topic names.
- Panda arm, Robotiq gripper, and camera configuration.
- `expected_skill_names`, which must match the names used by BT YAML in
  `../lerobot_bt_runtime_cpp/config/`.
- LeRobot policy variants and pretrained checkpoint paths.
- Skill transition conditions and timeouts.
- `robot_action_processor` and `robot_observation_processor` pipelines.

For real robot rollout, keep safety processors enabled where configured. For
example, `make_sandwich_executor.yaml` uses
`cartesian_action_safety_processor` before Panda commands are sent.

## Commands

Commands for starting the skill server, publishing manual VLM verdicts,
preflight, and tests are centralized in `../README.md`.
