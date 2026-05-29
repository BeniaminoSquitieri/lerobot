# lerobot_bt_runtime_cpp

This ROS 2 package is the C++ BehaviorTree.CPP runtime for the LeRobot BT
stack. It owns task sequencing, XML tree loading, retry behavior, and the
custom BT leaves that call the Python skill server.

It does not load LeRobot policies and it does not command the robot directly.
Those responsibilities belong to `../lerobot_bt_python` and `../lerobot`.

## Main Files

| Path | Responsibility |
| --- | --- |
| `src/lerobot_bt_main.cpp` | Executable entry point. Loads parameters, registers BT nodes, creates the tree, ticks it, and optionally publishes Groot/Groot2 state. |
| `src/run_named_command_node.cpp` | Base service-backed command node plus `DoSkill`. |
| `src/await_scene_node.cpp` | Scene-gate node that opens/polls VLM checks. |
| `include/lerobot_bt_runtime_cpp/*.hpp` | Public C++ declarations for the runtime nodes. |
| `trees/*.xml` | BehaviorTree.CPP task topology. |
| `config/*_bt.yaml` | Blackboard parameters consumed by the XML trees. |
| `launch/*.launch.py` | One-command ROS 2 launch files for each task. |
| `CMakeLists.txt` | Builds `lerobot_bt_runner` and installs config/tree/launch resources. |

## Relationship With Other Packages

```text
lerobot_bt_runtime_cpp
  -> uses lerobot_bt_interfaces service types
  -> calls lerobot_bt_python server over ROS 2
  -> waits for VLM state stored by lerobot_bt_python
```

BehaviorTree.CPP itself is expected from the ROS 2/system environment. See
`../behaviortree_cpp/README.md` for that dependency note.

## Task Files

| Task | Launch | XML tree | BT params | Python executor |
| --- | --- | --- | --- | --- |
| Make sandwich | `launch/make_sandwich.launch.py` | `trees/make_sandwich.xml` | `config/make_sandwich_bt.yaml` | `../lerobot_bt_python/make_sandwich_executor.yaml` |
| Make coffee | `launch/make_coffee.launch.py` | `trees/make_coffee.xml` | `config/make_coffee_bt.yaml` | `../lerobot_bt_python/make_coffee_executor.yaml` |
| Set breakfast table | `launch/set_breakfast_table.launch.py` | `trees/set_breakfast_table.xml` | `config/set_breakfast_table_bt.yaml` | `../lerobot_bt_python/set_breakfast_table_executor.yaml` |
| Prepare picnic bag | `launch/prepare_picnic_bag.launch.py` | `trees/prepare_picnic_bag.xml` | `config/prepare_picnic_bag_bt.yaml` | `../lerobot_bt_python/prepare_picnic_bag_executor.yaml` |
| Items in drawer | `launch/items_in_drawer.launch.py` | `trees/items_in_drawer.xml` | `config/items_in_drawer_bt.yaml` | `../lerobot_bt_python/items_in_drawer_executor.yaml` |

Name alignment matters:

1. XML nodes read blackboard keys such as `{place_first_toast_skill}`.
2. `config/*_bt.yaml` assigns those keys to concrete names such as
   `place_first_toast`.
3. The matching Python `*_executor.yaml` must list the same names under
   `expected_skill_names` and `skills`.

## Build

From the repository root:

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --packages-up-to lerobot_bt_runtime_cpp --symlink-install
source install/setup.bash
```

For Humble, source `/opt/ros/humble/setup.bash` instead.

## Run

Start the Python skill server first in another terminal:

```bash
uv run lerobot-bt-skill-server \
  --config_path=src/lerobot_bt_python/make_sandwich_executor.yaml
```

Then launch the BT runner:

```bash
ros2 launch lerobot_bt_runtime_cpp make_sandwich.launch.py
```

Run another task by swapping the launch file and the Python executor YAML:

```bash
TASK=items_in_drawer
uv run lerobot-bt-skill-server \
  --config_path=src/lerobot_bt_python/${TASK}_executor.yaml

ros2 launch lerobot_bt_runtime_cpp ${TASK}.launch.py
```

## Runner Parameters

The launch files pass task defaults, but the executable also accepts ROS
parameters:

- `tree_xml_path`: XML tree to load.
- `bt_command_service`: service used for BT -> Python commands. Default:
  `/lerobot_bt/run`.
- `vlm_state_service`: service used to poll Python VLM state. Default:
  `/lerobot_bt/vlm_state`.
- `tick_ms`: BT tick period. Default: `100`.
- `enable_groot_publisher`: publish tree state for Groot/Groot2. Default:
  `true`.
- `groot_publisher_port`: Groot2 publisher port when supported. Default:
  `1667`.

Example override:

```bash
ros2 launch lerobot_bt_runtime_cpp make_sandwich.launch.py \
  enable_groot_publisher:=false
```

## Groot2 Monitor

When the runner starts with Groot publishing enabled, open the monitor with:

```bash
uv run lerobot-bt-groot2
```

## Preflight

Run before a real robot session:

```bash
uv run python scripts/bt_preflight_check.py --task make_sandwich
uv run python scripts/bt_preflight_check.py --task make_sandwich --real
```

## Changing A Task

- Change tree order/control flow in `trees/*.xml`.
- Change names, timeouts, and retry counts in `config/*_bt.yaml`.
- Change policies, robot hardware, processors, camera topics, and skill
  transitions in `../lerobot_bt_python/*_executor.yaml`.
- Change service fields only in `../lerobot_bt_interfaces` and update both C++
  and Python users together.
