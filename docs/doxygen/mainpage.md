# Sandwich BT Stack

The sandwich BT stack is a VLM-gated BehaviorTree.CPP runtime.

The BT owns ordering and retry. The Python server owns skill execution and
verification state. The VLM observes the scene and reports final `SUCCESS` or
`FAILURE` verdicts.

Runtime path:

1. `sandwich_bt_runtime_cpp` sends `RunNamedCommand`.
2. `sandwich_bt_python` executes a real skill or opens a simulated gate.
3. `sandwich_bt_python` opens a `PENDING` verification attempt.
4. `VerifySkillOutcome` polls `GetSkillVerification`.
5. The VLM calls `ReportSkillVerification`.
6. The BT advances on `SUCCESS` or retries the same step on `FAILURE`.
