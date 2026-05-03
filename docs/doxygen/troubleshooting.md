# Troubleshooting {#troubleshooting}

## Stale generated ROS2 interfaces

**Symptom:**
```text
missing field in PlanNextStep / VerifyStep / RunNamedCommand
```

**Cause:**
The `.srv` files changed but `sandwich_bt_interfaces` was not rebuilt.

**Fix:**
```bash
source /opt/ros/jazzy/setup.bash
colcon build --base-paths src --packages-select sandwich_bt_interfaces \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

## Conda Python breaks ament/catkin_pkg

**Symptom:**
```text
ModuleNotFoundError: No module named 'catkin_pkg'
```

**Cause:**
CMake/ament picked conda Python instead of system ROS Python.

**Fix:**
```bash
colcon build --base-paths src --packages-select sandwich_bt_interfaces \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
```

## BehaviorTree.CPP missing

**Symptom:**
```text
Could not find behaviortree_cpp
```

**Fix options:**
```bash
sudo apt install ros-${ROS_DISTRO}-behaviortree-cpp
```
or provide an overlay and export:
```bash
export CMAKE_PREFIX_PATH=/path/to/bt_overlay:$CMAKE_PREFIX_PATH
export AMENT_PREFIX_PATH=/path/to/bt_overlay:$AMENT_PREFIX_PATH
export LD_LIBRARY_PATH=/path/to/bt_overlay/lib:$LD_LIBRARY_PATH
```

## `/sandwich_bt/run_command` unavailable

**Symptom:**
```text
collaborative runner exits with code 2
```

**Cause:**
The skill server or mock skill server is not running.

**Fix:**
```bash
source install/setup.bash
uv run lerobot-bt-skill-sim --ros2-service
```
or for real robot:
```bash
source install/setup.bash
lerobot-bt-skill-server --config_path "$(pwd)/src/sandwich_bt_python/sandwich_bt_executor.yaml"
```

## BT port name reserved

**Symptom:**
```text
BehaviorTree.CPP rejects XML using a port named name
```

**Fix:**
Use:
```xml
<RunNamedCommand kind="skill" command_name="place_first_toast"/>
```
not:
```xml
<RunNamedCommand kind="skill" name="place_first_toast"/>
```
