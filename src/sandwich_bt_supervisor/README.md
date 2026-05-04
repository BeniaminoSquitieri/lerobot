# Sandwich BT Supervisor

Closed-set collaborative supervisor for the sandwich task.

This package sits above the existing BT runtime. It does not replace the
BehaviorTree.CPP layer. It decides which subtask comes next, assigns that
subtask to either the robot or the human, and verifies the scene after each
handoff. In the hardware-free simulation, robot-owned steps are executed
through per-step BT XML subtrees instead of calling the skill executor
directly.

This README focuses on the supervisor's internal logic and process boundaries.
It intentionally avoids repeating setup and launch instructions from the shared
guide.

## Responsibility

It owns:

- minimal scene-state estimation for the sandwich task
- closed-set task allocation across `robot` and `human`
- explicit human confirmation before human-owned steps succeed
- scene verification after each step
- a hardware-free simulation path for the `robot -> human -> robot` loop

It does not own:

- low-level robot control
- ACT or GR00T policy inference
- BT retries and local recoveries
- live VLM perception

Those still belong to `sandwich_bt_python` and `sandwich_bt_runtime_cpp`.

## Files

- `planner_schema.py`: planner config and response schemas
- `scene_state.py`: closed-set scene-state estimator and verification rules
- `task_allocator.py`: assigns the next subtask to robot or human
- `human_interface.py`: explicit instruction, confirmation, and verification loop
- `vlm_supervisor.py`: orchestration entrypoint above robot and human executors
- `server.py`: ROS2 adapter that exposes planning and verification services
- `simulation.py`: mock collaborative demo built on top of the existing skill simulation
- `bt_executor.py`: subtree interpreter for the hardware-free BT contract tests
- `sandwich_bt_supervisor.yaml`: reference affordance table for the closed-set planner
- `../sandwich_bt_runtime_cpp/trees/*_subtree.xml`: per-step robot BTs used by the contract tests

## Mental Model

This package is a task-level decision layer above the primitive BT runtime.

- It does not tick BehaviorTree.CPP directly.
- It does not load learned robot checkpoints.
- It does not move the robot by itself from the ROS2 server process.

Instead, it answers two questions repeatedly:

1. given the current closed-set sandwich state, what step should happen next?
2. after a step was attempted, did the scene actually change as expected?

The BT runtime remains the execution mechanism for robot-owned primitives. The
supervisor decides when those primitives should be requested.

## Internal Flow

The normal collaborative loop is:

1. observe the current closed-set scene
2. estimate the scene phase
3. choose the unique primitive associated with that phase
4. assign that primitive to `robot` or `human`
5. execute the chosen step through a robot or human executor
6. verify that the resulting scene matches the expected effect
7. repeat until the supervisor returns `done` or `abort`

The package separates these responsibilities so the planning logic is testable
without binding it directly to ROS2, Panda hardware, or a VLM.

## Main Components

### `planner_schema.py`

Defines the closed-set domain and enforces config invariants.

- `TaskPrimitive` describes one allowed subtask.
- `SupervisorConfig` requires exactly one primitive per active scene phase.
- Robot primitives default `robot_skill` to their own name.
- Human primitives default `human_instruction` from the primitive name.

This file is the place where "what states and decisions exist" is made explicit.

### `scene_state.py`

Maps a simple boolean observation into one of the scene phases:

- `NEED_FIRST_TOAST`
- `NEED_POURING`
- `NEED_SECOND_TOAST`
- `DONE`

It also implements per-step verification rules. That keeps "what counts as
task progress" deterministic and inspectable.

### `task_allocator.py`

Turns a scene estimate into the next `PlanStepDecision`.

It does not search over arbitrary plans. It uses the configured closed-set
mapping from scene phase to primitive, then checks whether the required robot
skill or human executor is available. If not, it returns `abort` with a reason.

### `vlm_supervisor.py`

