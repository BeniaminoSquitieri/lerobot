# Sandwich BT Supervisor

Closed-set collaborative supervisor for the sandwich task.

This package sits above the existing BT runtime. It does not replace the
BehaviorTree.CPP layer. It decides which subtask comes next, assigns that
subtask to either the robot or the human, and verifies the scene after each
handoff. In the hardware-free simulation, robot-owned steps are executed
through per-step BT XML subtrees instead of calling the skill executor
directly.

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
- `simulation.py`: mock collaborative demo built on top of the existing skill simulation
- `bt_executor.py`: subtree interpreter for the hardware-free BT contract tests
- `sandwich_bt_supervisor.yaml`: reference affordance table for the closed-set planner
- `../sandwich_bt_runtime_cpp/trees/*_subtree.xml`: per-step robot BTs used by the contract tests

## Simulation

```bash
uv run lerobot-bt-supervisor-sim
```

This executes:

1. robot subtree `place_first_toast_subtree.xml`
2. human `pour_ingredient`
3. robot subtree `place_second_toast_subtree.xml`

and then exits once the scene reaches `DONE`.
