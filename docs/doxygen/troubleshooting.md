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

## Doxygen not installed

**Symptom:**
```text
./useful_scripts/build_sandwich_bt_docs.sh: line X: doxygen: command not found
```

**Cause:**
Doxygen (and optionally Graphviz) are not installed on the developer machine.

**Fix:**
Install Doxygen and Graphviz. Example:
```bash
sudo apt update && sudo apt install doxygen graphviz
```
or with conda:
```bash
conda install -c conda-forge doxygen graphviz
```

After installation, re-run:
```bash
useful_scripts/build_sandwich_bt_docs.sh
```

## Building BehaviorTree.CPP / missing `catkin_pkg` or rosdep failures

**Symptom:**
```text
ModuleNotFoundError: No module named 'catkin_pkg'
or colcon build aborts with missing dependencies for behaviortree_cpp
```

**Cause:**
- The build picked a Conda Python that does not contain ROS helper packages (e.g. `catkin_pkg`).
- Native build dependencies (ZeroMQ headers, etc.) are missing or `rosdep` was not run.

**Fix (steps we used successfully):**

1. Fast option: install prebuilt package
```bash
sudo apt update
sudo apt install ros-${ROS_DISTRO}-behaviortree-cpp
# or, if you need the v3 API:
sudo apt install ros-${ROS_DISTRO}-behaviortree-cpp-v3
```

2. To build from source (if you need latest examples):
```bash
# install native deps
sudo apt install libzmq3-dev

# clone into src/ so colcon will build it
cd $(pwd)
cd src
git clone https://github.com/BehaviorTree/BehaviorTree.CPP.git behaviortree_cpp
cd ..
```

3. Ensure `rosdep` and system python ROS packages are available:
```bash
sudo apt install python3-rosdep2
# optionally: pip install -U catkin_pkg  # if you prefer to fix the active python
```

4. Use `rosdep` to install OS-level deps and then build using system python:
```bash
rosdep update || true
rosdep install --from-paths src --ignore-src -r -y

# clean previous artifacts
rm -rf build install log

source /opt/ros/${ROS_DISTRO}/setup.bash
colcon build --base-paths src \
  --packages-up-to behaviortree_cpp sandwich_bt_runtime_cpp \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

Notes:
- If `ModuleNotFoundError: No module named 'catkin_pkg'` appears while a Conda env is active, either install `catkin_pkg` into that env (`pip install -U catkin_pkg`) or tell `colcon` to use the system Python as shown above.
- Installing the ROS-provided package is the simplest approach for most developers.

