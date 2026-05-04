# Sandwich BT Interfaces

ROS2 service definitions for the sandwich BT stack.

For build/run instructions and the architecture overview, use the shared guide:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md)

This README focuses on the semantic contract carried by the generated ROS2
interfaces. It intentionally leaves build and launch procedures in the shared
guide.

## Responsibility

This package owns the generated ROS2 contract used between:

- `sandwich_bt_runtime_cpp`
- `sandwich_bt_python`

It does not run anything by itself.

If you change any `.srv` file, rebuild this package before starting the supervisor server,
collaborative runner, or C++ BT runtime.

Use the shared guide for the exact rebuild commands and the conda/CMake workaround:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md), sections `8` and `19`

## Files

- `srv/RunNamedCommand.srv`: request/response contract for BT leaf commands
- `srv/GetSkillVerification.srv`: BT query contract for post-skill verification
- `srv/PlanNextStep.srv`: closed-set planning response for the collaborative supervisor
- `srv/ReportSkillVerification.srv`: external verifier contract for publishing verdicts
- `srv/VerifyStep.srv`: scene-verification response for the collaborative supervisor

`RunNamedCommand` carries:

- request: `kind`, `name`, `timeout_s`
- response: `success`, `status`, `elapsed_s`, `message`

`PlanNextStep` carries:

- request: `goal`, `current_task`, `available_robot_skills`, `available_human_skills`, `first_toast_on_plate`, `ingredient_on_first_toast`, `second_toast_on_top`
- response: `step_name`, `actor`, `reason`, `expected_state`, `confidence`

`VerifyStep` carries:

- request: `step_name`, `first_toast_on_plate`, `ingredient_on_first_toast`, `second_toast_on_top`
- response: `success`, `observed_state`, `failure_reason`, `confidence`

`GetSkillVerification` carries:

- request: `skill_name`
- response: `has_attempt`, `attempt_id`, `status`, `message`, `confidence`

`ReportSkillVerification` carries:

- request: `skill_name`, `attempt_id`, `status`, `message`, `confidence`
- response: `accepted`, `applied_attempt_id`, `message`

## Why This Package Exists

These `.srv` files are the cross-language contract for the sandwich BT stack.
They are compiled into generated Python and C++ bindings that are consumed by
other packages at runtime.

The important implication is that the source `.srv` file itself is not what the
other packages import. They import the generated artifacts under `install/`.
That is why changing a service definition always requires a rebuild before the
rest of the stack can run correctly.

## Contract Boundaries

Each service belongs to a specific boundary:

- `RunNamedCommand` is the BT runtime to Python execution boundary
- `GetSkillVerification` is the BT runtime to Python verification boundary
- `PlanNextStep` is the collaborative runner to supervisor planning boundary
- `ReportSkillVerification` is the external verifier to Python verification boundary
- `VerifyStep` is the collaborative runner to supervisor verification boundary

This separation is deliberate. The low-level BT runtime does not need to know
anything about collaborative planning, and the supervisor does not need to know
how a robot skill is physically executed.

## Field Semantics

### `RunNamedCommand`

- `kind` selects which execution path the Python server uses. Today the valid
  values are effectively `skill` and `recovery`.
- `name` is an opaque identifier from the perspective of the service. The BT
  runtime does not parse it; the Python server resolves it against YAML config.
- `timeout_s = 0` means "use the default timeout configured on the server side".
- `success` is the control signal that the BT runtime converts into BT
  `SUCCESS` or `FAILURE`.
- `status` and `message` are diagnostic context for logs and debugging.
- `elapsed_s` is telemetry, useful for tracing command duration and retries.

### `PlanNextStep`

- The request booleans are a closed-set scene observation, not raw perception.
- `available_robot_skills` and `available_human_skills` let the caller describe
  what the current runtime can actually execute.
- `actor` is expected to be one of `robot`, `human`, `done`, or `abort`.
- `step_name` may be empty for terminal decisions such as `done`.
- `expected_state` tells the caller which scene phase the chosen primitive is
  supposed to achieve.

### `VerifyStep`

- The request asks whether the effect of one named step is now visible in the
  current closed-set scene observation.
- `success` means "the scene now matches what that step was supposed to cause".
- `observed_state` is a human-readable summary of the current scene estimate.
- `failure_reason` explains why verification rejected the step.
- `confidence` is propagated through the supervisor stack but is not currently
  used as a threshold gate by the runner.

### `GetSkillVerification`

- `skill_name` is the BT-facing identifier, so it must match the skill name in
  the Python YAML and the `VerifySkillOutcome` XML node.
- `has_attempt = false` means no completed rollout has yet opened a
  verification window for that skill.
- `attempt_id` is monotonically incremented per skill name to distinguish BT
  retries from stale verifier responses.
- `status` is expected to be one of `UNKNOWN`, `PENDING`, `SUCCESS`, or
  `FAILURE`.

### `ReportSkillVerification`

- `attempt_id = 0` means "apply this verdict to the latest pending attempt".
- Explicit `attempt_id` values let an external verifier avoid writing a stale
  result onto a newer retry.
- `accepted = false` means the Python relay rejected the report, for example
  because the attempt was missing, stale, or already resolved.

## Compatibility Rules

- Renaming a service, request field, or response field is a breaking change for
  both Python and C++ callers.
- Adding a field is also a coordinated change: rebuild the interfaces and update
  every caller that depends on the new information.
- Changing the meaning of existing values, such as what counts as `success` or
  which `actor` strings are valid, is a behavior change across package
  boundaries even if the generated code still compiles.
