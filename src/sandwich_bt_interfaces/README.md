# Sandwich BT Interfaces

ROS2 service definitions for the active VLM-gated sandwich BT stack.

This package only generates service bindings. It does not run nodes.

## Services

- `RunNamedCommand.srv`: C++ BT runtime asks the Python server to run one skill
  or open one VLM/manual gate.
- `GetSkillVerification.srv`: C++ BT runtime polls the latest VLM check state
  for one skill/gate. The default endpoint is `/sandwich_bt/vlm_state`.
- `ReportSkillVerification.srv`: legacy compatibility path for reporting
  `SUCCESS` or `FAILURE`. The default endpoint is `/sandwich_bt/vlm_result_legacy`.

## Boundaries

```text
sandwich_bt_runtime_cpp -> RunNamedCommand -> sandwich_bt_python
sandwich_bt_runtime_cpp -> GetSkillVerification -> sandwich_bt_python
sandwich_bt_python      -> /sandwich_bt/vlm_request -> VLM/manual verifier
VLM/manual verifier     -> /sandwich_bt/vlm_result  -> sandwich_bt_python
```

## VLM Status

`GetSkillVerification` may return:

- `UNKNOWN`: no usable state exists for that skill/gate.
- `PENDING`: the BT must keep waiting.
- `RUNNING`: the VLM sees an action in progress; the BT keeps waiting.
- `WAIT_HUMAN`: the BT is intentionally waiting for human progress.
- `MANUAL_INTERVENTION_REQUIRED`: a human must fix the scene before continuing.
- `SUCCESS`: the BT can advance.
- `FAILURE`: the BT returns failure and the XML retry block retries the same
  skill/gate.

`/sandwich_bt/vlm_result` accepts waiting updates and final verdicts:

- `PENDING`
- `RUNNING`
- `WAIT_HUMAN`
- `MANUAL_INTERVENTION_REQUIRED`
- `SUCCESS`
- `FAILURE`

It may also send `next_action` in the JSON topic payload. The Python server maps
`CONTINUE` to `SUCCESS`, `RETRY_SKILL` to `FAILURE`, `WAIT_HUMAN` to
`WAIT_HUMAN`, and `REQUEST_MANUAL_INTERVENTION` to
`MANUAL_INTERVENTION_REQUIRED`.

## Rebuild Rule

If any `.srv` file changes, rebuild and source the workspace:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --base-paths src --packages-up-to sandwich_bt_runtime_cpp
source install/setup.bash
```
