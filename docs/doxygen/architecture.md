# Architecture {#architecture}

## Layered design

```text
VLM / Scene Provider
  -> closed-set SandwichSceneObservation
sandwich_bt_supervisor
  -> next step
  -> actor: robot | human | done | abort
  -> verification
collaborative_runner
  -> executes robot or human steps
sandwich_bt_runtime_cpp
  -> BehaviorTree.CPP XML
  -> retry/recovery
  -> RunNamedCommand leaf
sandwich_bt_python
  -> ACT/GR00T skill execution
  -> scripted recoveries
  -> mock skill server
Panda / Robotiq / Cameras
```

## Rule

The VLM must not command robot motion directly.
The VLM may only estimate closed-set scene state and provide confidence/failure reasons.

## Robot-owned step

1. Supervisor chooses robot step.
2. Collaborative runner executes robot subtree.
3. BT subtree calls `RunNamedCommand`.
4. `RunNamedCommand` calls `/sandwich_bt/run_command`.
5. Skill server executes mock or real policy.
6. BT returns `SUCCESS` or `FAILURE`.
7. Supervisor verifies scene.

## Human-owned step

1. Supervisor chooses human step.
2. Runner instructs human.
3. Human confirms or times out.
4. Scene is verified.
5. Supervisor either advances or aborts/replans.
