# Lunch Table Bussing BT

This guide lists the commands needed to run the `lunch_table_bussing` BT and to manually emulate the VLM verdicts.

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
`lunch_table_bussing_executor.yaml` with the real BC checkpoint path or Hub id.

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/sandwich_bt_python/lunch_table_bussing_executor.yaml"
```

## Terminal 2: BT runner

Preferred launch command:

```bash
ros2 launch sandwich_bt_runtime_cpp lunch_table_bussing.launch.py
```

Equivalent direct runner command:

```bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner \
  --ros-args \
  --params-file "$(pwd)/src/sandwich_bt_runtime_cpp/config/lunch_table_bussing_bt.yaml" \
  -p tree_xml_path:="$(pwd)/src/sandwich_bt_runtime_cpp/trees/lunch_table_bussing.xml"
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
  "{data: '{\"skill_name\":\"lunch_table_bussing.scene_0_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"table setup ready\"}'}"
```

Trash item disposed:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_and_dispose_trash\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"trash item placed in bin\"}'}"
```

Plate cleared:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"clear_plate\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"plate and plate trash handled\"}'}"
```

Cutlery stored:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_and_store_cutlery\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"cutlery stored\"}'}"
```

Dishware stored:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_and_store_dishware\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"dishware stored\"}'}"
```

Task complete:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"lunch_table_bussing.task_complete\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"table bussing task complete\"}'}"
```

## Failure and human help examples

Retry the current skill:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"clear_plate\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"plate_not_in_container\",\"message\":\"plate is not correctly stored\"}'}"
```

Request human intervention:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_and_store_dishware\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"fragile_object_unreachable\",\"required_human_action\":\"move fragile object back into the robot workspace\",\"message\":\"human help required\"}'}"
```

## Useful checks

```bash
ros2 topic echo /sandwich_bt/status
ros2 topic echo /sandwich_bt/skill_request
ros2 topic echo /sandwich_bt/skill_result
```
