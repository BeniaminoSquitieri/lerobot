# LeRobot BT Stack

This stack follows one runtime model:

```text
BehaviorTree.CPP decides order, waiting, and retries.
Python executes one named BC skill or opens one VLM gate.
VLM/manual verifier reports waiting states, success, failure, or requested action.
```

There is no separate supervisor in the active runtime path. There are no
deterministic Panda recovery motions between attempts. If the VLM reports
`FAILURE`, the XML-level `RetryUntilSuccessful` node starts the same BC skill
again from the beginning.

## Architecture (multi-machine)

The BT stack and the VLM run on **two separate machines** communicating over
ROS 2:

```text
┌── IITICB001DW001 (robot machine) ──┐    ┌── iitbmp014srv002 (GPU server) ──┐
│                                     │    │                                  │
│  panda_camera_publisher.py          │─── │  panda_vlm_live.py               │
│  (RealSense → CompressedImage)      │ROS2│  (Qwen3-VL model, inference)     │
│                                     │    │                                  │
│  lerobot-bt-skill-server  (Python)  │─── │  listens on:                     │
│  lerobot_bt_runner        (C++ BT)  │ROS2│  /lerobot_bt/vlm_request         │
│                                     │    │  publishes on:                   │
│  Panda robot + Robotiq gripper      │    │  /lerobot_bt/vlm_result           │
│  RealSense cameras (USB)            │    │                                  │
└─────────────────────────────────────┘    └──────────────────────────────────┘
```

Both machines must be on the same ROS 2 domain (default: 0).

### ⚠️ CRITICAL: CycloneDDS Configuration

**Panda hardware requires CycloneDDS.** Without proper configuration, the two
machines **will not discover each other** and ROS2 topics/services won't be
visible across the network.

#### Step 1: Create `~/.ros/cyclonedds.xml` on BOTH machines

```bash
mkdir -p ~/.ros
cat > ~/.ros/cyclonedds.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS xmlns="https://cdds.io/config">
  <Domain>
    <General>
      <AllowMulticast>true</AllowMulticast>
    </General>
  </Domain>
</CycloneDDS>
EOF
```

#### Step 2: Export env vars on EVERY terminal (robot + GPU server)

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/.ros/cyclonedds.xml
```

**❌ Common mistake:** forgetting to set these on one terminal — cross-machine
discovery will silently fail.

#### Step 3: Launch Panda control with CycloneDDS

```bash
CYCLONEDDS_URI=file://$HOME/.ros/cyclonedds.xml panda_control_launch
```

#### Step 4: Verify cross-machine discovery

On the **robot machine**, after launching the server:
```bash
ros2 topic list | grep -E "lerobot_bt|panda"
```

On the **GPU server**, these same topics must be visible:
```bash
ros2 topic list | grep -E "lerobot_bt|panda"
```

If topics are missing on one machine, re-check Step 2 on ALL terminals.

#### Step 5: Verify communication

```bash
# Robot machine
ros2 topic pub /lerobot_bt/vlm_request std_msgs/msg/String '{"data":"{\"skill_name\":\"ping\"}"}' -1

# GPU server — should see the message
ros2 topic echo /lerobot_bt/vlm_request
```

### Network addresses (reference)

| Machine | Hostname | IP | Interface |
|---------|----------|----|-----------|
| Robot | IITICB001DW001 | 192.168.100.171 | eno1 |
| GPU server | iitbmp014srv002 | 192.168.100.180 | enp1s0f1 |

## Packages

| Package | Role |
| --- | --- |
| `lerobot_bt_runtime_cpp` | Loads/ticks BT XML and bridges BT leaves to ROS2 services. |
| `lerobot_bt_python` | Executes real BC skills and manages VLM check attempts. |
| `lerobot_bt_interfaces` | Generates the three ROS2 service contracts used by the stack. |

## Quick Preflight Checks

Before launching anything, run the preflight script to validate the
environment:

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/lerobot
python3 scripts/bt_preflight_check.py --task make_sandwich
```

