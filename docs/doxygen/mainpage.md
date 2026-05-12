# LeRobot BT Stack

The LeRobot BT stack is a VLM-gated BehaviorTree.CPP runtime.

The BT owns ordering, waiting, and retry. The Python server owns skill execution
and VLM check state. The VLM observes the scene and reports waiting states,
final `SUCCESS`/`FAILURE`, or a requested next action.

Runtime path:

1. `lerobot_bt_runtime_cpp` sends `RunNamedCommand`.
2. `lerobot_bt_python` executes a real skill or opens a simulated gate.
3. `lerobot_bt_python` opens a `PENDING` VLM check attempt.
4. `VerifySkillOutcome` polls `GetSkillVerification`.
5. The VLM publishes `/lerobot_bt/vlm_result`.
6. The BT keeps waiting on `RUNNING`, `WAIT_HUMAN`, or
   `MANUAL_INTERVENTION_REQUIRED`.
7. The BT advances on `SUCCESS` or retries the same step on `FAILURE`.
