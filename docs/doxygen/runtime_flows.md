# Runtime Flows {#runtime_flows}

## End-to-end robot step flow

1. `sandwich_bt_supervisor/collaborative_runner.py` requests next action.
2. Supervisor picks actor and step.
3. If actor is `robot`, runner executes a BT subtree.
4. BT leaf `RunNamedCommand` sends ROS2 service request.
5. Python server dispatches to executor.
6. Executor runs learned skill or scripted recovery.
7. Result maps back to BT `SUCCESS`/`FAILURE`.
8. Runner asks supervisor to verify resulting scene state.

## Human handoff flow

1. Runner receives actor `human` from supervisor.
2. Human interface prompts operator and waits for confirmation.
3. Runner asks supervisor to verify expected scene state.
4. Runner continues, aborts, or retries depending on supervisor output.

## Failure boundary design

- BT runtime handles local action retry/recovery.
- Python executor reports command-level failures.
- Supervisor owns global abort/replan and verification failure decisions.
- Scene/VLM integration remains read-only with respect to motion commands.
