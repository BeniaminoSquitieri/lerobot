# BT/VLM Cleanup Inventory

Scope: active BT/VLM/LeRobot flow inventory before any cleanup refactor.

## 1) bt_vlm_bridge.py

- Item: src/lerobot_bt_python/bt_vlm_bridge.py
- References found:
  - pyproject console script: lerobot-bt-vlm-bridge
  - BT Python/runtime docs and architecture diagrams
  - VLM server requirements (optional compatibility path)
- Classification: Optional compatibility utility (not required by the current JSON-native active flow).
- Deletion risk: Medium.
- Recommended action: Keep for now; if deprecated later, preserve compatibility alias first.
- Safe for immediate cleanup: No.

## 2) ReportSkillVerification.srv

- Item: src/lerobot_bt_interfaces/srv/ReportSkillVerification.srv
- References found:
  - Included in rosidl generation (CMake)
  - Imported/served by SkillCommandServer
  - Mentioned in interface and BT docs/diagrams
- Classification: Legacy compatibility runtime interface still wired in server/build.
- Deletion risk: Medium-High.
- Recommended action: Do not remove now; deprecate first, then remove with coordinated interface/runtime change.
- Safe for immediate cleanup: No.

## 3) /lerobot_bt/vlm_result_legacy usage

- Item: Legacy VLM result service endpoint and config wiring.
- References found:
  - Default field in SkillCommandServerConfig
  - Present in executor YAML profiles
  - Service created and handled in server.py
  - Documented manual call path in BT README
- Classification: Legacy runtime compatibility path, not required for active topic-based VLM flow.
- Deletion risk: Medium-High.
- Recommended action: Keep until explicit deprecation window and test coverage are in place.
- Safe for immediate cleanup: No.

## 4) Legacy BT node registrations (RunNamedCommandNode / RunRobotSkillNode / OpenVLMGateNode)

- Item: legacy node family in run_named_command_node.*
- References found:
  - Source/header and CMake target inclusion
  - Current main registers only AwaitScene and DoSkill builders
  - Active XML trees use AwaitScene/DoSkill only
- Classification: Legacy implementation compiled in target; registration already inactive in runtime behavior.
- Deletion risk: Low-Medium (build coupling must be checked before removal).
- Recommended action: No-op for "stop registering" (already true); consider later quarantine/removal in isolated commit with build check.
- Safe for immediate cleanup: Not yet.

## 5) metareader

- Item: top-level metareader package/directory.
- References found:
  - Imported by teleoperator module
  - Used in teleoperator tests
  - Referenced by teleop configs/scripts
- Classification: Active optional subsystem (teleoperation), outside BT/VLM runtime path.
- Deletion risk: High.
- Recommended action: Do not touch in BT cleanup.
- Safe for immediate cleanup: No.

## 6) dummy_action_server.py

- Item: scripts/dummy_action_server.py
- References found:
  - No packaging/runtime/test imports found
  - Self-referential usage examples only
- Classification: Standalone dev utility, currently unused by active BT/VLM flow.
- Deletion risk: Low-Medium (possible manual external use).
- Recommended action: Quarantine (move to clearly named legacy/dev_tools location), not hard delete.
- Safe for immediate cleanup: Yes (quarantine only).
- Update: quarantined at scripts/legacy/dummy_action_server.py with compatibility stub kept at scripts/dummy_action_server.py.

## 7) groot2_monitor.py

- Item: src/lerobot_bt_python/groot2_monitor.py
- References found:
  - pyproject console script: lerobot-bt-groot2
  - Self-documented as entrypoint for Groot monitoring
- Classification: Dev/ops utility (monitoring), optional but packaged.
- Deletion risk: Medium.
- Recommended action: Keep; if relocated, preserve entrypoint compatibility.
- Safe for immediate cleanup: No.

## 8) src/lerobot_bt_diagrams/lerobot_bt_runtime_cpp/

- Item: requested subpath under src/lerobot_bt_diagrams
- References found:
  - No such path present in workspace
  - Existing diagram paths are:
    - src/lerobot_bt_diagrams/
    - src/lerobot_bt_runtime_cpp/diagrams/
- Classification: Non-existent path in current repository state.
- Deletion risk: None.
- Recommended action: No-op.
- Safe for immediate cleanup: Not applicable.

## Immediate Cleanup Candidate (conservative)

- Approved candidate: scripts/dummy_action_server.py
- Action style: Move to quarantine location; do not delete outright.

## Compatibility seam options

- Structural extraction of legacy service registration is deferred in this pass.
- Reason: no boolean registration field currently exists; `legacy_vlm_result_service` is a service-name string, not an enable/disable toggle.
- A future pass should add an explicit boolean field with a default that preserves current behavior before any registration gating is introduced.

## Pass 1 outcome

- Landed:
  - Added source-derived contract doc at `docs/refactor/bt_vlm_contract.md`.
  - Added pure unit/contract tests at `tests/lerobot_bt/test_vlm_contract.py`.
  - Added narrow deprecation markers: one-shot warning on bridge entrypoint invocation, one-shot warning on legacy service handler invocation, and deprecated comment over `legacy_vlm_result_service`.
  - Quarantined `scripts/dummy_action_server.py` to `scripts/legacy/dummy_action_server.py` and kept a compatibility stub at the original path.
  - Stripped mechanical `# Comment:` lines from selected BT Python modules with per-file diff/AST gates.
- Explicitly skipped:
  - Original Batch 6 structural extraction/gating in `server.py`.
  - `.srv` edits, C++ edits, executor YAML edits, BT XML edits, metareader changes, and upstream `src/lerobot/**` policy/dataset/robot module changes.
- Why original Batch 6 was blocked:
  - The planned registration gating assumed an existing boolean toggle that does not exist in current config shape.
- Checks run:
  - `conda run -n lerobot python -m pytest tests/lerobot_bt -svv` (green after ROS2-binding skips).
  - `python3 -c "import ast, pathlib; [ast.parse(p.read_text()) for p in pathlib.Path('src/lerobot_bt_python').glob('*.py')]"` (green).
- Optional checks unavailable in this environment:
  - `uv run pytest tests -svv --maxfail=10` (uv not installed).
  - `colcon build` package checks (colcon not available in this shell).
  - Entry-point smoke checks not run because ROS2 runtime tooling is unavailable here.
