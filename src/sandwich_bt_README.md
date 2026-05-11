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
| `sandwich_bt_python` | Executes real BC skills and manages VLM check attempts. |
| `sandwich_bt_interfaces` | Generates the three ROS2 service contracts used by the stack. |

## Active Flow

Default tree:

```text
src/sandwich_bt_runtime_cpp/trees/makesandwitch.xml
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

second_toast_ready
  -> human step represented as VLM/manual gate

place_second_toast
  -> BC skill
  -> VLM/manual result

makesandwitch.task_complete
  -> final VLM/manual task gate
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

The readable BT command leaves map to these Python command kinds:

- `RunRobotSkill`: runs one configured BC skill on the robot.
- `OpenVLMGate`: opens a VLM/manual check attempt without robot motion.

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
    RunRobotSkill(skill_name="<skill>")
    WaitForSkillVerdict(skill_name="<skill>")
```

For a VLM/human gate with no robot motion, the shape is:

```text
RetryUntilSuccessful(name="retry_<gate>_until_vlm_success")
  Sequence(name="<gate>_wait_or_manual_intervention_gate")
    OpenVLMGate(gate_name="<gate>")
    WaitForGateVerdict(gate_name="<gate>")
```

If the skill call fails, the sequence fails and the same skill is retried.

If the VLM reports `FAILURE`, `WaitForSkillVerdict` returns BT `FAILURE`; the
same `RetryUntilSuccessful` wrapper restarts the same BC skill from the
beginning.

If the VLM reports `RUNNING`, `WAIT_HUMAN`, or
`MANUAL_INTERVENTION_REQUIRED`, `WaitForGateVerdict` or
`WaitForSkillVerdict` keeps returning BT
`RUNNING`; the tree waits for a later `SUCCESS` or `FAILURE`.

No gripper open/close, Panda reset, or deterministic Cartesian delta is run by
the retry mechanism.

`WaitForGateVerdict` and `WaitForSkillVerdict` are readable wrappers around the
same C++ VLM check node. They are intentionally present in XML so Groot shows
whether the BT is waiting on a human/VLM gate or checking a robot skill result.

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

Start the C++ BT runner with the active real-robot tree and its task parameter
profile. Start this after the skill server is ready.

Preferred launch command:

```bash
ros2 launch sandwich_bt_runtime_cpp makesandwitch.launch.py
```

Equivalent direct runner command:

```bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner --ros-args \
  --params-file "$(pwd)/src/sandwich_bt_runtime_cpp/config/makesandwitch_bt.yaml" \
  -p tree_xml_path:="$(pwd)/src/sandwich_bt_runtime_cpp/trees/makesandwitch.xml"
```

The XML keeps the order/retry structure. The YAML profile keeps the names and
timeouts that are expected to change between BTs:

```text
initial_scene_ready
place_first_toast
pour_ingredient
second_toast_ready
place_second_toast
makesandwitch.task_complete
```

For a new BT, make a new XML if the order changes. If only checkpoint names,
skill names, or timeouts change, make a new `config/*.yaml` profile and pass it
with `--params-file`.

### Optional Groot2 monitor

Open Groot2 already configured for the BT.CPP monitor endpoint:

```bash
lerobot-bt-groot2
```

This writes Groot2's local settings to `Mode=Monitor`, `Host=localhost`, and
`Port=1667` before launching the GUI. If Groot2 is installed somewhere custom,
pass its path explicitly:

```bash
lerobot-bt-groot2 --app ~/Applications/Groot2-v1.9.0-x86_64.AppImage
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

Second toast positioned correctly by the human:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"second_toast_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"second toast ready\"}'}"
```

Second toast placed correctly:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_second_toast\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"second toast ok\"}'}"
```

Task complete:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"makesandwitch.task_complete\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"sandwich task complete\"}'}"
```

Force a retry for the current stage:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"toast misplaced\",\"message\":\"retry skill\"}'}"
```

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_second_toast\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"toast misplaced\",\"message\":\"retry skill\"}'}"
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

The real-robot config currently has `vlm_timeout_s: 0.0`, so pending VLM
attempts do not automatically become `FAILURE` while you are doing slower
manual tests. Set a positive value in the executor YAML when you want automatic
timeout-to-retry behavior.

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

## Additional BT command guides

The same command format is documented for the additional scene-gated BTs:

- [VLM, BT, and BC conventions](sandwich_bt_vlm_conventions_README.md)
- [Lunch Table Bussing](sandwich_bt_lunch_table_bussing_README.md)
- [Grocery Bagging](sandwich_bt_grocery_bagging_README.md)
- [Items In Drawer](sandwich_bt_items_in_drawer_README.md)
- [Make Coffee](sandwich_bt_make_coffee_README.md)
