# Sandwich BT Stack

This stack follows one runtime model:

```text
BehaviorTree.CPP decides order, waiting, and retries.
Python executes one named BC skill or opens one VLM gate.
VLM/manual verifier reports waiting states, success, failure, or requested action.
```

There is no separate supervisor in the active runtime path. There are no
deterministic Panda recovery motions between attempts. If the VLM reports
`FAILURE`, the XML-level `RetryUntilSuccessful` node starts the same BC skill
again from the beginning.

## Packages

| Package | Role |
| --- | --- |
| `sandwich_bt_runtime_cpp` | Loads/ticks BT XML and bridges BT leaves to ROS2 services. |
| `sandwich_bt_python` | Executes real BC skills, manages VLM check attempts, and provides the mock simulator entrypoint. |
| `sandwich_bt_interfaces` | Generates the three ROS2 service contracts used by the stack. |

## Active Flow

Default tree:

```text
src/sandwich_bt_runtime_cpp/trees/sandwich_tree.xml
```

Runtime sequence:

```text
initial_scene_ready
  -> VLM/manual gate, no robot motion

place_first_toast
  -> BC skill
  -> VLM/manual result

pour_ingredient
  -> human step represented as VLM/manual gate

place_second_toast
  -> BC skill
  -> VLM/manual result
```

The BT never advances past a gate while the VLM check is a waiting status:
`PENDING`, `RUNNING`, `WAIT_HUMAN`, or `MANUAL_INTERVENTION_REQUIRED`.

## ROS2 Services

The Python server exposes:

```text
/sandwich_bt/run
/sandwich_bt/vlm_state
/sandwich_bt/vlm_result_legacy
```

`RunNamedCommand` accepts these active `kind` values:

- `skill`: run one configured BC skill on the robot.
- `simulated_skill`: simulate a skill and auto-mark the VLM check as `SUCCESS`.
- `simulated_skill_pending`: open a VLM check attempt without robot motion.

`/sandwich_bt/vlm_result` is the VLM/manual input boundary. It may report:

- `PENDING`
- `RUNNING`
- `WAIT_HUMAN`
- `MANUAL_INTERVENTION_REQUIRED`
- `SUCCESS`
- `FAILURE`

It may also report `next_action` instead of `status`. Supported values are
`CONTINUE`, `RETRY_SKILL`, `WAIT_HUMAN`, and
`REQUEST_MANUAL_INTERVENTION`.

## Failure And Retry

For a robot skill, the BT subtree shape is:

```text
RetryUntilSuccessful(name="retry_<skill>_on_vlm_retry_skill")
  Sequence(name="<skill>_vlm_replanning_loop")
    RunNamedCommand(kind="skill", command_name="<skill>")
    VLMReplanningDecision(skill_name="<skill>")
```

For a VLM/human gate with no robot motion, the shape is:

```text
RetryUntilSuccessful(name="retry_<gate>_until_vlm_success")
  Sequence(name="<gate>_wait_or_manual_intervention_gate")
    RunNamedCommand(kind="simulated_skill_pending", command_name="<gate>")
    WaitForVLMDecision(skill_name="<gate>")
```

If the skill call fails, the sequence fails and the same skill is retried.

If the VLM reports `FAILURE`, `VLMReplanningDecision` returns BT `FAILURE`; the
same `RetryUntilSuccessful` wrapper restarts the same BC skill from the
beginning.

If the VLM reports `RUNNING`, `WAIT_HUMAN`, or
`MANUAL_INTERVENTION_REQUIRED`, `WaitForVLMDecision` or
`VLMReplanningDecision` keeps returning BT
`RUNNING`; the tree waits for a later `SUCCESS` or `FAILURE`.

No gripper open/close, Panda reset, or deterministic Cartesian delta is run by
the retry mechanism.

`WaitForVLMDecision` and `VLMReplanningDecision` are semantic aliases of the
same C++ VLM check node. They are intentionally present in XML so Groot shows
where the BT is waiting for the VLM, where it can retry the same skill, and
where manual intervention blocks progress.

## Run Commands

Every ROS2 terminal:

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

Real skill server:

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/sandwich_bt_python/sandwich_bt_executor.yaml"
```

BT runner:

```bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner --ros-args \
  -p tree_xml_path:="$(pwd)/src/sandwich_bt_runtime_cpp/trees/sandwich_tree_two_real_skills_manual_vlm.xml"
```

Mock server:

```bash
lerobot-bt-skill-sim --ros2-service
```

Manual VLM verdict:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"first toast ok\",\"confidence\":0.95}'}"
```

`attempt_id: 0` means "apply to the latest pending attempt for that
`skill_name`".
