# BT/VLM Debugging Guide

Scope: a log-and-error-message reference for the active BT/VLM/LeRobot flow. This guide does not introduce tooling or recipes; it documents what the runtime already emits and where, so an operator reading a log can trace the event back to source.

For the source-derived contract baseline (topic names, payload fields, file:line references for the request/result handlers) see [bt_vlm_contract.md](bt_vlm_contract.md).

## Flow at a glance

1. The C++ BT calls the `RunNamedCommand` service handled by `SkillCommandServer._handle_request` in [src/lerobot_bt_python/server.py](../../src/lerobot_bt_python/server.py).
2. For a skill, the server opens a fresh VLM check attempt (`VlmCheckRegistry.begin_attempt`) and publishes a JSON request on the configured VLM request topic via `SkillCommandServer._publish_vlm_request`.
3. An external verifier publishes a JSON result on the configured VLM result topic. `SkillCommandServer._handle_vlm_result_topic` parses it and applies it through `VlmCheckRegistry.report`.
4. The BT polls `WaitForVLMVerdict`, which reads the latest snapshot from the same registry.

## Structured log fields

After Pass 2, both `_publish_vlm_request` and `_handle_vlm_result_topic` emit logs with key-value fields that are stable enough to grep for. The full wording is not pinned, but the following keys are expected to appear when the corresponding value is in scope:

| key       | meaning                                                                 |
| --------- | ----------------------------------------------------------------------- |
| `event=`  | event tag, e.g. `vlm_request_published`, `vlm_result_received`          |
| `skill=`  | BT skill name (only present when parsed successfully)                   |
| `attempt=`| monotonic per-skill attempt id (only present when parsed successfully)  |
| `status=` | published/received status token, or a parse-failure tag (`invalid_json`, `invalid_payload`, `rejected`) |
| `topic=`  | configured ROS2 topic name (`cfg.vlm_request_topic` / `cfg.vlm_result_topic`) |

Example grep recipes (using the configured topic name as a discriminator):

```bash
# All VLM publications.
grep "event=vlm_request_published" <log>

# All VLM receptions that failed to parse.
grep -E "event=vlm_result_received status=(invalid_json|invalid_payload|rejected)" <log>
```

The contract for these fields is pinned by static AST tests in [tests/lerobot_bt/test_log_format_contract.py](../../tests/lerobot_bt/test_log_format_contract.py). Adding or removing one of the key tokens will fail that test.

## Why `self.get_logger()` inside `SkillCommandServer`

`SkillCommandServer` is a `rclpy.node.Node`. All log calls inside the node and its ROS callbacks go through `self.get_logger()` so the messages reach the ROS2 log sink, are tagged with the node name, and respect ROS2 log level configuration. The module also imports stdlib `logging`, but that is used only by helpers outside the node (notably the `run()` startup function). A future contributor should not switch `self.get_logger()` calls to `logging.getLogger(__name__)` inside the node; doing so would silently change where the messages are routed.

## `bt_vlm_bridge.py` is legacy compatibility

[src/lerobot_bt_python/bt_vlm_bridge.py](../../src/lerobot_bt_python/bt_vlm_bridge.py) is a translation node kept for the Panda live-VLM compatibility path. It is not on the active BT/VLM flow. On first invocation it logs a one-shot deprecation message via `logging.getLogger(__name__).warning(...)`. If you see a `bt_vlm_bridge is a legacy compatibility path` line in the logs and you are not running the Panda bridge intentionally, suspect a misconfigured launch.

The legacy `legacy_vlm_result_service` (`/lerobot_bt/vlm_result_legacy` by default) is similarly preserved. Its handler in `SkillCommandServer._handle_legacy_vlm_result` also emits a one-shot deprecation warning on first call.

## Common failure patterns

### Mismatched `attempt_id`

`VlmCheckRegistry.report` rejects a result whose `attempt_id` does not match the latest open attempt for that skill. The warning surface is the rejection message returned in `VlmCheckUpdate.message` (logged at warning level by both the topic and service handlers):

> `VLM result for skill '<name>' targeted attempt <N>, but the latest attempt is <M>.`

Typical causes: the verifier replied late after a new attempt was opened, or the verifier hardcoded an `attempt_id` instead of echoing the value from the request payload.

### Unknown skill name

`VlmCheckRegistry._validate_skill_name` raises `ValueError("Unknown skill '<name>'.")` when the registry is configured with a `known_skill_names` set and the report targets a name outside it. The topic handler converts this into:

> `event=vlm_result_received status=rejected topic=... error=Unknown skill '<name>'.`

If you see this, the verifier and the server disagree on the skill vocabulary. Check the YAML profile loaded by `SkillCommandServer` and the request payload the verifier replied to.

### Unsupported status token

`VlmCheckRegistry.report` raises `ValueError` when the `status` field is outside the allowed set. The Pass 2 error message includes both the offending token and the expected vocabulary:

> `Unsupported VLM status '<bad>'. Expected one of ['FAILURE', 'MANUAL_INTERVENTION_REQUIRED', 'PENDING', 'RUNNING', 'SUCCESS', 'WAIT_HUMAN'].`

The expected substrings are pinned by [tests/lerobot_bt/test_error_messages.py](../../tests/lerobot_bt/test_error_messages.py).

### Timeout while `PENDING`

`VlmCheckSnapshot.timeout_s` is initialized from `cfg.vlm_timeout_s` (default `30.0`). `VlmCheckRegistry._expire_if_needed_locked` converts a waiting snapshot whose age exceeds the timeout into a `FAILURE` snapshot with the message:

> `VLM check attempt <N> for skill '<name>' timed out after <T>s without SUCCESS.`

If you see waiting snapshots flipping to `FAILURE` without any topic activity, the most likely cause is a verifier that is not publishing, or a topic-name mismatch between the publisher and `cfg.vlm_result_topic`. The latter is visible in the `topic=` field of any earlier `vlm_request_published` log line.

## Where logs come from (source pointers)

- VLM request publication: `SkillCommandServer._publish_vlm_request` in [src/lerobot_bt_python/server.py](../../src/lerobot_bt_python/server.py).
- VLM result reception: `SkillCommandServer._handle_vlm_result_topic` in [src/lerobot_bt_python/server.py](../../src/lerobot_bt_python/server.py).
- Legacy service path: `SkillCommandServer._handle_legacy_vlm_result` in [src/lerobot_bt_python/server.py](../../src/lerobot_bt_python/server.py).
- Status vocabulary and registry transitions: [src/lerobot_bt_python/verification.py](../../src/lerobot_bt_python/verification.py).
- Legacy Panda bridge: [src/lerobot_bt_python/bt_vlm_bridge.py](../../src/lerobot_bt_python/bt_vlm_bridge.py).
