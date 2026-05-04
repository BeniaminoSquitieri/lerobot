# Sandwich BT Python

Python execution layer for the sandwich BT stack.

For build/run instructions and the architecture overview, use the shared guide:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md)
- Diagramma I/O del package: [`sandwich_bt_python_io_flow.svg`](./sandwich_bt_python_io_flow.svg)

This README focuses on how the package behaves internally at runtime. It
intentionally does not repeat setup, build, or launch instructions from the
shared guide.

## Responsibility

This package executes commands requested by the C++ BehaviorTree.CPP runtime.

It owns:

- loading skill configs from `sandwich_bt_executor.yaml`
- lazy-loading learned policy runtimes on first use
- running learned policy inference on the robot (ACT and any supported `PreTrainedConfig` family)
- executing scripted recoveries
- maintaining the post-skill verification state for each BT attempt
- exposing ROS2 services that let an external verifier publish `SUCCESS` or `FAILURE`
- returning command results to the BT through `RunNamedCommand`

It does not own:

- BT node ordering
- retry structure
- Groot publication

Those belong to `sandwich_bt_runtime_cpp`.

## Python Files

- `__init__.py`: package export surface for the public config dataclasses
- `config.py`: draccus config dataclasses for skills, recoveries, and the server
- `conditions.py`: helpers that evaluate observation-based success and failure checks
- `executor.py`: learned skill and recovery dispatcher used by the server
- `recoveries.py`: deterministic recovery motions executed between BT attempts
- `server.py`: ROS2 service node for command execution and verification relay
- `simulation.py`: hardware-free mock robot plus an optional ROS2 service harness for local smoke tests
- `verification.py`: in-memory registry for pending/success/failure verification verdicts

## Request Lifecycle

One BT leaf request flows through this package in the following order:

1. `server.py` receives one `RunNamedCommand` request from the C++ BT runtime.
2. The request is dispatched by `kind`:
   `skill` goes to `SkillCommandExecutor.execute_skill`, `recovery` goes to
   `SkillCommandExecutor.execute_named_recovery`.
3. For a learned skill, `executor.py` resolves the command `name` against the
   YAML config and lazily builds a `SkillRuntime` bundle:
   dataset metadata, policy, preprocessor, and postprocessor.
4. The executor enters a control loop:
   read robot observation, apply the observation processor, evaluate whether
   the skill is already done or failed, otherwise predict the next action and
   send it through the robot action processor.
5. For a recovery, `recoveries.py` executes a deterministic sequence of robot
   motions such as pauses, Cartesian deltas, gripper changes, or a reset.
6. If a skill returns `SUCCESS`, the server creates a new verification attempt
   in `PENDING` state. The BT can only move on once an external verifier
   resolves that attempt to `SUCCESS`.
7. The server converts the resulting `CommandResult` into the ROS2 response
   fields `success`, `status`, `elapsed_s`, and `message`.

The important boundary is that this package never decides BT ordering. It only
executes the one named command it was asked to run.

## Runtime Model

- The ROS2 node is created once and exposes three service endpoints:
  `RunNamedCommand`, `GetSkillVerification`, and `ReportSkillVerification`.
- The robot and the processor pipelines are created at server startup, before
  any BT command is accepted.
- Learned skills are lazy-loaded on first use and then cached by name.
- Each invocation resets the policy and processors before execution so that a
  second BT attempt does not inherit model state from a previous attempt.
- `_command_lock` serializes command execution. This package assumes only one
  skill or recovery should touch the robot at a time.
- `verification.py` assigns a monotonic `attempt_id` per skill name. This
  prevents an old verifier response from being applied to a newer BT retry.
- The executor does not know whether the command came from a test subtree or
  the full sandwich tree. It sees only a `name`, `kind`, and optional timeout.
- `simulation.py` provides the same service contract with mock execution so the
  BT can be exercised without hardware.

## Verification Flow

The learned skill and the scene-level success decision are now decoupled.

1. `RunNamedCommand(kind="skill", name="place_first_toast")` executes one
   behavior-cloning rollout and returns once that rollout stops.
