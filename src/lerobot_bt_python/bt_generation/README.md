# bt_generation

This package builds and validates the Behavior Tree (BT) that the robot runs.
It contains **no robot, policy, camera, or torch imports**: it only reads YAML,
validates Linear IR, and renders text artifacts (XML + ROS2 params YAML).

This package is the source of BT task artifacts. The C++ runtime package does
not store task XML/YAML files; it only consumes the generated files passed in at
launch or through `generate_and_run.py`.

`generate.py` and `generate_and_run.py` share parser/provenance helpers in
`cli_utils.py`; registry and plan validation share runtime-bound checks in
`registry.py`; `renderer.py` is the only module that emits BT XML/YAML text.

Robot-skill `verify_after` gates can remain in the validated Linear IR as task
postconditions. By default, `renderer.py` does not emit them as extra
`AwaitScene` leaves immediately after a `DoSkill`, because the C++ `DoSkill`
node already waits for `GetSkillVerification`. Pass
`--explicit-postcondition-gates` for manual experiments that need those leaves
rendered explicitly.

For the runtime-vs-support/offline split, use
[../../../docs/robot_runtime_code_map.md](../../../docs/robot_runtime_code_map.md)
as the source of truth. In short: generation/validation/rendering modules are on
the robot-day path, logging/provenance helpers are support tooling, and
`eval_ablation.py` is offline evaluation only.
