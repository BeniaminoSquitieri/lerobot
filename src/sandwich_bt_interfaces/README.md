# Sandwich BT Interfaces

ROS2 service definitions for the sandwich BT stack.

For build/run instructions and the architecture overview, use the shared guide:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md)

## Responsibility

This package owns the generated ROS2 contract used between:

- `sandwich_bt_runtime_cpp`
- `sandwich_bt_python`

It does not run anything by itself.

## Files

- `srv/RunNamedCommand.srv`: request/response contract for BT leaf commands
- `srv/PlanNextStep.srv`: closed-set planning response for the collaborative supervisor
- `srv/VerifyStep.srv`: scene-verification response for the collaborative supervisor

`RunNamedCommand` carries:

- request: `kind`, `name`, `timeout_s`
- response: `success`, `status`, `elapsed_s`, `message`

`PlanNextStep` carries:

- request: `goal`, `current_task`, `available_robot_skills`, `available_human_skills`
- response: `step_name`, `actor`, `reason`, `expected_state`, `confidence`

`VerifyStep` carries:

- request: `step_name`
- response: `success`, `observed_state`, `failure_reason`, `confidence`
