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

`RunNamedCommand` carries:

- request: `kind`, `name`, `timeout_s`
- response: `success`, `status`, `elapsed_s`, `message`
