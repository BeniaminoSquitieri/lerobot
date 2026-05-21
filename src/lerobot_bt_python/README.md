# LeRobot BT Python

Python execution layer for the VLM-gated LeRobot BT stack.

For run commands and the stack overview, use:

- [`../lerobot_bt_README.md`](../lerobot_bt_README.md)

## Responsibility

This package owns:

- loading skill configs from `make_sandwich_executor.yaml`;
- lazy-loading learned policy runtimes on first use;
- running BC/ACT policy inference on the robot;
- opening a VLM check attempt after each successful skill or gate;
- accepting terminal/manual verifier results as live stops for running skills;
- exposing BT-facing ROS2 services plus verifier-facing ROS2 topics.

This package intentionally does not implement deterministic Panda recovery
motions. A VLM `FAILURE` is handled by the BT retrying the same BC skill.

## Active Command Kinds

- `skill`: run a configured learned primitive.
- `vlm_gate_pending`: open a pending VLM check attempt without robot motion.

## Request Lifecycle

1. `lerobot_bt_runner` calls `/lerobot_bt/run`.
2. `server.py` dispatches `kind="skill"` to `SkillCommandExecutor.execute_skill`.
3. The executor runs one policy rollout and returns `CommandResult`.
4. If the command succeeded normally, `server.py` creates a VLM check attempt
   with status `PENDING` and publishes a JSON request on `/lerobot_bt/vlm_request`.
5. If a `SUCCESS`, `FAILURE`, `WAIT_HUMAN`, or
   `MANUAL_INTERVENTION_REQUIRED` result arrives while the skill is running,
   the executor stops the rollout and `server.py` creates the VLM check attempt
   already set to that verifier status.
6. `WaitForVLMVerdict` polls `/lerobot_bt/vlm_state` and returns BT `RUNNING`
   while the attempt remains in a waiting state.
7. A manual tester or VLM publishes JSON on `/lerobot_bt/vlm_result`
   with `RUNNING`, `WAIT_HUMAN`, `MANUAL_INTERVENTION_REQUIRED`, `SUCCESS`, or
   `FAILURE`.
8. The BT advances on `SUCCESS` or retries the same skill on `FAILURE`.

## Files

- `config.py`: draccus config dataclasses for skills and server options.
- `executor.py`: learned skill executor.
- `server.py`: ROS2 service node for command execution and VLM check relay.
- `verification.py`: in-memory registry for VLM pending/success/failure verdicts.
- `make_sandwich_executor.yaml`: active sandwich skill profile.
- `set_breakfast_table_executor.yaml`: breakfast table setup skill profile template.
- `items_in_drawer_executor.yaml`: drawer insertion skill profile template.
- `make_coffee_executor.yaml`: coffee task skill profile template.
- `prepare_picnic_bag_executor.yaml`: picnic bag preparation skill profile template.

The scene-task profile templates follow the same structure as the sandwich
profile. Keep the `name` fields aligned with the BT XML. Each skill can expose
multiple `policy_variants`; set the top-level `policy_variant` as the default,
then override it per skill with `skill.policy_variant` when a task mixes
different policy families. The variant key must match a registered LeRobot
policy type such as `act`, `smolvla`, `diffusion`, `groot`, `multi_task_dit`,
`pi0`, `pi0_fast`, `pi05`, `sac`, `reward_classifier`, `sarm`, `tdmpc`,
`vqbet`, `wall_x`, or `xvla`. Replace only the selected variants'
`pretrained_path` values with real local checkpoint paths or Hugging Face model
ids. Because these templates use `metadata_source: robot`, their
`dataset_repo_id` values are labels for logging/metadata identity; the live
robot feature schema is used during rollout. The SmolVLA templates use
`n_action_steps: 50` and `chunk_size: 50`; adjust those if a checkpoint was
trained with a different horizon.

The server performs strict startup validation:

