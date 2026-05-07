# Sandwich BT Python

Python execution layer for the VLM-gated sandwich BT stack.

For run commands and the stack overview, use:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md)

## Responsibility

This package owns:

- loading skill configs from `sandwich_bt_executor.yaml`;
- lazy-loading learned policy runtimes on first use;
- running BC/ACT policy inference on the robot;
- opening a `PENDING` verification attempt after each successful skill or gate;
- exposing BT-facing ROS2 services plus verifier-facing ROS2 topics.

This package intentionally does not implement deterministic Panda recovery
motions. A VLM `FAILURE` is handled by the BT retrying the same BC skill.

## Active Command Kinds

- `skill`: run a configured learned primitive.
- `simulated_skill`: simulate a primitive and auto-resolve verification as `SUCCESS`.
- `simulated_skill_pending`: open a pending verification attempt without robot motion.

`recovery` and `simulated_recovery` are not part of the active runtime path.

## Request Lifecycle

1. `sandwich_bt_runner` calls `/sandwich_bt/run_command`.
2. `server.py` dispatches `kind="skill"` to `SkillCommandExecutor.execute_skill`.
3. The executor runs one policy rollout and returns `CommandResult`.
4. If the command succeeded, `server.py` creates a verification attempt with
   status `PENDING`.
5. `server.py` publishes a JSON request on `/sandwich_bt/verification_request`.
6. `VerifySkillOutcome` polls `/sandwich_bt/get_skill_verification` and returns
   BT `RUNNING` while the attempt remains `PENDING`.
7. A manual tester or VLM publishes JSON on `/sandwich_bt/verification_report`
   with `SUCCESS` or `FAILURE`.
8. The BT advances on `SUCCESS` or retries the same skill on `FAILURE`.

## Files

- `config.py`: draccus config dataclasses for skills and server options.
- `executor.py`: learned skill executor.
- `server.py`: ROS2 service node for command execution and verification relay.
- `simulation.py`: compatibility wrapper for `sandwich_bt_simulation.skill_server`.
- `verification.py`: in-memory registry for pending/success/failure verdicts.
- `vlm_stub.py`: optional topic-to-topic helper for manual VLM testing.

## Manual Verification

Watch the verifier requests emitted by the server:

```bash
ros2 topic echo /sandwich_bt/verification_request
```

Advance the BT manually, using the same topic a real VLM will use:

```bash
ros2 topic pub --once /sandwich_bt/verification_report std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"scene ok\",\"confidence\":0.95}'}"
```

Publish `FAILURE` instead of `SUCCESS` to make the enclosing
`RetryUntilSuccessful` restart that BT stage. `attempt_id: 0` applies the
verdict to the latest pending attempt for that skill.

The legacy `/sandwich_bt/report_skill_verification` service still exists for
compatibility, but new manual tools and VLM implementations should use topics.
