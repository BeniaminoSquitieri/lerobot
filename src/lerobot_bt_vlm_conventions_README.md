# VLM, BT, and BC Conventions

This page defines the shared contract used by the LeRobot BT stack and by the
additional scene-gated BTs.

## Roles

- BT: owns the procedural task order, retry boundaries, and which skill or gate
  is next.
- BC skill: executes one trained manipulation primitive.
- VLM: verifies whether the expected scene state was reached after a gate or
  skill.

The VLM is not a planner in this architecture. It does not choose the next
object, select the next skill, or rewrite the task. It only reports whether the
current requested scene condition is acceptable.

## Standard Flow

```text
BT opens a gate or runs a BC skill
Python server opens a VLM check attempt
VLM/manual verifier reports a verdict on /lerobot_bt/vlm_result
BT advances on SUCCESS or retries on FAILURE
```

The common BT pattern is:

```text
OpenVLMGate(gate_name=scene_i_ready)
WaitForVLMVerdict(check_name=scene_i_ready)
RunRobotSkill(skill_i)
WaitForVLMVerdict(check_name=skill_i)
```

Task completion is also a gate:

```text
OpenVLMGate(gate_name=task_complete)
WaitForVLMVerdict(check_name=task_complete)
```

## Verdict Statuses

- `SUCCESS`: the expected scene state was reached; the BT can continue.
- `FAILURE`: the expected scene state was not reached; the current XML retry
  block should rerun.
- `RUNNING` or `PENDING`: the verifier is not ready to make a terminal decision.
- `WAIT_HUMAN`: human action is still in progress; the BT remains blocked.
- `MANUAL_INTERVENTION_REQUIRED`: a human needs to fix the scene before the BT
  can continue safely.

The VLM topic also accepts scene-oriented tokens:

```text
scene_0_ready -> SUCCESS
scene_1_ready -> SUCCESS
task_complete -> SUCCESS
anomaly_detected -> FAILURE
human_help_required -> MANUAL_INTERVENTION_REQUIRED
```

## Topic Payload

The verifier publishes JSON inside a `std_msgs/msg/String`:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"scene ok\"}'}"
```

Required fields:

- `skill_name`: the gate or skill name printed on `/lerobot_bt/vlm_request`.
- `attempt_id`: the attempt id printed on `/lerobot_bt/vlm_request`; `0` means
  "latest pending attempt for this name".
- `status`: one of the verdict statuses above.

Useful optional fields:

- `message`
- `scene_id`
- `scene_state`
- `failure_reason`
- `required_human_action`
- `next_action`

`next_action` can be used instead of `status`:

```text
CONTINUE -> SUCCESS
RETRY_SKILL -> FAILURE
WAIT_HUMAN -> WAIT_HUMAN
REQUEST_MANUAL_INTERVENTION -> MANUAL_INTERVENTION_REQUIRED
```

## Multi-Object Tasks

For now, multi-object tasks should be explicit at the BT level. If a task has
several objects, model them as several BT phases or several configured skill
names once the objects are known.

A single BC skill verdict should mean that the current primitive achieved its
own expected transition, for example "this trash item is in the bin". It should
not secretly mean that an entire object category is complete unless the skill
was explicitly trained and documented as a category-level primitive.

## Dataset Convention

Collect BC datasets as scene transitions:

```text
scene_i:
  required initial state

BC skill:
  one manipulation primitive

scene_i+1:
  expected final state
```

Example:

```text
Dataset: open_drawer
scene_i:
  drawer_closed
  handle_visible
  workspace_clear

BC skill:
  open_drawer

scene_i+1:
  drawer_open
  inner_space_visible
  gripper_free
```