This checks (in order):
1. ROS 2 environment (Jazzy sourced, `ros2` available)
2. Workspace build (`install/setup.bash`, ROS2 packages built)
3. Python environment (`lerobot`, `rclpy`, `torch`, `lerobot_bt_python` importable)
4. YAML consistency (skill names match between BT params and executor config)
5. Policy checkpoints (local HuggingFace cache)
6. Robot hardware (cameras, Panda ping) — only with `--real` flag

Exit code 0 = all mandatory checks passed.

## How To Swap Policy Models

You only need to edit **one file**: the executor YAML
(`src/lerobot_bt_python/<task>_executor.yaml`).

**These files NEVER need changes for policy swaps:**
- BT tree XML (`src/lerobot_bt_runtime_cpp/trees/<task>.xml`)
- BT params YAML (`src/lerobot_bt_runtime_cpp/config/<task>_bt.yaml`)
- Launch files

### Option A: Change the active variant

```yaml
skills:
  - name: place_first_toast
    policy_variant: smolvla    # ← change this (act, smolvla, diffusion, pi0, ...)
```

### Option B: Update a pretrained_path

```yaml
policy_variants:
  act:
    pretrained_path: "YourOrg/your-model-name"   # ← change this
```

### Option C: Add a new variant

```yaml
policy_variant: my_new_model
policy_variants:
  my_new_model:
    type: act
    device: cuda
    pretrained_path: "YourOrg/my-trained-checkpoint"
    n_action_steps: 16
    chunk_size: 16
```

## VLM Communication Test (simulated, no robot motion)

Use this to verify the BT ↔ VLM protocol **without running the full BT stack**
or moving the robot. Only the VLM node and camera publisher need to be active.

### Prerequisites

**On the robot machine** (`IITICB001DW001`):
```bash
conda activate lerobot_ben
cd ~/users/sben/panda_live_camera
python3 panda_camera_publisher.py
```

**On the GPU server** (`iitbmp014srv002`):
```bash
conda activate ros2_jazzy
source /opt/ros/jazzy/setup.bash
cd ~/panda_live_viewer
python3 panda_vlm_live.py
```

Wait until you see `"Ready. Listening on ..."`.

### Run the test

**On the robot machine**, in another terminal:
```bash
conda activate lerobot_ben
cd ~/users/sben/lerobot
source install/setup.bash
python3 scripts/simulate_vlm_test.py
```

### Expected output

```
==================================================
  TEST COMUNICAZIONE BT → VLM (simulato)
==================================================
  → INVIO richiesta: skill=place_first_toast, attempt=42, task='Pick the toast...'
  ← RISPOSTA: skill=place_first_toast, attempt=42, status=RUNNING
  ← RISPOSTA: skill=place_first_toast, attempt=42, status=SUCCESS
✓ TEST PASSATO
```

On the server VLM terminal you should see:
```
[INFO] [lerobot_bt_vlm_server]: Received VLM request for place_first_toast (attempt 42)
[INFO] [lerobot_bt_vlm_server]: RUNNING: VLM processing (skill=place_first_toast, attempt=42)
```

### What the test validates

| Check | Expected |
|-------|----------|
| `skill_name` preserved in response | `"place_first_toast"` |
| `attempt_id` preserved in response | `42` |
| `status` is valid VLM status | `RUNNING`, `SUCCESS`, `FAILURE`, etc. |
| Intermediate `RUNNING` published | Yes (good practice) |
| Terminal status (`SUCCESS`/`FAILURE`) | Published within timeout |
| `task` field reaches VLM prompt | Task description from executor YAML |

### Troubleshooting

If the test times out (60 s) with no response:

