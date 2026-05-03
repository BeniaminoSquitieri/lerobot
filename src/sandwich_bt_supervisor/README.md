# Sandwich BT Supervisor

Closed-set collaborative supervisor for the sandwich task.

This package sits above the existing BT runtime. It does not replace the
BehaviorTree.CPP layer. It decides which subtask comes next, assigns that
subtask to either the robot or the human, and verifies the scene after each
handoff. In the hardware-free simulation, robot-owned steps are executed
through per-step BT XML subtrees instead of calling the skill executor
directly.

## Responsibility

It owns:

- minimal scene-state estimation for the sandwich task
- closed-set task allocation across `robot` and `human`
- explicit human confirmation before human-owned steps succeed
- scene verification after each step
- a hardware-free simulation path for the `robot -> human -> robot` loop

It does not own:

- low-level robot control
- ACT or GR00T policy inference
- BT retries and local recoveries
- live VLM perception

Those still belong to `sandwich_bt_python` and `sandwich_bt_runtime_cpp`.

## Files

- `planner_schema.py`: planner config and response schemas
- `scene_state.py`: closed-set scene-state estimator and verification rules
- `task_allocator.py`: assigns the next subtask to robot or human
- `human_interface.py`: explicit instruction, confirmation, and verification loop
- `vlm_supervisor.py`: orchestration entrypoint above robot and human executors
- `server.py`: ROS2 adapter that exposes planning and verification services
- `simulation.py`: mock collaborative demo built on top of the existing skill simulation
- `bt_executor.py`: subtree interpreter for the hardware-free BT contract tests
- `sandwich_bt_supervisor.yaml`: reference affordance table for the closed-set planner
- `../sandwich_bt_runtime_cpp/trees/*_subtree.xml`: per-step robot BTs used by the contract tests

## Simulation

```bash
uv run lerobot-bt-supervisor-sim
```

This executes:

1. robot subtree `place_first_toast_subtree.xml`
2. human `pour_ingredient`
3. robot subtree `place_second_toast_subtree.xml`

and then exits once the scene reaches `DONE`.

## ROS2 Server

Before running the live server or runner, rebuild the generated supervisor interfaces:

```bash
colcon build --base-paths src --packages-select sandwich_bt_interfaces
source install/setup.bash
```

If `ament_cmake` picks the conda Python and fails on `catkin_pkg`, rebuild with:

```bash
colcon build --base-paths src --packages-select sandwich_bt_interfaces \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

```bash
source install/setup.bash
uv run lerobot-bt-supervisor-server --config_path "$(pwd)/src/sandwich_bt_supervisor/sandwich_bt_supervisor.yaml"
```

This node is intentionally thin. It exposes:

- `/sandwich_supervisor/next_action`
- `/sandwich_supervisor/verify_step`

and delegates planning/verification to the existing supervisor logic.

## Collaborative Runner

The next layer above the supervisor server is a separate runner process:

```bash
source install/setup.bash
uv run lerobot-bt-supervisor-server --config_path "$(pwd)/src/sandwich_bt_supervisor/sandwich_bt_supervisor.yaml"
uv run lerobot-bt-collaborative-runner --mock-scene
```

For the negative path:

```bash
source install/setup.bash
uv run lerobot-bt-supervisor-server --config_path "$(pwd)/src/sandwich_bt_supervisor/sandwich_bt_supervisor.yaml"
uv run lerobot-bt-collaborative-runner --mock-scene --deny-human-confirmation
```

The runner talks to the supervisor only through ROS2 services. In `--mock-scene`
mode it uses:

- a deterministic closed-set scene provider
- `BtXmlRobotExecutor` for robot-owned subtrees
- a manual/mock human confirmation path

By default the robot subtree executor uses an in-process `RunNamedCommand` backend:

```bash
source install/setup.bash
uv run lerobot-bt-supervisor-server --config_path "$(pwd)/src/sandwich_bt_supervisor/sandwich_bt_supervisor.yaml"
uv run lerobot-bt-collaborative-runner --mock-scene --robot-backend in-process
```

To validate the live `RunNamedCommand` contract, start the mock ROS2 skill server in a second terminal:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
uv run lerobot-bt-skill-sim --ros2-service
```

and run the collaborative loop against it:

```bash
source install/setup.bash
uv run lerobot-bt-collaborative-runner --mock-scene --robot-backend ros2
```

If `/sandwich_bt/run_command` is unavailable, the runner exits with code `2`.

Exit codes:

- `0`: task reached `DONE`
- `1`: task aborted or step verification failed
- `2`: ROS2 supervisor service or `RunNamedCommand` service unavailable / no response
- `3`: invalid config, stale generated interfaces, or invalid supervisor output

## ROS2 Probe

For a minimal live check of the service boundary without running the full collaborative loop:

```bash
source install/setup.bash
uv run lerobot-bt-supervisor-probe
```

To probe verification against an explicit observed state:

```bash
source install/setup.bash
uv run lerobot-bt-supervisor-probe \
  --first-toast-on-plate \
  --verify-step place_first_toast
```
