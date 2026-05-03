# Sandwich BT Interfaces

ROS2 service definitions for the sandwich BT stack.

For build/run instructions and the architecture overview, use the shared guide:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md)

## Responsibility

This package owns the generated ROS2 contract used between:

- `sandwich_bt_runtime_cpp`
- `sandwich_bt_python`

It does not run anything by itself.

If you change any `.srv` file, rebuild this package before starting the supervisor server,
collaborative runner, or C++ BT runtime:

```bash
colcon build --base-paths src --packages-select sandwich_bt_interfaces
source install/setup.bash
```

In a conda environment, if `catkin_pkg` is missing from the Python selected by CMake, rebuild with:

```bash
colcon build --base-paths src --packages-select sandwich_bt_interfaces \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

## Files

- `srv/RunNamedCommand.srv`: request/response contract for BT leaf commands
- `srv/PlanNextStep.srv`: closed-set planning response for the collaborative supervisor
- `srv/VerifyStep.srv`: scene-verification response for the collaborative supervisor

`RunNamedCommand` carries:

- request: `kind`, `name`, `timeout_s`
- response: `success`, `status`, `elapsed_s`, `message`

`PlanNextStep` carries:

- request: `goal`, `current_task`, `available_robot_skills`, `available_human_skills`, `first_toast_on_plate`, `ingredient_on_first_toast`, `second_toast_on_top`
- response: `step_name`, `actor`, `reason`, `expected_state`, `confidence`

`VerifyStep` carries:

- request: `step_name`, `first_toast_on_plate`, `ingredient_on_first_toast`, `second_toast_on_top`
- response: `success`, `observed_state`, `failure_reason`, `confidence`
