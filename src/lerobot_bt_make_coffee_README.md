# Make Coffee BT

This guide lists the commands needed to run the `make_coffee` BT and to manually emulate the VLM verdicts.

BT diagram: [make_coffee_bt.png](lerobot_bt_runtime_cpp/diagrams/make_coffee_bt.png)

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
  --config_path "$(pwd)/src/lerobot_bt_python/make_coffee_executor.yaml"
```

## Terminal 2: BT runner

Preferred launch command:

```bash
ros2 launch lerobot_bt_runtime_cpp make_coffee.launch.py
```

Equivalent direct runner command:

```bash
ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner \
  --ros-args \
  --params-file "$(pwd)/src/lerobot_bt_runtime_cpp/config/make_coffee_bt.yaml" \
  -p tree_xml_path:="$(pwd)/src/lerobot_bt_runtime_cpp/trees/make_coffee.xml"
```

## Terminal 3: observe VLM requests

```bash
ros2 topic echo /lerobot_bt/vlm_request
```

## VLM verdict commands

Send each command when the BT is waiting for the corresponding VLM request. Keep `attempt_id` aligned with the latest request printed on `/lerobot_bt/vlm_request`.

Initial scene ready:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"make_coffee.scene_0_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"coffee setup ready\"}'}"
```

Human placed the cup under the dispenser:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"make_coffee.cup_under_dispenser\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"cup is under the dispenser\"}'}"
```

Capsule inserted:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_and_insert_capsule\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"capsule inserted\"}'}"
```

Robot closed the machine:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"close_coffee_machine\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"coffee machine closed\"}'}"
```

Human pressed the start button and extraction starts. This is the final BT gate:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"make_coffee.human_press_start_button\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"coffee extraction started\"}'}"
```

## Failure and human help examples

Retry the current skill:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_and_insert_capsule\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"capsule_not_inserted\",\"message\":\"capsule is not correctly inserted\"}'}"
```

Request human intervention:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"make_coffee.human_press_start_button\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"button_not_pressed\",\"required_human_action\":\"press the coffee machine start button\",\"message\":\"human help required\"}'}"
```

## Useful checks

```bash
ros2 topic echo /lerobot_bt/status
ros2 topic echo /lerobot_bt/skill_request
ros2 topic echo /lerobot_bt/skill_result
```
