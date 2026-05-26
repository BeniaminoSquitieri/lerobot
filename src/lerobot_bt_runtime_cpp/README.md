# LeRobot BT Runtime C++

C++ BehaviorTree.CPP runtime for the LeRobot BT stack.

For build/run instructions and the architecture overview, use the shared guide:

- [`../lerobot_bt_README.md`](../lerobot_bt_README.md)

Architecture diagram:

- [`lerobot_bt_architecture.svg`](./lerobot_bt_architecture.svg)
- [`diagrams/bt_architecture_detailed.svg`](./diagrams/bt_architecture_detailed.svg)
- [`diagrams/bt_sequence_detailed.svg`](./diagrams/bt_sequence_detailed.svg)
- [`diagrams/bt_contracts_detailed.svg`](./diagrams/bt_contracts_detailed.svg)

This README focuses on the C++ runtime behavior.

## Responsibility

This package owns BT orchestration.

It owns:

- loading BT XML trees
- registering merged command+verify leaves: `AwaitScene` and `DoSkill`
- ticking the tree until success or failure
- converting service replies into BT `RUNNING`, `SUCCESS`, or `FAILURE`
- publishing to Groot when supported by the installed BehaviorTree.CPP version

It does not own:

- policy loading
- robot connection
- VLM implementation

Those belong to `lerobot_bt_python`.

## Files

- `src/lerobot_bt_main.cpp`: runner executable
- `src/run_named_command_node.cpp`: service-backed BT leaf implementation (base class used by merged nodes)
- `include/lerobot_bt_runtime_cpp/run_named_command_node.hpp`: BT leaf declarations
- `src/await_scene_node.cpp`: merged skill+verify and gate+verify BT leaves
- `include/lerobot_bt_runtime_cpp/await_scene_node.hpp`: merged leaf declarations
- `trees/make_sandwich.xml`: active two-real-skill sandwich task with VLM gates
- `trees/set_breakfast_table.xml`: scene-gated breakfast table setup task
- `trees/items_in_drawer.xml`: scene-gated drawer insertion task
- `trees/make_coffee.xml`: scene-gated coffee preparation task
- `trees/prepare_picnic_bag.xml`: scene-gated picnic bag preparation task
- `config/*_bt.yaml`: task-level gate names, skill names, timeouts, and retry limits loaded into the BT blackboard
- `launch/*.launch.py`: one-command runner startup for each task profile
- `diagrams/*_bt.png`: rendered PNG diagrams of each BT
- `tools/render_bt_diagrams.py`: script that regenerates the PNG diagrams from XML and YAML

## Execution Model

`lerobot_bt_main.cpp` is intentionally small. Its job is to host a normal
BehaviorTree.CPP tick loop and register the custom service-backed leaf nodes.

At startup it:

1. creates one ROS2 node named `lerobot_bt_runner`
2. reads the runtime parameters `tree_xml_path`, `bt_command_service`,
   `vlm_state_service`, `tick_ms`, `enable_groot_publisher`,
   `groot_publisher_port`, and the `bt.*` task profile values
3. registers `AwaitScene` and `DoSkill` as custom merged BT builders
   (each combines action execution with VLM verification)
4. writes the `bt.*` task profile values to the BT blackboard
5. loads the XML tree from disk
6. optionally enables a Groot publisher if the installed BT.CPP version has a
   compatible publisher API
7. ticks the tree until the root stops returning `RUNNING`

The executable returns `0` on final BT `SUCCESS` and `1` on final BT `FAILURE`.
That makes the process exit code usable as a high-level integration signal.
On `Ctrl+C`, it halts the active BT, destroys the Groot/ZMQ publisher, and then
returns `130`. If the Groot port is already occupied, the runner logs a warning
and continues without monitor publishing instead of aborting.

The task XMLs use blackboard placeholders for skill names, gate names, retry
limits, and timeouts. Pass the matching `config/*_bt.yaml` profile together with
`tree_xml_path`. The Python execution config must still define each referenced
BC skill before the tree can execute on the robot.

