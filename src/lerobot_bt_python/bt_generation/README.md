# bt_generation

This package builds and validates the Behavior Tree (BT) that the robot runs.
It contains **no robot, policy, camera, or torch imports**: it only reads YAML,
validates Linear IR, and renders text artifacts (XML + ROS2 params YAML).

For the runtime-vs-support/offline split, use
[../../../docs/robot_runtime_code_map.md](../../../docs/robot_runtime_code_map.md)
as the source of truth. In short: generation/validation/rendering modules are on
the robot-day path, logging/provenance helpers are support tooling, and
`eval_ablation.py` is offline evaluation only.
