# fakes

Smoke-test-only fakes. **Nothing here runs on the real robot.**

| File | Purpose |
|---|---|
| `fake_bt_executor_server.py` | Fake `RunNamedCommand`/VLM-state server and pure-Python scenario simulator for non-robot smoke tests. |

The real robot skill server is [`lerobot_bt_python.server`](../server.py). The
fake deliberately avoids robot, policy, camera, VLM, and transformer imports and
must never be used on robot day.

See [../../../docs/robot_runtime_code_map.md](../../../docs/robot_runtime_code_map.md)
for the full runtime-vs-test classification.
