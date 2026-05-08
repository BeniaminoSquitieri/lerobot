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
- registering the `RunNamedCommand` BT leaf
- registering the `VerifySkillOutcome` BT leaf and the Groot-readable aliases
  `WaitForVLMDecision` and `VLMReplanningDecision`
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
- `trees/sandwich_tree.xml`: full sandwich task tree
- `trees/sandwich_tree_first_real_rest_simulated.xml`: bring-up tree that runs `place_first_toast` as real and simulates the remaining primitives
- `trees/sandwich_tree_two_real_skills_manual_vlm.xml`: current two-real-skill task with manual/VLM topic gates

## Execution Model

`sandwich_bt_main.cpp` is intentionally small. Its job is to host a normal
BehaviorTree.CPP tick loop and register the custom service-backed leaf nodes.

At startup it:

1. creates one ROS2 node named `sandwich_bt_runner`
2. reads the runtime parameters `tree_xml_path`, `bt_command_service`,
   `vlm_state_service`, `tick_ms`, and `enable_groot_publisher`
3. registers `RunNamedCommand` as a custom BT builder
4. registers `VerifySkillOutcome`, `WaitForVLMDecision`, and
   `VLMReplanningDecision` as VLM-check-node builders
5. loads the XML tree from disk
6. optionally enables a Groot publisher if the installed BT.CPP version has a
   compatible publisher API
7. ticks the tree until the root stops returning `RUNNING`

The executable returns `0` on final BT `SUCCESS` and `1` on final BT `FAILURE`.
That makes the process exit code usable as a high-level integration signal.

## `RunNamedCommand` Leaf Lifecycle

The custom leaf is implemented as a `BT::StatefulActionNode`, not a synchronous
action, because the ROS2 service reply may arrive after multiple tree ticks.

Its behavior is:

1. `onStart()` validates the BT input ports `kind` and `command_name`, reads the
   optional `timeout_s`, waits for the configured ROS2 service, and sends an
   asynchronous request.
2. The node returns `RUNNING` immediately after sending the request.
3. `onRunning()` polls the future. While the service call is incomplete, the
   node keeps returning `RUNNING`.
4. Once the future completes, the node maps `response.success` to BT
   `SUCCESS` or `FAILURE`.
5. `onHalted()` clears the local waiting state, but it does not cancel work
   already executing on the Python server.

This means the leaf is only a transport bridge. All semantics of "what a skill
does" remain on the Python side.

## `VerifySkillOutcome` Leaf Lifecycle

This second custom leaf is also a `BT::StatefulActionNode`.

The XML trees normally use two semantic aliases of this same C++ class:

- `WaitForVLMDecision`: used for scene/human gates such as initial scene ready
  or human pouring.
- `VLMReplanningDecision`: used after a robot/simulated skill, where a VLM
  `FAILURE` means "retry this same skill from the beginning."

The aliases exist so Groot shows the intent of each VLM check point. They do
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
- robot-side effects are always requested through `RunNamedCommand`
- VLM/manual waiting gates are shown as `WaitForVLMDecision`
- post-skill retry decisions are shown as `VLMReplanningDecision`
For example, the usual subtree shape is:

1. run one named BC skill
2. check the outcome of that skill through `VLMReplanningDecision`
3. if the VLM reports `FAILURE`, let the named `RetryUntilSuccessful` trigger
   another attempt of the same skill

That keeps retry structure visible in the tree instead of hiding it inside the
Python executor.

## BT Ports And Naming

- The leaf expects the port name `command_name`, not `name`.
- `kind` is forwarded as an opaque string. The Python server currently handles
   `skill`, `no_motion_skill`, and `vlm_gate_pending`.
- `timeout_s` is optional and overrides the Python-side default for that one
  leaf execution.
- `VerifySkillOutcome`, `WaitForVLMDecision`, and `VLMReplanningDecision` expect
  the port `skill_name`.

The C++ runtime does not interpret the command name. It only forwards the
string. The matching config entry must exist on the Python side.

## When To Modify This Package

Change this package when you need to:

- add a new custom BT leaf type
- change how the BT runtime talks to ROS2
- alter tick frequency or runner parameters
- change Groot integration behavior
- change the XML-level control structure for retries or ordering

Do not modify this package just to point a leaf at a different checkpoint or a
different skill checkpoint. Those changes belong to `sandwich_bt_python`.
