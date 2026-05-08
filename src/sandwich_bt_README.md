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
- `no_motion_skill`: skip robot motion and auto-mark the VLM check as `SUCCESS`.
- `vlm_gate_pending`: open a VLM check attempt without robot motion.

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

For a real running `skill`, `SUCCESS`, `FAILURE`, `WAIT_HUMAN`, or
`MANUAL_INTERVENTION_REQUIRED` also acts as a live stop: the Python executor
stops sending policy actions, then opens the skill's VLM check already set to
that status. `PENDING` and `RUNNING` are only post-skill waiting states.

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
    RunNamedCommand(kind="vlm_gate_pending", command_name="<gate>")
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

## Real Robot Complete Test

Use the commands below to run the current two-real-skill sandwich test with the
real Panda/Robotiq/camera stack and a manual terminal acting as the VLM.

Run this setup in every ROS2 terminal:

```bash
conda activate lerobot
cd /home/panda-admin/users/sben/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

If the ROS2 packages have not been built after changing interfaces or trees,
build once and source again:

```bash
colcon build --base-paths src --packages-up-to sandwich_bt_runtime_cpp
source install/setup.bash
```

### Terminale 1: real skill server

Start the Python execution layer. This connects the real robot and executes the
learned skills configured in `sandwich_bt_executor.yaml`.

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/sandwich_bt_python/sandwich_bt_executor.yaml"
```

### Terminale 2: BehaviorTree runner

Start the C++ BT runner with the temporary real-robot tree. Start this after the
skill server is ready.

```bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner --ros-args \
  -p tree_xml_path:="$(pwd)/src/sandwich_bt_runtime_cpp/trees/sandwich_tree_two_real_skills_manual_vlm.xml"
```

The tree order is:

```text
initial_scene_ready
place_first_toast
pour_ingredient
place_second_toast
```

### Terminale 3: manual VLM

Watch the verifier requests emitted by the skill server:

```bash
ros2 topic echo /sandwich_bt/vlm_request
```

For each request, publish a verdict on the same topic a real VLM will use. You
can stop the echo with `Ctrl+C`, publish one of the commands below, then start
the echo again. `attempt_id: 0` means "apply this verdict to the latest pending
attempt for that `skill_name`".

For the two real BC skills, you do not have to wait for `/sandwich_bt/vlm_request`
if the robot has already achieved the visible goal. Publishing the `SUCCESS` or
`FAILURE` result while the policy is still moving stops that skill and lets the
BT advance to the VLM decision node immediately.

Initial scene ready:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"initial_scene_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"initial scene ready\"}'}"
```

First toast placed correctly:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"first toast ok\"}'}"
```

Human is still pouring. This keeps the BT blocked on the human/VLM gate:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pour_ingredient\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"message\":\"human is pouring\"}'}"
```

Human pouring completed:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pour_ingredient\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"ingredient poured\"}'}"
```

Second toast placed correctly:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_second_toast\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"second toast ok\"}'}"
```

Force a retry for the current stage:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"toast misplaced\",\"message\":\"retry skill\"}'}"
```

Request manual intervention without advancing the BT:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"object_missing\",\"required_human_action\":\"put toast back in reachable area\"}'}"
```

Equivalent `next_action` values are accepted too:

```text
CONTINUE -> SUCCESS
RETRY_SKILL -> FAILURE
WAIT_HUMAN -> WAIT_HUMAN
REQUEST_MANUAL_INTERVENTION -> MANUAL_INTERVENTION_REQUIRED
```

The real-robot config currently has `vlm_timeout_s: 30.0`, so a pending VLM
attempt becomes `FAILURE` if no `SUCCESS` arrives within 30 seconds. Increase
that value or set it to `0` in `sandwich_bt_executor.yaml` for slower manual
tests.

### Useful inspection commands

List the stack topics and services:

```bash
ros2 topic list | grep sandwich_bt
ros2 service list | grep sandwich_bt
```

Inspect the latest VLM state for one stage:

```bash
ros2 service call /sandwich_bt/vlm_state sandwich_bt_interfaces/srv/GetSkillVerification \
  "{skill_name: 'place_first_toast'}"
```

Legacy service path for a VLM/manual verdict. New tools should prefer the
`/sandwich_bt/vlm_result` topic, but this remains available:

```bash
ros2 service call /sandwich_bt/vlm_result_legacy sandwich_bt_interfaces/srv/ReportSkillVerification \
  "{skill_name: 'place_first_toast', attempt_id: 0, status: 'SUCCESS', message: 'first toast ok'}"
```

### Optional mock/server commands

Hardware-free mock server:

```bash
lerobot-bt-skill-sim --ros2-service
```

Optional topic-to-topic VLM stub. It listens on `/sandwich_bt/vlm_sim` and
publishes normalized reports to `/sandwich_bt/vlm_result`:

```bash
lerobot-bt-vlm-stub
```

Example input for the stub:

```bash
ros2 topic pub --once /sandwich_bt/vlm_sim std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"first toast ok\"}'}"
```
