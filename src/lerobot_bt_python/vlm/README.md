# vlm

This package contains the VLM/operator verifier protocol helpers used by the BT
Python runtime. It owns semantic verdict state and topic payload parsing, but it
does not own RGB-D publishing or metric perception gates.

| File                  | Responsibility                                                 |
| --------------------- | -------------------------------------------------------------- |
| `verification.py`     | In-memory state machine for VLM/gate attempts and statuses.    |
| `protocol.py`         | JSON payload helpers for verifier request/result topics.       |
| `operator_console.py` | Human-readable terminal banners for VLM request/result events. |

Boundary: VLM code may interpret verifier statuses and semantic scene results.
It should not open cameras, publish RGB-D, query `/perception/query_pose`, or
evaluate spatial-prior distance checks.