```bash
# On BOTH machines, verify topics are visible:
ros2 topic list | grep -E "lerobot_bt|panda"

# On the robot machine, verify the VLM topics have publishers/subscribers:
ros2 topic info /lerobot_bt/vlm_request
# Should show: Publisher count: 1, Subscription count: 1

# On the GPU server, test locally:
python3 -c "
import json, rclpy, time
from std_msgs.msg import String
rclpy.init()
n = rclpy.create_node('test')
p = n.create_publisher(String, '/lerobot_bt/vlm_request', 10)
m = String()
m.data = json.dumps({'event':'vlm_check_requested','skill_name':'test_skill','attempt_id':1,'status':'PENDING','message':'hello','task':'test task','allowed_statuses':['PENDING','RUNNING','SUCCESS','FAILURE'],'allowed_next_actions':['CONTINUE','RETRY_SKILL']})
for _ in range(3):
    p.publish(m)
    time.sleep(0.5)
    rclpy.spin_once(n, timeout_sec=0.1)
print('PUBLISHED')
time.sleep(2)
n.destroy_node()
rclpy.shutdown()
"
# The VLM terminal should show: "Received VLM request for test_skill"
```

### Automated test with validation

For a more thorough protocol check:
```bash
python3 scripts/test_vlm_protocol.py --test skill
python3 scripts/test_vlm_protocol.py --test gate
```

This publishes a request, collects all responses, and automatically validates:
- `skill_name` / `attempt_id` match
- Status vocabulary correctness
- Intermediate `RUNNING` presence
- Terminal status arrival

## VLM Server Requirements

For implementing a custom VLM verifier node, see the detailed specification:
[`src/lerobot_bt_python/VLM_SERVER_REQUIREMENTS.md`](lerobot_bt_python/VLM_SERVER_REQUIREMENTS.md)

Key protocol points:
- Subscribe to `/lerobot_bt/vlm_request` (`std_msgs/String`, JSON payload)
- Publish on `/lerobot_bt/vlm_result` (`std_msgs/String`, JSON payload)
- Preserve `skill_name` and `attempt_id` from request to response
- Use exact status vocabulary: `PENDING`, `RUNNING`, `WAIT_HUMAN`,
  `MANUAL_INTERVENTION_REQUIRED`, `SUCCESS`, `FAILURE`
- The `task` field in requests contains the human-readable task description
  (e.g. `"Pick the toast upon the table."`). Include it in the VLM prompt.
- Publish `RUNNING` immediately after receiving a request while inference is
  in progress

## Active Flow

Default tree:

```text
src/lerobot_bt_runtime_cpp/trees/make_sandwich.xml
```

Runtime sequence:

```text
initial_scene_ready
  -> VLM/manual gate, no robot motion

place_first_toast
  -> BC skill
  -> VLM/manual result

pour_ingredient
  -> human step represented as VLM/manual gate

second_toast_ready
  -> human step represented as VLM/manual gate

place_second_toast
  -> BC skill
  -> VLM/manual result

make_sandwich.task_complete
  -> final VLM/manual task gate
```

The BT never advances past a gate while the VLM check is a waiting status:
`PENDING`, `RUNNING`, `WAIT_HUMAN`, or `MANUAL_INTERVENTION_REQUIRED`.

## ROS2 Services

The Python server exposes:

```text
/lerobot_bt/run
/lerobot_bt/vlm_state
/lerobot_bt/vlm_result_legacy
```

The readable BT command leaves map to these Python command kinds:

- `RunRobotSkill`: runs one configured BC skill on the robot.
- `OpenVLMGate`: opens a VLM/manual check attempt without robot motion.

`/lerobot_bt/vlm_result` is the VLM/manual input boundary. It may report:

- `PENDING`
- `RUNNING`
- `WAIT_HUMAN`
- `MANUAL_INTERVENTION_REQUIRED`
- `SUCCESS`
- `FAILURE`

It may also report `next_action` instead of `status`. Supported values are
`CONTINUE`, `RETRY_SKILL`, `WAIT_HUMAN`, and
`REQUEST_MANUAL_INTERVENTION`.

For a real running `skill`, `SUCCESS`, `FAILURE`, `WAIT_HUMAN`, or
`MANUAL_INTERVENTION_REQUIRED` also acts as a live stop: the Python executor
stops sending policy actions, then opens the skill's VLM check already set to
that status. `PENDING` and `RUNNING` are only post-skill waiting states.

