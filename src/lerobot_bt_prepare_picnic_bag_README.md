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

Bag next picnic item:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"bag_next_picnic_item\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"all picnic items are now inside the bag\"}'}"
```

Human closes the bag:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"prepare_picnic_bag.human_close_bag\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"human closed the picnic bag\"}'}"
```

Task complete:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"prepare_picnic_bag.task_complete\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"picnic bag is packed and the scene is complete\"}'}"
```

## Failure and human help examples

Retry the current skill:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"bag_next_picnic_item\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"more_items_remaining\",\"message\":\"the scene is not clean yet, run the bagging skill again\"}'}"
```

Request human intervention:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"prepare_picnic_bag.human_open_bag\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"bag_not_open\",\"required_human_action\":\"open the picnic bag and keep it open for the robot\",\"message\":\"human help required\"}'}"
```

## Useful checks

```bash
ros2 topic echo /lerobot_bt/status
ros2 topic echo /lerobot_bt/skill_request
ros2 topic echo /lerobot_bt/skill_result
```
