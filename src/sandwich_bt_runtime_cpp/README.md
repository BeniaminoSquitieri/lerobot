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
- registering the `VerifySkillOutcome` BT leaf
- ticking the tree until success or failure
- converting service replies into BT `SUCCESS` or `FAILURE`
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
- `src/verify_skill_outcome_node.cpp`: BT leaf that polls scene verification state
- `include/sandwich_bt_runtime_cpp/verify_skill_outcome_node.hpp`: verification leaf declaration
- `trees/sandwich_tree.xml`: full sandwich task tree
- `trees/sandwich_tree_first_primitive_only.xml`: bring-up tree for only `place_first_toast`
- `trees/sandwich_tree_first_real_rest_simulated.xml`: bring-up tree that runs `place_first_toast` as real and simulates the remaining primitives
- `trees/sandwich_tree_two_real_skills_manual_vlm.xml`: current two-real-skill task with manual/VLM topic gates
- `trees/place_first_toast_subtree.xml`: retry subtree for the first toast step
- `trees/place_second_toast_subtree.xml`: retry subtree for the second toast step

## Execution Model

`sandwich_bt_main.cpp` is intentionally small. Its job is to host a normal
BehaviorTree.CPP tick loop and register the custom service-backed leaf nodes.

At startup it:

1. creates one ROS2 node named `sandwich_bt_runner`
2. reads the runtime parameters `tree_xml_path`, `service_name`, `tick_ms`,
   and `enable_groot_publisher`
3. registers `RunNamedCommand` as a custom BT builder
4. loads the XML tree from disk
5. optionally enables a Groot publisher if the installed BT.CPP version has a
   compatible publisher API
6. ticks the tree until the root stops returning `RUNNING`

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

Its behavior is:

1. `onStart()` validates the `skill_name` input port and sends a
   `GetSkillVerification` request.
2. While the Python side still reports `PENDING`, the leaf keeps polling and
   returns `RUNNING`.
3. If the Python side reports `SUCCESS`, the leaf returns BT `SUCCESS`.
4. If the Python side reports `FAILURE`, or no attempt exists for that skill,
   the leaf returns BT `FAILURE`.

This is the point where post-hoc scene verification gates the BT. The C++ node
polls Python-side state; the VLM/manual implementation itself is decoupled and
reports verdicts through `/sandwich_bt/verification_report`.

## XML Contract Used In This Repository

The runtime is generic, but the trees in this repository follow a deliberate
shape:

- retry behavior lives in XML through `RetryUntilSuccessful`
- local ordering lives in XML through `Sequence`
- robot-side effects are always requested through `RunNamedCommand`
For example, the usual subtree shape is:

1. run one named BC skill
2. verify the outcome of that skill through `VerifySkillOutcome`
3. if the VLM reports `FAILURE`, let `RetryUntilSuccessful` trigger another attempt

That keeps retry structure visible in the tree instead of hiding it inside the
Python executor.

## BT Ports And Naming

- The leaf expects the port name `command_name`, not `name`.
- `kind` is forwarded as an opaque string. The Python server currently handles
  `skill`, `simulated_skill`, and `simulated_skill_pending`.
- `timeout_s` is optional and overrides the Python-side default for that one
  leaf execution.
- `VerifySkillOutcome` expects the port `skill_name`.

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
