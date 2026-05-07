# Sandwich BT Stack

This stack follows one runtime model:

```text
BehaviorTree.CPP decides order and retries.
Python executes one named BC skill or opens one VLM gate.
VLM/manual verifier reports SUCCESS or FAILURE.
```

There is no separate supervisor in the active runtime path. There are no
deterministic Panda recovery motions between attempts. If the VLM reports
`FAILURE`, the XML-level `RetryUntilSuccessful` node starts the same BC skill
again from the beginning.

## Packages

| Package | Role |
| --- | --- |
| `sandwich_bt_runtime_cpp` | Loads/ticks BT XML and bridges BT leaves to ROS2 services. |
| `sandwich_bt_python` | Executes real BC skills, manages verification attempts, and provides the mock simulator entrypoint. |
| `sandwich_bt_interfaces` | Generates the three ROS2 service contracts used by the stack. |

## Active Flow

Default tree:

```text
src/sandwich_bt_runtime_cpp/trees/sandwich_tree.xml
```

Runtime sequence:

```text
initial_scene_ready
  -> VLM/manual gate, no robot motion

place_first_toast
  -> BC skill
  -> VLM/manual verification

pour_ingredient
  -> human step represented as VLM/manual gate

place_second_toast
  -> BC skill
  -> VLM/manual verification
```

The BT never advances past a gate while verification is `PENDING`.

## ROS2 Services

The Python server exposes:

```text
/sandwich_bt/run_command
/sandwich_bt/get_skill_verification
/sandwich_bt/report_skill_verification
```

`RunNamedCommand` accepts these active `kind` values:

- `skill`: run one configured BC skill on the robot.
- `simulated_skill`: simulate a skill and auto-mark verification as `SUCCESS`.
- `simulated_skill_pending`: open a verification attempt without robot motion.

`ReportSkillVerification` is the VLM/manual input boundary. It should report
only:

- `SUCCESS`
- `FAILURE`

The VLM must not report `RUNNING` or `PENDING`. `PENDING` is created by the
Python server; BT `RUNNING` is returned internally by `VerifySkillOutcome` while
it polls the pending attempt.

## Failure And Retry

For a robot skill, the BT subtree shape is:

```text
RetryUntilSuccessful
  Sequence
    RunNamedCommand(kind="skill", command_name="<skill>")
    VerifySkillOutcome(skill_name="<skill>")
```

If the skill call fails, the sequence fails and the same skill is retried.

If the VLM reports `FAILURE`, `VerifySkillOutcome` returns BT `FAILURE`; the
same `RetryUntilSuccessful` wrapper restarts the same BC skill from the
beginning.

No gripper open/close, Panda reset, or deterministic Cartesian delta is run by
the retry mechanism.

## Run Commands

Every ROS2 terminal:

```bash
conda activate lerobot
cd ~/lerobot
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

Real skill server:

```bash
lerobot-bt-skill-server \
  --config_path "$(pwd)/src/sandwich_bt_python/sandwich_bt_executor.yaml"
```

BT runner:

```bash
ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner
```

Mock server:

```bash
lerobot-bt-skill-sim --ros2-service
```

Manual VLM verdict:

```bash
ros2 service call /sandwich_bt/report_skill_verification \
  sandwich_bt_interfaces/srv/ReportSkillVerification \
  "{skill_name: place_first_toast, attempt_id: 0, status: SUCCESS, message: 'first toast ok', confidence: 0.95}"
```

`attempt_id: 0` means "apply to the latest pending attempt for that
`skill_name`".