Holds the domain-level supervisor object.

It combines scene observation, scene estimation, task allocation, and step
dispatch. This is the highest-level object that still knows nothing about ROS2
wire formats.

### `server.py`

Provides the ROS2 adapter for planning and verification services only.

The key design choice is that the server intentionally uses unavailable robot
and human executors as guard rails. It should answer planning questions, not
silently start moving the robot. Actual execution belongs to the collaborative
runner.

### `collaborative_runner.py`

Owns the live loop that talks to the supervisor services and performs step
execution.

It is responsible for:

- waiting for supervisor services
- requesting the next action
- dispatching robot or human execution
- calling verification after execution
- turning failures into process exit codes

### `bt_executor.py`

Implements a minimal subtree interpreter used in contract tests and mock
collaborative runs.

It supports only the BT constructs used by this repository:

- `RetryUntilSuccessful`
- `Sequence`
- `RunNamedCommand`

This lets the supervisor validate robot-owned subtree behavior without needing
the full C++ BT runtime in-process.

### `named_command_backends.py`

Defines how robot-owned subtree commands are executed in collaborative mode.

- `InProcessMockNamedCommandBackend` runs against the mock Python service
  directly in the same process.
- `Ros2NamedCommandBackend` calls the live `/sandwich_bt/run_command` service.

That abstraction lets the collaborative runner exercise the same subtree logic
against either mock or live execution boundaries.

## Server Versus Runner

The most important architectural split in this package is:

- the supervisor server plans and verifies
- the collaborative runner executes and loops

This split prevents the planning service from taking ownership of robot control
and makes it possible to test the reasoning layer independently from execution.

## Configuration Semantics

`sandwich_bt_supervisor.yaml` is not just a list of steps. It defines the
closed-set task graph.

- Each active phase must map to exactly one `TaskPrimitive`.
- Robot primitives should point to the BT subtree that realizes that step.
- Human primitives should carry the instruction text that a human executor will
  present or confirm.
- `available_robot_skills` and `available_human_skills` describe capability
  availability, not scene state.
- `human_confirmation_timeout_s` governs how long the higher-level loop allows a
  human step to remain pending.

## Simulation

For startup and execution commands, use the shared guide:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md), section `15`

This executes:

1. robot subtree `place_first_toast_subtree.xml`
2. human `pour_ingredient`
3. robot subtree `place_second_toast_subtree.xml`

and then exits once the scene reaches `DONE`.

## ROS2 Server

Before running the live server or runner, rebuild the generated supervisor interfaces.

Use the shared guide for the exact build and startup commands:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md), sections `8`, `15.1`, and `19`

This node is intentionally thin. It exposes:

- `/sandwich_supervisor/next_action`
- `/sandwich_supervisor/verify_step`

and delegates planning/verification to the existing supervisor logic.

## Collaborative Runner

The next layer above the supervisor server is a separate runner process.

Use the shared guide for positive mock-scene bring-up, negative
human-confirmation testing, and ROS2-backed robot execution:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md), sections `15.3` and `15.4`

The runner talks to the supervisor only through ROS2 services. In `--mock-scene`
mode it uses:

- a deterministic closed-set scene provider
- `BtXmlRobotExecutor` for robot-owned subtrees
- a manual/mock human confirmation path

By default the robot subtree executor uses an in-process `RunNamedCommand` backend.
The shared guide also covers the live ROS2 `RunNamedCommand` validation path with the
mock skill server.

If `/sandwich_bt/run_command` is unavailable, the runner exits with code `2`.

Exit codes:

- `0`: task reached `DONE`
- `1`: task aborted or step verification failed
- `2`: ROS2 supervisor service or `RunNamedCommand` service unavailable / no response
- `3`: invalid config, stale generated interfaces, or invalid supervisor output

## ROS2 Probe

For a minimal live check of the service boundary without running the full
collaborative loop, use the shared guide:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md), section `15.2`