- every `expected_skill_names` entry must exist in `skills`
- every skill name must be unique
- every selected policy variant must have a real `pretrained_path`, not a
  `TODO_...` placeholder
- every `required_cameras` entry must exist in `robot.cameras`

## Manual VLM Result

Watch the verifier requests emitted by the server:

```bash
ros2 topic echo /lerobot_bt/vlm_request
```

Advance the BT manually, using the same topic a real VLM will use:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"scene ok\"}'}"
```

Publish `FAILURE` instead of `SUCCESS` to make the enclosing
`RetryUntilSuccessful` restart that BT stage. `attempt_id: 0` applies the
verdict to the latest pending attempt for that skill.

For a real `skill`, a terminal/manual result can also be published while the
robot is still moving. That live result stops the policy rollout first, then
the server opens the corresponding VLM check already resolved with the same
status. `RUNNING` and `PENDING` are ignored as live skill stops.

Publish waiting states to keep the BT blocked:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pour_ingredient\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"message\":\"human is pouring\"}'}"
```

The same topic can carry richer VLM reasons:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"object_missing\",\"required_human_action\":\"put toast back in reachable area\"}'}"
```

The legacy `/lerobot_bt/vlm_result_legacy` service still exists for
compatibility, but new manual tools and VLM implementations should use topics.

VLM check attempts have a configurable timeout. If the VLM/manual verifier
does not report `SUCCESS` before `vlm_timeout_s`, the Python registry
marks the attempt as `FAILURE`; the BT VLM check node then returns failure
and the XML retry wrapper reruns the same skill. Set `vlm_timeout_s: 0`
to disable this automatic timeout.

## Active Sandwich Tree

Use `make_sandwich.xml` for the active task with two real BC skills and manual
VLM verdicts. For VLM gates, wait for
`/lerobot_bt/vlm_request` before publishing. For real BC skills, either wait
for the request after the rollout ends or publish the terminal/manual verdict
while the skill is moving to stop it immediately.

Expected manual report order:

```text
initial_scene_ready SUCCESS -> starts place_first_toast
place_first_toast SUCCESS -> opens the human pouring gate
pour_ingredient WAIT_HUMAN/RUNNING -> BT keeps waiting
pour_ingredient SUCCESS -> opens the second-toast positioning gate
second_toast_ready SUCCESS -> starts place_second_toast
place_second_toast SUCCESS -> opens the final task-complete gate
make_sandwich.task_complete SUCCESS -> final task gate succeeds
```

Any `FAILURE` verdict for a requested stage makes the XML retry block rerun that
same gate or skill. The future real VLM should publish the same JSON reports on
the same topic, so the BT does not change when manual CLI publishing is replaced.

## Scene Task Profiles

For the additional scene-gated tasks, start the Python server with the matching
executor profile and start the C++ runner with the matching XML tree plus BT
profile, for example:

```bash
lerobot-bt-skill-server --config_path src/lerobot_bt_python/prepare_picnic_bag_executor.yaml
```

```bash
ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner --ros-args \
  --params-file src/lerobot_bt_runtime_cpp/config/prepare_picnic_bag_bt.yaml \
  -p tree_xml_path:="$(pwd)/src/lerobot_bt_runtime_cpp/trees/prepare_picnic_bag.xml"
```

After installing or sourcing the ROS2 workspace, the runner can also be started
with the task launch file:

```bash
ros2 launch lerobot_bt_runtime_cpp prepare_picnic_bag.launch.py
```

The same pairing applies to:

- `set_breakfast_table_executor.yaml` with `set_breakfast_table_bt.yaml` and `set_breakfast_table.xml`
- `items_in_drawer_executor.yaml` with `items_in_drawer_bt.yaml` and `items_in_drawer.xml`
- `make_coffee_executor.yaml` with `make_coffee_bt.yaml` and `make_coffee.xml`
- `prepare_picnic_bag_executor.yaml` with `prepare_picnic_bag_bt.yaml` and `prepare_picnic_bag.xml`
