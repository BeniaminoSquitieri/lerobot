# Sandwich BT Runtime C++

C++ BehaviorTree.CPP runtime for the sandwich BT stack.

For build/run instructions and the architecture overview, use the shared guide:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md)

Architecture diagram:

- [`sandwich_bt_architecture.svg`](./sandwich_bt_architecture.svg)

This README focuses on the C++ runtime behavior. It intentionally avoids
duplicating setup, build, and launch material from the shared guide.

## Responsibility

This package owns BT orchestration.

It owns:

- loading BT XML trees
- registering readable command-start leaves: `OpenVLMGate`, `RunRobotSkill`,
  and task-specific aliases
- registering readable VLM-wait leaves: `WaitForGateVerdict` and
  `WaitForSkillVerdict`
- ticking the tree until success or failure
- converting service replies into BT `RUNNING`, `SUCCESS`, or `FAILURE`
- publishing to Groot when supported by the installed BehaviorTree.CPP version

It does not own:

- policy loading
- robot connection
- VLM implementation

Those belong to `sandwich_bt_python`.

## Files

- `src/sandwich_bt_main.cpp`: runner executable
- `src/run_named_command_node.cpp`: service-backed BT leaf implementation
- `include/sandwich_bt_runtime_cpp/run_named_command_node.hpp`: BT leaf declaration
- `src/verify_skill_outcome_node.cpp`: BT leaf that polls VLM check state
- `include/sandwich_bt_runtime_cpp/verify_skill_outcome_node.hpp`: VLM check leaf declaration
- `trees/makesandwitch.xml`: active two-real-skill sandwich task with manual/VLM topic gates

## Execution Model

`sandwich_bt_main.cpp` is intentionally small. Its job is to host a normal
BehaviorTree.CPP tick loop and register the custom service-backed leaf nodes.

At startup it:

1. creates one ROS2 node named `sandwich_bt_runner`
2. reads the runtime parameters `tree_xml_path`, `bt_command_service`,
   `vlm_state_service`, `tick_ms`, `enable_groot_publisher`, and
   `groot_publisher_port`
3. registers `OpenVLMGate`, `RunRobotSkill`, and the task-specific aliases as
   custom BT builders
4. registers `WaitForGateVerdict` and `WaitForSkillVerdict` as VLM-check-node
   builders
5. loads the XML tree from disk
6. optionally enables a Groot publisher if the installed BT.CPP version has a
   compatible publisher API
7. ticks the tree until the root stops returning `RUNNING`

The executable returns `0` on final BT `SUCCESS` and `1` on final BT `FAILURE`.
That makes the process exit code usable as a high-level integration signal.
On `Ctrl+C`, it halts the active BT, destroys the Groot/ZMQ publisher, and then
returns `130`. If the Groot port is already occupied, the runner logs a warning
and continues without monitor publishing instead of aborting.

## Command-Start Leaf Lifecycle

`OpenVLMGate`, `RunRobotSkill`, and the task-specific aliases are thin BT
wrappers around the same ROS2 command service. They are implemented as
`BT::StatefulActionNode`, not synchronous actions, because the service reply
may arrive after multiple tree ticks.

Its behavior is:

1. `onStart()` validates the visible BT input port, waits for the configured
   ROS2 service, and sends an asynchronous request.
2. The node returns `RUNNING` immediately after sending the request.
3. `onRunning()` polls the future. While the service call is incomplete, the
   node keeps returning `RUNNING`.
4. Once the future completes, the node maps `response.success` to BT
   `SUCCESS` or `FAILURE`.
5. `onHalted()` clears the local waiting state, but it does not cancel work
   already executing on the Python server.

`PrepareInitialScene` and `PrepareSecondToast` use the same behavior as
`OpenVLMGate`. `PlaceFirstToast` and `PlaceSecondToast` use the same behavior
as `RunRobotSkill`.

## Verdict-Wait Leaf Lifecycle

This second custom leaf is also a `BT::StatefulActionNode`.

The XML trees normally use two readable wrappers of this same C++ polling
behavior:

- `WaitForGateVerdict`: used for scene/human gates such as initial scene ready
  or human pouring.
- `WaitForSkillVerdict`: used after a robot skill, where a VLM
  `FAILURE` means "retry this same skill from the beginning."

The wrappers exist so Groot shows the intent of each VLM check point. They do
not add a second communication path and they do not change the ROS2 contract.
The XML files also include `TreeNodesModel` entries for these custom nodes so
Groot can display/edit their ports when opening the tree file directly.

Its behavior is:

1. `onStart()` validates the `skill_name` input port and sends a
   `VLM state service` request.
2. While the Python side reports `PENDING`, `RUNNING`, `WAIT_HUMAN`, or
   `MANUAL_INTERVENTION_REQUIRED`, the leaf keeps polling and returns BT
   `RUNNING`.
3. If the Python side reports `SUCCESS`, the leaf returns BT `SUCCESS`.
4. If the Python side reports `FAILURE`, or no attempt exists for that skill,
   the leaf returns BT `FAILURE`.

This is the point where the post-skill VLM check gates the BT. The C++ node
polls Python-side state; the VLM/manual implementation itself is decoupled and
reports verdicts through `/sandwich_bt/vlm_result`.

## XML Contract Used In This Repository

The runtime is generic, but the trees in this repository follow a deliberate
shape:

- retry behavior lives in XML through `RetryUntilSuccessful`
- local ordering lives in XML through `Sequence`
- VLM/manual gates are opened through `OpenVLMGate` or task-specific aliases
  such as `PrepareInitialScene` and `PrepareSecondToast`
- robot skills are executed through `RunRobotSkill` or task-specific aliases
  such as `PlaceFirstToast` and `PlaceSecondToast`
- VLM/manual gate verdicts are awaited through `WaitForGateVerdict`
- robot skill verdicts are awaited through `WaitForSkillVerdict`
For example, the usual subtree shape is:

1. run one named BC skill
2. check the outcome of that skill through `WaitForSkillVerdict`
3. if the VLM reports `FAILURE`, let the named `RetryUntilSuccessful` trigger
   another attempt of the same skill

That keeps retry structure visible in the tree instead of hiding it inside the
Python executor.

## BT Ports And Naming

- `OpenVLMGate` expects `gate_name`.
- `PrepareInitialScene` and `PrepareSecondToast` expect `gate_name`.
- `RunRobotSkill` expects `skill_name`; `timeout_s` is optional.
- `PlaceFirstToast` and `PlaceSecondToast` expect `skill_name`; `timeout_s` is
  optional.
- `WaitForGateVerdict` expects `gate_name`.
- `WaitForSkillVerdict` expects `skill_name`.

The C++ runtime maps these readable ports to the Python command service. A
real skill name must still match an entry in the Python skill config.

## When To Modify This Package

Change this package when you need to:

- add a new custom BT leaf type
- change how the BT runtime talks to ROS2
- alter tick frequency or runner parameters
- change Groot integration behavior
- change the XML-level control structure for retries or ordering

Do not modify this package just to point a leaf at a different checkpoint or a
different skill checkpoint. Those changes belong to `sandwich_bt_python`.