2. The server records `place_first_toast` attempt `N` as `PENDING`.
3. The BT runtime enters `VerifySkillOutcome(skill_name="place_first_toast")`
   and polls `GetSkillVerification`.
4. An external verifier, typically a VLM wrapper, calls
   `ReportSkillVerification` with `status=SUCCESS` or `status=FAILURE`.
5. The verification leaf returns BT `SUCCESS` or `FAILURE`.
6. `RetryUntilSuccessful num_attempts="-1"` in the XML decides whether to
   advance to the next primitive or rerun recovery plus skill.

This keeps the BT responsible for retry logic while leaving perception outside
the low-level skill executor.

## Manual Verification Hook

Until a real VLM client is integrated, the verifier can be emulated from a
terminal with plain ROS2 service calls:

```bash
ros2 service call /sandwich_bt/get_skill_verification \
  sandwich_bt_interfaces/srv/GetSkillVerification \
  "{skill_name: place_first_toast}"
```

```bash
ros2 service call /sandwich_bt/report_skill_verification \
  sandwich_bt_interfaces/srv/ReportSkillVerification \
  "{skill_name: place_first_toast, attempt_id: 0, status: SUCCESS, message: 'scene ok', confidence: 0.95}"
```

`attempt_id: 0` means "apply this verdict to the latest pending attempt".

## Skill Termination Semantics

Skill termination is configured, not hardcoded.

- `transition.mode = timeout` means the skill succeeds when the timeout is
  reached unless a failure condition fired earlier.
- `transition.mode = all_conditions` means the skill succeeds only when all
  configured success conditions are met before timeout.
- `transition.mode = all_conditions_or_timeout` means success conditions can
  end the skill early, but timeout still counts as success.
- `transition.mode = until_success` means the skill keeps running until all
  configured success conditions become true. In this mode the timeout is
  ignored, so at least one success condition is required.
- `failure_conditions` are checked on every loop iteration and immediately end
  the command with `FAILURE`.
- A service request may override the configured timeout through `timeout_s`.

This design lets the same execution loop support purely time-based skills and
skills that should stop once some observation predicate becomes true.

## Configuration Semantics

`sandwich_bt_executor.yaml` is the contract between BT command names and actual
runtime behavior.

- `skills[].name` must match the `command_name` used in the BT XML.
- `verification_query_service_name` is what the BT runtime polls after each
  skill attempt.
- `verification_report_service_name` is what the external verifier uses to
  publish the final scene verdict for the latest or explicit `attempt_id`.
- `skills[].policy` is an ordinary LeRobot `PreTrainedConfig` subclass. The
  policy family must be imported in `config.py` so draccus can deserialize it.
- `skills[].dataset_repo_id`, `dataset_root`, and `dataset_revision` are used
  to load dataset metadata and statistics, not to replay demonstrations.
- `rename_map` exists to bridge naming mismatches between dataset features and
  the observation/action keys produced by the live robot stack.
- `robot_action_processor` and `robot_observation_processor` are server-level
  adapters around the skill loop. They are a good place for safety clipping,
  coordinate conversion, or key normalization that should apply to every skill.
- `recoveries[]` define named deterministic motions. The BT refers to them only
  by name and never sees their internal steps.

## Extension Points

- Add a new learned primitive by adding one `skills[]` entry and making sure
  the BT XML uses the same command name.
- Swap in a real VLM verifier by pointing it at `ReportSkillVerification`.
  The Python server already keeps the BT-facing state machine.
- Add a new policy family by importing its config class in `config.py`, so the
  YAML can instantiate it through `PreTrainedConfig`.
- Add a new recovery primitive kind by extending `RecoveryStepConfig` validation
  in `config.py` and the execution logic in `recoveries.py`.
- Add richer success or failure predicates by extending `conditions.py`.

## Runtime Config

- `sandwich_bt_executor.yaml`: runtime config loaded by `server.py`
- `sandwich_bt_executor_headless.yaml`: mock-friendly variant used for headless/local testing
