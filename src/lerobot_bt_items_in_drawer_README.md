# Items In Drawer BT

This guide lists the commands needed to run the `items_in_drawer` BT and to manually emulate the VLM verdicts.

BT diagram: [items_in_drawer_bt.png](lerobot_bt_runtime_cpp/diagrams/items_in_drawer_bt.png)

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
`items_in_drawer_executor.yaml` with the real BC checkpoint path or Hub id.

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/lerobot_bt_python/items_in_drawer_executor.yaml"
```

## Terminal 2: BT runner

Preferred launch command:

```bash
ros2 launch lerobot_bt_runtime_cpp items_in_drawer.launch.py
```

Equivalent direct runner command:

```bash
ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner \
  --ros-args \
  --params-file "$(pwd)/src/lerobot_bt_runtime_cpp/config/items_in_drawer_bt.yaml" \
  -p tree_xml_path:="$(pwd)/src/lerobot_bt_runtime_cpp/trees/items_in_drawer.xml"
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
  "{data: '{\"skill_name\":\"items_in_drawer.scene_0_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"drawer setup ready\"}'}"
```

Drawer opened:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"open_drawer\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"drawer is open\"}'}"
```

Object picked:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_object_for_drawer\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"object picked for drawer insertion\"}'}"
```

Object inserted:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"insert_object_in_drawer\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"object inserted in drawer\"}'}"
```

Drawer closed:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"close_drawer\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"drawer is closed\"}'}"
```

Task complete:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"items_in_drawer.task_complete\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"items in drawer task complete\"}'}"
```

## Failure and human help examples

Retry the current skill:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"insert_object_in_drawer\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"object_not_inside_drawer\",\"message\":\"object is not fully inside the drawer\"}'}"
```

Request human intervention:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"close_drawer\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"drawer_blocked\",\"required_human_action\":\"remove the obstruction from the drawer rails\",\"message\":\"human help required\"}'}"
```

## Useful checks

```bash
ros2 topic echo /lerobot_bt/status
ros2 topic echo /lerobot_bt/skill_request
ros2 topic echo /lerobot_bt/skill_result
```
