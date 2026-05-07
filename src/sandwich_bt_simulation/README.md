# Sandwich BT Simulation

Simulation-only package for the VLM-gated sandwich BT stack.

This package provides a mock `RunNamedCommand` server that behaves like the real
Python skill server without moving hardware.

## Commands

Run the default mock sequence:

```bash
lerobot-bt-skill-sim
```

Run the ROS2 mock service:

```bash
lerobot-bt-skill-sim --ros2-service
```

The default sequence is:

```text
initial_scene_ready -> place_first_toast -> pour_ingredient -> place_second_toast
```

`initial_scene_ready` and `pour_ingredient` are `simulated_skill_pending` gates.
The robot skills are mocked, and no deterministic recovery motions are executed.
