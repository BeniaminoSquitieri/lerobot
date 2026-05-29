# lerobot_bt_python

This package is the Python execution layer for the LeRobot behavior-tree stack.
It connects the C++ BT runner to LeRobot policies, the Panda/Robotiq robot
backend, cameras, action/observation processors, and VLM or human verification.

The C++ runner decides what should happen next. This package executes the named
command and reports the result.

## Main Files

| File | Responsibility |
| --- | --- |
| `server.py` | ROS 2 node that exposes `RunNamedCommand`, VLM state services, verifier topics, robot startup, and optional camera publishing. |
| `executor.py` | Runs one learned skill: observation, policy action selection, processor pipeline, robot command, transition conditions, and result mapping. |
| `skill_runtime_loader.py` | Loads policies and builds runtime feature metadata for configured skills. |
| `config.py` | Draccus dataclasses matching the executor YAML schema. |
| `processor_factory.py` | Builds LeRobot `RobotProcessorPipeline` instances from YAML processor step declarations. |
| `verification.py` | In-memory state machine for VLM/gate attempts and statuses. |
| `vlm_protocol.py` | JSON payload helpers for verifier request/result messages. |
| `camera_publisher.py` | Publishes already-open robot camera frames to ROS topics for an external verifier. |
| `bt_vlm_bridge.py` | Legacy bridge between BT JSON VLM topics and the Panda string VLM protocol. |
| `operator_console.py` | Human-readable terminal banners for VLM request/result events. |
| `*_executor.yaml` | Task-specific robot, camera, policy, skill, processor, and VLM config. |

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

## Start The Skill Server

From the repository root, in a terminal with ROS 2 and the colcon workspace
sourced:

```bash
cd /home/bsquitieri/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash
uv run lerobot-bt-skill-server \
  --config_path=src/lerobot_bt_python/make_sandwich_executor.yaml
```

For Humble, source `/opt/ros/humble/setup.bash` instead.

The entrypoint defaults to `make_sandwich_executor.yaml` if no config is
passed, but passing `--config_path` is preferred because it makes the active
task explicit.

## Start The VLM Bridge

If your verifier already consumes `/lerobot_bt/vlm_request` and publishes
`/lerobot_bt/vlm_result`, start that verifier directly.

Use the compatibility bridge only for the legacy Panda VLM string protocol:

```bash
uv run lerobot-bt-vlm-bridge
```

Default bridge topics:

- BT request in: `/lerobot_bt/vlm_request`
- BT result out: `/lerobot_bt/vlm_result`
- Panda request out: `/panda/vlm/request`
- Panda status in: `/panda/vlm/status`

## Manual VLM Result

Use the `attempt_id` printed by the server banner.

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":1,\"status\":\"SUCCESS\",\"message\":\"Scene check passed.\"}'}"
```

Terminal statuses are `SUCCESS` and `FAILURE`. Non-terminal statuses such as
`PENDING`, `RUNNING`, `WAIT_HUMAN`, and `MANUAL_INTERVENTION_REQUIRED` keep the
gate open.

## Run With The BT Runner

Use one terminal for this Python server and a second terminal for the C++
runner:

```bash
ros2 launch lerobot_bt_runtime_cpp make_sandwich.launch.py
```

To switch task:

```bash
TASK=items_in_drawer
uv run lerobot-bt-skill-server \
  --config_path=src/lerobot_bt_python/${TASK}_executor.yaml

ros2 launch lerobot_bt_runtime_cpp ${TASK}.launch.py
```

## Preflight

Run before hardware rollout:

```bash
uv run python scripts/bt_preflight_check.py --task make_sandwich
uv run python scripts/bt_preflight_check.py --task make_sandwich --real
```

## Tests And Checks

Targeted BT Python tests:

```bash
uv run pytest tests/lerobot_bt -q
```

Basic syntax check when dependencies are unavailable:

```bash
python3 -m py_compile src/lerobot_bt_python/*.py
```
