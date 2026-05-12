# Grocery Bagging BT

This guide lists the commands needed to run the `grocery_bagging` BT and to manually emulate the VLM verdicts.

BT diagram: [grocery_bagging_bt.png](lerobot_bt_runtime_cpp/diagrams/grocery_bagging_bt.png)

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
`grocery_bagging_executor.yaml` with the real BC checkpoint path or Hub id.

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/lerobot_bt_python/grocery_bagging_executor.yaml"
```

## Terminal 2: BT runner

Preferred launch command:

```bash
ros2 launch lerobot_bt_runtime_cpp grocery_bagging.launch.py
```

Equivalent direct runner command:

```bash
ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner \
  --ros-args \
  --params-file "$(pwd)/src/lerobot_bt_runtime_cpp/config/grocery_bagging_bt.yaml" \
  -p tree_xml_path:="$(pwd)/src/lerobot_bt_runtime_cpp/trees/grocery_bagging.xml"
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
  "{data: '{\"skill_name\":\"grocery_bagging.scene_0_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"bagging setup ready\"}'}"
```

Rigid or cylindrical item bagged:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"bag_rigid_or_cylindrical_item\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"rigid or cylindrical item is in the bag\"}'}"
```

Flat or long item bagged:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"bag_flat_or_long_item\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"flat or long item is in the bag\"}'}"
```

Soft or fragile item bagged:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"bag_soft_or_fragile_item\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"soft or fragile item is in the bag\"}'}"
```

Task complete:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"grocery_bagging.task_complete\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"grocery bagging task complete\"}'}"
```

## Failure and human help examples

Retry the current skill:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"bag_flat_or_long_item\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"item_outside_bag\",\"message\":\"item is still outside the bag\"}'}"
```

Request human intervention:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"bag_soft_or_fragile_item\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"bag_collapsed\",\"required_human_action\":\"open and stabilize the grocery bag\",\"message\":\"human help required\"}'}"
```

## Useful checks

```bash
ros2 topic echo /lerobot_bt/status
ros2 topic echo /lerobot_bt/skill_request
ros2 topic echo /lerobot_bt/skill_result
```