## Failure And Retry

For a robot skill, the BT subtree shape is:

```text
RetryUntilSuccessful(name="retry_<skill>_on_vlm_retry_skill")
  Sequence(name="<skill>_vlm_replanning_loop")
    RunRobotSkill(skill_name="<skill>")
    WaitForVLMVerdict(check_name="<skill>")
```

For a VLM/human gate with no robot motion, the shape is:

```text
RetryUntilSuccessful(name="retry_<gate>_until_vlm_success")
  Sequence(name="<gate>_wait_or_manual_intervention_gate")
    OpenVLMGate(gate_name="<gate>")
    WaitForVLMVerdict(check_name="<gate>")
```

If the skill call fails, the sequence fails and the same skill is retried.

If the VLM reports `FAILURE`, `WaitForVLMVerdict` returns BT `FAILURE`; the
same `RetryUntilSuccessful` wrapper restarts the same BC skill from the
beginning.

If the VLM reports `RUNNING`, `WAIT_HUMAN`, or
`MANUAL_INTERVENTION_REQUIRED`, `WaitForVLMVerdict` keeps returning BT
`RUNNING`; the tree waits for a later `SUCCESS` or `FAILURE`.

No gripper open/close, Panda reset, or deterministic Cartesian delta is run by
the retry mechanism.

`WaitForVLMVerdict` is the single C++ VLM check node. It waits on the latest
attempt named by `check_name`, whether that attempt was opened by a human/VLM
gate or by a completed robot skill.

## Real Robot Complete Test

Full setup with the real Panda/Robotiq/camera stack and the live VLM verifier.
All terminals on the **robot machine** (`IITICB001DW001`) unless marked with
☁️ (GPU server).

### ⚠️ Before first launch — rebuild!

Every time you change an interface (`.srv`), a launch file, or a BT tree XML,
you must rebuild the ROS2 workspace. If you skip this, launch files and service
bindings will be missing at runtime:

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/lerobot
colcon build --base-paths src --packages-up-to lerobot_bt_runtime_cpp
source install/setup.bash
```

### Common setup (every terminal on the robot machine)

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/lerobot
source install/setup.bash
```

### Terminal 1 ☁️ (GPU server): VLM verifier

```bash
conda activate ros2_jazzy
source /opt/ros/jazzy/setup.bash
cd ~/panda_live_viewer
python3 panda_vlm_live.py
```

Wait for `"Ready. Listening on ..."`.

### Terminal 2 (robot machine): camera publisher

**Not needed when `camera_publish_map` is configured in the executor YAML.**
The BT skill server now publishes camera frames directly on ROS topics for
the VLM (see `camera_publish_map` in the executor YAML). If you need the
standalone publisher for debugging without the BT stack, run:

```bash
conda activate lerobot_ben
cd ~/users/sben/panda_live_camera
python3 panda_camera_publisher.py
```

Publishes compressed images to `/panda/camera/front/image_compressed` and
`/panda/camera/wrist/image_compressed`. The VLM on the GPU server subscribes
to these topics over ROS 2.

### Terminal 3 (robot machine): skill server

Start the Python execution layer. This connects the real robot and executes the
learned skills configured in `make_sandwich_executor.yaml`.

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/lerobot
source install/setup.bash
python3 -m lerobot_bt_python.server \
  --config_path src/lerobot_bt_python/make_sandwich_executor.yaml
```

Wait for `"ROS2 skill command service node is ready."`

### Terminal 4 (robot machine): BehaviorTree runner

Start the C++ BT runner **after** the skill server is ready.

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/lerobot
source install/setup.bash
ros2 launch lerobot_bt_runtime_cpp make_sandwich.launch.py
```

### Terminal 5 (optional, robot machine): manual VLM override

You can manually publish verdicts to override or supplement the live VLM.
`attempt_id: 0` means "apply this verdict to the latest pending attempt".

