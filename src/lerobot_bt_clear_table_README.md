# Clear Table BT

This guide lists the commands needed to run the `clear_table` BT and to manually emulate the VLM verdicts.

BT diagram: [clear_table_bt.png](lerobot_bt_runtime_cpp/diagrams/clear_table_bt.png)

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
`clear_table_executor.yaml` with the real BC checkpoint path or Hub id.

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/lerobot_bt_python/clear_table_executor.yaml"
```

## Terminal 2: BT runner

Preferred launch command:

```bash
ros2 launch lerobot_bt_runtime_cpp clear_table.launch.py
```

Equivalent direct runner command:

```bash
ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner \
  --ros-args \
  --params-file "$(pwd)/src/lerobot_bt_runtime_cpp/config/clear_table_bt.yaml" \
  -p tree_xml_path:="$(pwd)/src/lerobot_bt_runtime_cpp/trees/clear_table.xml"
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
  "{data: '{\"skill_name\":\"clear_table.scene_0_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"table setup ready\"}'}"
```

Trash item disposed:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_and_dispose_trash\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"trash item placed in bin\"}'}"
```

Plate cleared:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"clear_plate\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"plate and plate trash handled\"}'}"
```

Cutlery stored:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_and_store_cutlery\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"cutlery stored\"}'}"
```

Dishware stored:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_and_store_dishware\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"dishware stored\"}'}"
```

Task complete:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"clear_table.task_complete\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"clear table task complete\"}'}"
```

## Failure and human help examples

Retry the current skill:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"clear_plate\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"plate_not_in_container\",\"message\":\"plate is not correctly stored\"}'}"
```

Request human intervention:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_and_store_dishware\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"fragile_object_unreachable\",\"required_human_action\":\"move fragile object back into the robot workspace\",\"message\":\"human help required\"}'}"
```

## Useful checks

```bash
ros2 topic echo /lerobot_bt/status
ros2 topic echo /lerobot_bt/skill_request
ros2 topic echo /lerobot_bt/skill_result
```
