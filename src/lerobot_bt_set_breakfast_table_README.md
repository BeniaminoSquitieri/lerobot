# Set Breakfast Table BT

This guide lists the commands needed to run the `set_breakfast_table` BT and to manually emulate the VLM verdicts.

BT diagram: [set_breakfast_table_bt.png](lerobot_bt_runtime_cpp/diagrams/set_breakfast_table_bt.png)

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
`set_breakfast_table_executor.yaml` with the real BC checkpoint path or Hub id.

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/lerobot_bt_python/set_breakfast_table_executor.yaml"
```

## Terminal 2: BT runner

Preferred launch command:

```bash
ros2 launch lerobot_bt_runtime_cpp set_breakfast_table.launch.py
```

Equivalent direct runner command:

```bash
ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner \
  --ros-args \
  --params-file "$(pwd)/src/lerobot_bt_runtime_cpp/config/set_breakfast_table_bt.yaml" \
  -p tree_xml_path:="$(pwd)/src/lerobot_bt_runtime_cpp/trees/set_breakfast_table.xml"
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
  "{data: '{\"skill_name\":\"breakfast_table.tablecloth_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"tablecloth placed\"}'}"
```

Robot places cereal box:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_cereal_box\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"cereal box placed\"}'}"
```

Human places tea box:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"breakfast_table.tea_box_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"tea box placed\"}'}"
```

Robot places bottle:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_bottle\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"bottle placed\"}'}"
```

Robot places cup:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_cup\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"cup placed\"}'}"
```

Human places spoon:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"breakfast_table.spoon_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"spoon placed\"}'}"
```

Robot places bowl:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_bowl\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"bowl placed\"}'}"
```

Task complete:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"breakfast_table.task_complete\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"breakfast table task complete\"}'}"
```

## Failure and human help examples

Retry the current skill:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_cup\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"cup_not_stable\",\"message\":\"cup is not correctly placed\"}'}"
```

Request human intervention:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_bowl\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"bowl_out_of_reach\",\"required_human_action\":\"move the bowl back into the robot workspace\",\"message\":\"human help required\"}'}"
```

## Useful checks

```bash
ros2 topic echo /lerobot_bt/status
ros2 topic echo /lerobot_bt/skill_request
ros2 topic echo /lerobot_bt/skill_result
```
