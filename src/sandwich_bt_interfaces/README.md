# Sandwich BT Interfaces

ROS2 service definitions for the active VLM-gated sandwich BT stack.

This package only generates service bindings. It does not run nodes.

## Services

- `RunNamedCommand.srv`: C++ BT runtime asks the Python server to run one skill
  or open one simulated verification gate.
- `GetSkillVerification.srv`: C++ BT runtime polls the latest verification state
  for one skill/gate.
- `ReportSkillVerification.srv`: legacy compatibility path for reporting
  `SUCCESS` or `FAILURE`.

## Boundaries

```text
sandwich_bt_runtime_cpp -> RunNamedCommand -> sandwich_bt_python
sandwich_bt_runtime_cpp -> GetSkillVerification -> sandwich_bt_python
sandwich_bt_python      -> /sandwich_bt/verification_request -> VLM/manual verifier
VLM/manual verifier     -> /sandwich_bt/verification_report  -> sandwich_bt_python
```

## Verification Status

`GetSkillVerification` may return:

- `UNKNOWN`: no usable state exists for that skill/gate.
- `PENDING`: the BT must keep waiting.
- `SUCCESS`: the BT can advance.
- `FAILURE`: the BT returns failure and the XML retry block retries the same
  skill/gate.

`/sandwich_bt/verification_report` accepts only final verdicts:

- `SUCCESS`
- `FAILURE`

The VLM should not report `PENDING` or `RUNNING`; those are internal waiting
states.

## Rebuild Rule

If any `.srv` file changes, rebuild and source the workspace:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --base-paths src --packages-up-to sandwich_bt_runtime_cpp
source install/setup.bash
```
