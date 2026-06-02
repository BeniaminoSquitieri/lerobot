# lerobot_bt_interfaces

This ROS 2 package defines the typed service boundary between the C++
BehaviorTree.CPP runner and the Python LeRobot skill server.

It contains only interface definitions. It should not contain policy loading,
robot execution, BT XML, VLM business logic, or task-specific configuration.

Classification: every file here is part of the real robot runtime path (P0). It
is a frozen contract and must not change without coordinated runtime updates.
See [../../docs/robot_runtime_code_map.md](../../docs/robot_runtime_code_map.md)
for the full runtime-vs-test map.

## Who Uses This Package

| Consumer | How it uses the interfaces |
| --- | --- |
| `../lerobot_bt_runtime_cpp` | Calls `RunNamedCommand` from BT leaves and polls `GetSkillVerification` while waiting for scene verdicts. |
| `../lerobot_bt_python` | Implements the services in `server.py` and accepts legacy verifier reports through `ReportSkillVerification`. |
| External verifier tools | May publish topic JSON directly, or use the legacy report service when compatibility is needed. |

## Services

### `RunNamedCommand.srv`

C++ BT -> Python server command request.

Request:

- `kind`: command path. Current values are `skill` and `vlm_gate_pending`.
- `name`: configured skill or gate name.
- `timeout_s`: optional timeout override. `0` lets the Python config decide.

Response:

- `success`: boolean outcome consumed by the BT leaf.
- `status`: detailed result such as `SUCCESS`, `FAILURE`, `TIMEOUT`, or `ERROR`.
- `elapsed_s`: command duration measured by Python.
- `message`: human-readable diagnostics.

### `GetSkillVerification.srv`

C++ BT -> Python server polling request for the latest VLM/gate state.

Request:

- `skill_name`: skill or gate whose latest attempt should be inspected.

Response:

- `has_attempt`: whether Python has seen this skill/gate.
- `attempt_id`: monotonic attempt id assigned by Python.
- `status`: `UNKNOWN`, `RUNNING`, `SUCCESS`, or `FAILURE`.
- `message`: current status detail.

### `ReportSkillVerification.srv`

Legacy external verifier -> Python server update path.

Prefer publishing JSON to `/lerobot_bt/vlm_result` for new integrations. Keep
this service compatible while legacy clients exist.

## Commands

Build and interface-inspection commands are centralized in `../README.md`.

## Compatibility Rules

- Do not rename fields casually. Both the C++ BT runner and Python server use
  these generated types.
- Additive fields still require coordinated C++ and Python changes.
- Keep `kind` string values stable: `skill` and `vlm_gate_pending` are part of
  the runtime contract.
- New task names belong in BT/Python YAML, not in `.srv` files.
