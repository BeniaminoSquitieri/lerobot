# Sandwich BT Python

Python execution layer for the VLM-gated sandwich BT stack.

For run commands and the stack overview, use:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md)

## Responsibility

This package owns:

- loading skill configs from `sandwich_bt_executor.yaml`;
- lazy-loading learned policy runtimes on first use;
- running BC/ACT policy inference on the robot;
- opening a `PENDING` VLM check attempt after each successful skill or gate;
- exposing BT-facing ROS2 services plus verifier-facing ROS2 topics.

This package intentionally does not implement deterministic Panda recovery
motions. A VLM `FAILURE` is handled by the BT retrying the same BC skill.

## Active Command Kinds

- `skill`: run a configured learned primitive.
- `simulated_skill`: simulate a primitive and auto-resolve the VLM check as `SUCCESS`.
- `simulated_skill_pending`: open a pending VLM check attempt without robot motion.

`recovery` and `simulated_recovery` are not part of the active runtime path.

## Request Lifecycle

1. `sandwich_bt_runner` calls `/sandwich_bt/run`.
2. `server.py` dispatches `kind="skill"` to `SkillCommandExecutor.execute_skill`.
3. The executor runs one policy rollout and returns `CommandResult`.
4. If the command succeeded, `server.py` creates a VLM check attempt with
   status `PENDING`.
5. `server.py` publishes a JSON request on `/sandwich_bt/vlm_request`.
6. `VerifySkillOutcome` polls `/sandwich_bt/vlm_state` and returns
   BT `RUNNING` while the attempt remains in a waiting state.
7. A manual tester or VLM publishes JSON on `/sandwich_bt/vlm_result`
   with `RUNNING`, `WAIT_HUMAN`, `MANUAL_INTERVENTION_REQUIRED`, `SUCCESS`, or
   `FAILURE`.
8. The BT advances on `SUCCESS` or retries the same skill on `FAILURE`.

## Files

- `config.py`: draccus config dataclasses for skills and server options.
- `executor.py`: learned skill executor.
- `server.py`: ROS2 service node for command execution and VLM check relay.
- `simulation.py`: compatibility wrapper for `sandwich_bt_simulation.skill_server`.
- `verification.py`: in-memory registry for VLM pending/success/failure verdicts.
- `vlm_stub.py`: optional topic-to-topic helper for manual VLM testing.

## Manual VLM Result

Watch the verifier requests emitted by the server:

```bash
ros2 topic echo /sandwich_bt/vlm_request
```

Advance the BT manually, using the same topic a real VLM will use:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"scene ok\"}'}"
```

Publish `FAILURE` instead of `SUCCESS` to make the enclosing
`RetryUntilSuccessful` restart that BT stage. `attempt_id: 0` applies the
verdict to the latest pending attempt for that skill.

Publish waiting states to keep the BT blocked:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pour_ingredient\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"message\":\"human is pouring\"}'}"
```

The same topic can carry richer VLM reasons:

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"object_missing\",\"required_human_action\":\"put toast back in reachable area\"}'}"
```

The legacy `/sandwich_bt/vlm_result_legacy` service still exists for
compatibility, but new manual tools and VLM implementations should use topics.

VLM check attempts have a configurable timeout. If the VLM/manual verifier
does not report `SUCCESS` before `vlm_timeout_s`, the Python registry
marks the attempt as `FAILURE`; the BT VLM check node then returns failure
and the XML retry wrapper reruns the same skill. Set `vlm_timeout_s: 0`
to disable this automatic timeout.

## Current Two-Skill Test

Use `sandwich_tree_two_real_skills_manual_vlm.xml` for the current temporary
task with two real BC skills and manual VLM verdicts. Wait for each
`/sandwich_bt/vlm_request` before publishing the corresponding report.

Expected manual report order:

```text
initial_scene_ready SUCCESS -> starts place_first_toast
place_first_toast SUCCESS -> opens the human pouring gate
pour_ingredient WAIT_HUMAN/RUNNING -> BT keeps waiting
pour_ingredient SUCCESS -> starts place_second_toast
place_second_toast SUCCESS -> completes the BT
```

Any `FAILURE` verdict for a requested stage makes the XML retry block rerun that
same gate or skill. The future real VLM should publish the same JSON reports on
the same topic, so the BT does not change when manual CLI publishing is replaced.