For the two real BC skills, you do not have to wait for `/lerobot_bt/vlm_request`
if the robot has already achieved the visible goal. Publishing the `SUCCESS` or
`FAILURE` result while the policy is still moving stops that skill and lets the
BT advance to the VLM decision node immediately.

Initial scene ready:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"initial_scene_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"initial scene ready\"}'}"
```

First toast placed correctly:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"first toast ok\"}'}"
```

Human is still pouring. This keeps the BT blocked on the human/VLM gate:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pour_ingredient\",\"attempt_id\":0,\"status\":\"WAIT_HUMAN\",\"message\":\"human is pouring\"}'}"
```

Human pouring completed:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"pour_ingredient\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"ingredient poured\"}'}"
```

Second toast positioned correctly by the human:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"second_toast_ready\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"second toast ready\"}'}"
```

Second toast placed correctly:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_second_toast\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"second toast ok\"}'}"
```

Task complete:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"make_sandwich.task_complete\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"make sandwich task complete\"}'}"
```

Force a retry for the current stage:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"toast misplaced\",\"message\":\"retry skill\"}'}"
```

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_second_toast\",\"attempt_id\":0,\"status\":\"FAILURE\",\"failure_reason\":\"toast misplaced\",\"message\":\"retry skill\"}'}"
```

Request manual intervention without advancing the BT:

```bash
ros2 topic pub --once /lerobot_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"next_action\":\"REQUEST_MANUAL_INTERVENTION\",\"failure_reason\":\"object_missing\",\"required_human_action\":\"put toast back in reachable area\"}'}"
```

Equivalent `next_action` values are accepted too:

```text
CONTINUE -> SUCCESS
RETRY_SKILL -> FAILURE
WAIT_HUMAN -> WAIT_HUMAN
REQUEST_MANUAL_INTERVENTION -> MANUAL_INTERVENTION_REQUIRED
```

The real-robot config currently has `vlm_timeout_s: 0.0`, so pending VLM
attempts do not automatically become `FAILURE` while you are doing slower
manual tests. Set a positive value in the executor YAML when you want automatic
timeout-to-retry behavior.

### Useful inspection commands

List the stack topics and services:

```bash
ros2 topic list | grep lerobot_bt
ros2 service list | grep lerobot_bt
```

Inspect the latest VLM state for one stage:

```bash
ros2 service call /lerobot_bt/vlm_state lerobot_bt_interfaces/srv/GetSkillVerification \
  "{skill_name: 'place_first_toast'}"
```

Legacy service path for a VLM/manual verdict. New tools should prefer the
`/lerobot_bt/vlm_result` topic, but this remains available:

```bash
ros2 service call /lerobot_bt/vlm_result_legacy lerobot_bt_interfaces/srv/ReportSkillVerification \
  "{skill_name: 'place_first_toast', attempt_id: 0, status: 'SUCCESS', message: 'first toast ok'}"
```

## Additional BT command guides

The same command format is documented for the additional scene-gated BTs:

- [VLM, BT, and BC conventions](lerobot_bt_vlm_conventions_README.md)
- [Set Breakfast Table](lerobot_bt_set_breakfast_table_README.md)
- [Items In Drawer](lerobot_bt_items_in_drawer_README.md)
- [Make Coffee](lerobot_bt_make_coffee_README.md)
- [Prepare Picnic Bag](lerobot_bt_prepare_picnic_bag_README.md)

Rendered PNG diagrams:

- [Make Sandwich BT](lerobot_bt_runtime_cpp/diagrams/make_sandwich_bt.png)
- [Set Breakfast Table BT](lerobot_bt_runtime_cpp/diagrams/set_breakfast_table_bt.png)
- [Items In Drawer BT](lerobot_bt_runtime_cpp/diagrams/items_in_drawer_bt.png)
- [Make Coffee BT](lerobot_bt_runtime_cpp/diagrams/make_coffee_bt.png)
- [Prepare Picnic Bag BT](lerobot_bt_runtime_cpp/diagrams/prepare_picnic_bag_bt.png)
