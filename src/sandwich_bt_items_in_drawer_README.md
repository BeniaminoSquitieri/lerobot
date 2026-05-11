# Items In Drawer BT

This guide lists the commands needed to run the `items_in_drawer` BT and to manually emulate the VLM verdicts.

## Terminal setup

Run this in every terminal:

```bash
conda activate lerobot
cd /home/panda-admin/users/sben/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

## Terminal 1: skill server

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/sandwich_bt_python/items_in_drawer_executor.yaml"
```

## Terminal 2: BT runner

```bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner \
  --ros-args \
  --params-file "$(pwd)/src/sandwich_bt_runtime_cpp/config/items_in_drawer_bt.yaml" \
  -p tree_xml_path:="$(pwd)/src/sandwich_bt_runtime_cpp/trees/items_in_drawer.xml"
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
  "{data: '{\"skill_name\":\"items_in_drawer.scene_0_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"drawer setup ready\"}'}"
```

Drawer opened:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"open_drawer\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"drawer is open\"}'}"
```

Object picked:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pick_object_for_drawer\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"object picked for drawer insertion\"}'}"
```

Object inserted:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"insert_object_in_drawer\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"object inserted in drawer\"}'}"
```

Drawer closed:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"close_drawer\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"drawer is closed\"}'}"
```

Task complete:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"items_in_drawer.task_complete\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"items in drawer task complete\"}'}"
```

## Failure and human help examples

Retry the current skill:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"insert_object_in_drawer\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"object_not_inside_drawer\",\"message\":\"object is not fully inside the drawer\"}'}"
```

Request human intervention:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"close_drawer\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"drawer_blocked\",\"required_human_action\":\"remove the obstruction from the drawer rails\",\"message\":\"human help required\"}'}"
```

## Useful checks

```bash
ros2 topic echo /sandwich_bt/status
ros2 topic echo /sandwich_bt/skill_request
ros2 topic echo /sandwich_bt/skill_result
```