## Merged Leaf Lifecycle

`AwaitScene` and `DoSkill` are merged BT leaves that combine action execution
with VLM verification in a single node. Each replaces the old two-node pair
(`OpenVLMGate` + `WaitForVLMVerdict` or `RunRobotSkill` + `WaitForVLMVerdict`).

They are implemented as `BT::StatefulActionNode` with a two-phase state machine:

1. **Phase 1 Send command**: `onStart()` sends the ROS2 service request
   (skill or gate). The node returns `RUNNING`.
2. **Phase 2 Poll VLM**: After the command completes, the node automatically
   switches to polling the VLM state service. It returns `RUNNING` while
   waiting, `SUCCESS` on VLM approval, or `FAILURE` on VLM rejection.

`onHalted()` clears pending state but does not cancel in-flight server work.

## VLM Integration

The merged leaves (`AwaitScene` and `DoSkill`) handle VLM verdict polling
internally there is no separate verdict-wait leaf. The C++ node queries the
`/lerobot_bt/vlm_state` service (provided by the Python skill server) which
returns the latest VLM check status for the given skill/gate name.

External verifiers (manual terminal or the live Panda VLM) publish verdicts
to the `/lerobot_bt/vlm_result` topic. The Python server consumes these and
updates the check registry that the C++ node polls.

For live VLM verification, run `lerobot-bt-vlm-bridge`. It translates between
the BT protocol (`/lerobot_bt/vlm_request` → `/lerobot_bt/vlm_result`) and the
Panda VLM Verifier (`/panda/vlm/request` → `/panda/vlm/status`). The BT only
polls Python-side state; the VLM/manual implementation itself is decoupled and
reports verdicts through the bridge.

## XML Contract Used In This Repository

The runtime is generic, but the trees in this repository follow a deliberate
shape:

- retry behavior lives in XML through `RetryUntilSuccessful`
- local ordering lives in XML through `Sequence`
- VLM/manual gates are opened through `OpenVLMGate`
- robot skills are executed through `RunRobotSkill`
- VLM/manual gate and robot skill verdicts are awaited through
  `WaitForVLMVerdict`

For example, the usual subtree shape is:

1. run one named BC skill
2. check the outcome of that skill through `WaitForVLMVerdict`
3. if the VLM reports `FAILURE`, let the named `RetryUntilSuccessful` trigger
   another attempt of the same skill

That keeps retry structure visible in the tree instead of hiding it inside the
Python executor.

## BT Ports And Naming

- `OpenVLMGate` expects `gate_name`.
- `RunRobotSkill` expects `skill_name`; `timeout_s` is optional.
- `WaitForVLMVerdict` expects `check_name`.

The C++ runtime maps command leaves to the Python command service and
`WaitForVLMVerdict` to the Python VLM state service. A real skill name must
still match an entry in the Python skill config.

The active tree uses blackboard placeholders such as
`{place_first_toast_skill}` instead of hard-coded task names. The default values
come from C++ parameters and can be overridden by passing a ROS2 params file,
for example:

```bash
ros2 launch lerobot_bt_runtime_cpp make_sandwich.launch.py
```

The launch files pass the matching `config/*_bt.yaml` profile and XML tree to
`lerobot_bt_runner`. For debugging, you can still run the executable directly
and override `tree_xml_path` by hand.

Use XML for control structure changes: order, retry boundaries, and which node
types appear. Use a `config/*_bt.yaml` profile for task-level values: gate
names, skill names, retry limits, and skill timeouts.

## Rendered BT Diagrams

The `diagrams/` directory contains PNG images for every task tree. Regenerate
them after changing XML or BT YAML profiles with:

```bash
uv run python src/lerobot_bt_runtime_cpp/tools/render_bt_diagrams.py
```

The repository-level architecture image is generated separately because it
documents packages, services, topics, and verifier flow rather than one XML
tree:

```bash
uv run python src/lerobot_bt_runtime_cpp/tools/render_architecture_overview.py
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
policy definitions still belong to `lerobot_bt_python`.
