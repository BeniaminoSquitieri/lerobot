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
- `trees/lunch_table_bussing.xml`: scene-gated lunch table cleanup task
- `trees/grocery_bagging.xml`: scene-gated grocery bagging task
- `trees/items_in_drawer.xml`: scene-gated drawer insertion task
- `trees/make_coffee.xml`: scene-gated coffee preparation task
- `config/*_bt.yaml`: task-level gate names, skill names, timeouts, and retry limits loaded into the BT blackboard
- `launch/*.launch.py`: one-command runner startup for each task profile
- `diagrams/*_bt.png`: rendered PNG diagrams of each BT
- `tools/render_bt_diagrams.py`: script that regenerates the PNG diagrams from XML and YAML

## Execution Model

`sandwich_bt_main.cpp` is intentionally small. Its job is to host a normal
BehaviorTree.CPP tick loop and register the custom service-backed leaf nodes.

At startup it:

1. creates one ROS2 node named `sandwich_bt_runner`
2. reads the runtime parameters `tree_xml_path`, `bt_command_service`,
   `vlm_state_service`, `tick_ms`, `enable_groot_publisher`,
   `groot_publisher_port`, and the `bt.*` task profile values
3. registers `OpenVLMGate`, `RunRobotSkill`, and the task-specific aliases as
   custom BT builders
4. registers `WaitForGateVerdict` and `WaitForSkillVerdict` as VLM-check-node
   builders
5. writes the `bt.*` task profile values to the BT blackboard
6. loads the XML tree from disk
7. optionally enables a Groot publisher if the installed BT.CPP version has a
   compatible publisher API
8. ticks the tree until the root stops returning `RUNNING`

The executable returns `0` on final BT `SUCCESS` and `1` on final BT `FAILURE`.
That makes the process exit code usable as a high-level integration signal.
On `Ctrl+C`, it halts the active BT, destroys the Groot/ZMQ publisher, and then
returns `130`. If the Groot port is already occupied, the runner logs a warning
and continues without monitor publishing instead of aborting.

The task XMLs use blackboard placeholders for skill names, gate names, retry
limits, and timeouts. Pass the matching `config/*_bt.yaml` profile together with
`tree_xml_path`. The Python execution config must still define each referenced
BC skill before the tree can execute on the robot.

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

The active tree uses blackboard placeholders such as
`{place_first_toast_skill}` instead of hard-coded task names. The default values
come from C++ parameters and can be overridden by passing a ROS2 params file,
for example:

```bash
ros2 launch sandwich_bt_runtime_cpp makesandwitch.launch.py
```

The launch files pass the matching `config/*_bt.yaml` profile and XML tree to
`sandwich_bt_runner`. For debugging, you can still run the executable directly
and override `tree_xml_path` by hand.

Use XML for control structure changes: order, retry boundaries, and which node
types appear. Use a `config/*_bt.yaml` profile for task-level values: gate
names, skill names, retry limits, and skill timeouts.

## Rendered BT Diagrams

The `diagrams/` directory contains PNG images for every task tree. Regenerate
them after changing XML or BT YAML profiles with:

```bash
uv run python src/sandwich_bt_runtime_cpp/tools/render_bt_diagrams.py
```

## When To Modify This Package

Change this package when you need to:

- add a new custom BT leaf type
- change how the BT runtime talks to ROS2
- alter tick frequency or runner parameters
- change Groot integration behavior
- change the XML-level control structure for retries or ordering

Do not change C++ just to point a leaf at a different checkpoint or skill name.
Those values belong in a BT parameter profile under `config/`. The actual robot
policy definitions still belong to `sandwich_bt_python`.
