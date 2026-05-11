# Make Coffee BT

This guide lists the commands needed to run the `make_coffee` BT and to manually emulate the VLM verdicts.

## Terminal setup

Run this in every terminal:

```bash
conda activate lerobot
cd /home/panda-admin/users/sben/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

## Terminal 1: skill server

Before launching this server, replace every `TODO_MODEL...` value in
`make_coffee_executor.yaml` with the real BC checkpoint path or Hub id.

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/sandwich_bt_python/make_coffee_executor.yaml"
```

## Terminal 2: BT runner

Preferred launch command:

```bash
ros2 launch sandwich_bt_runtime_cpp make_coffee.launch.py
```

Equivalent direct runner command:

```bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner \
  --ros-args \
  --params-file "$(pwd)/src/sandwich_bt_runtime_cpp/config/make_coffee_bt.yaml" \
  -p tree_xml_path:="$(pwd)/src/sandwich_bt_runtime_cpp/trees/make_coffee.xml"
```

## Terminal 3: observe VLM requests

```bash
ros2 topic echo /sandwich_bt/vlm_request
```

## VLM verdict commands

Send each command when the BT is waiting for the corresponding VLM request. Keep `attempt_id` aligned with the latest request printed on `/sandwich_bt/vlm_request`.

Initial scene ready:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"make_coffee.scene_0_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"coffee setup ready\"}'}"
```

Cup placed under dispenser:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_cup_under_dispenser\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"cup is under the dispenser\"}'}"
```

Capsule inserted:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_and_insert_capsule\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"capsule inserted\"}'}"
```

Start button pressed:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"press_start_button\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"coffee extraction started\"}'}"
```

Task complete:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"make_coffee.task_complete\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"coffee task complete\"}'}"
```

## Failure and human help examples

Retry the current skill:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_and_insert_capsule\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"capsule_not_inserted\",\"message\":\"capsule is not correctly inserted\"}'}"
```

Request human intervention:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"press_start_button\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"machine_not_ready\",\"required_human_action\":\"check the coffee machine state\",\"message\":\"human help required\"}'}"
```

## Useful checks

```bash
ros2 topic echo /sandwich_bt/status
ros2 topic echo /sandwich_bt/skill_request
ros2 topic echo /sandwich_bt/skill_result
```
