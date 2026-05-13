# Prepare Picnic Bag BT

This guide lists the commands needed to run the `prepare_picnic_bag` BT and to manually emulate the VLM verdicts.

BT diagram: [prepare_picnic_bag_bt.png](lerobot_bt_runtime_cpp/diagrams/prepare_picnic_bag_bt.png)

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
`prepare_picnic_bag_executor.yaml` with the real BC checkpoint path or Hub id.

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/lerobot_bt_python/prepare_picnic_bag_executor.yaml"
```

## Terminal 2: BT runner

Preferred launch command:

```bash
ros2 launch lerobot_bt_runtime_cpp prepare_picnic_bag.launch.py
```

Equivalent direct runner command:

```bash
ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner \
  --ros-args \
  --params-file "$(pwd)/src/lerobot_bt_runtime_cpp/config/prepare_picnic_bag_bt.yaml" \
  -p tree_xml_path:="$(pwd)/src/lerobot_bt_runtime_cpp/trees/prepare_picnic_bag.xml"
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
  "{data: '{\"skill_name\":\"prepare_picnic_bag.scene_0_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"picnic scene ready\"}'}"
```

Human opens and holds the bag:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"prepare_picnic_bag.human_open_bag\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"human opened the bag and is holding it open\"}'}"
```

Human inserts the Monster drink:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"prepare_picnic_bag.human_insert_monster\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"Monster drink is inside the bag\"}'}"
```

Robot inserts the bread:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"bag_bread\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"bread is inside the bag\"}'}"
```

Human inserts the mustard:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"prepare_picnic_bag.human_insert_mustard\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"mustard is inside the bag\"}'}"
```

Robot inserts the pear. This is the final BT step:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"bag_pear\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"pear is inside the bag\"}'}"
```

## Failure and human help examples

Retry the current skill:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"bag_bread\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"bread_not_bagged\",\"message\":\"bread is not correctly inside the bag\"}'}"
```

Request human intervention:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"prepare_picnic_bag.human_insert_monster\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"monster_not_bagged\",\"required_human_action\":\"insert the Monster drink into the picnic bag\",\"message\":\"human help required\"}'}"
```

## Useful checks

```bash
ros2 topic echo /lerobot_bt/status
ros2 topic echo /lerobot_bt/skill_request
ros2 topic echo /lerobot_bt/skill_result
```
