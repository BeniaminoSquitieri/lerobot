# BT/VLM Runtime Contract (Pass 1 Baseline)

This document freezes the active BT/VLM contract from current source.
It is descriptive only and must not be treated as a design proposal.

## Transport Endpoints

- Active request topic: `/lerobot_bt/vlm_request`
  - Default in server config: `src/lerobot_bt_python/config.py:323`
  - Bridge constant: `src/lerobot_bt_python/bt_vlm_bridge.py:30`
- Active result topic: `/lerobot_bt/vlm_result`
  - Default in server config: `src/lerobot_bt_python/config.py:326`
  - Bridge constant: `src/lerobot_bt_python/bt_vlm_bridge.py:32`
- Legacy service endpoint: `/lerobot_bt/vlm_result_legacy`
  - Default in server config: `src/lerobot_bt_python/config.py:320`
  - Service registration in server node: `src/lerobot_bt_python/server.py:605`, `src/lerobot_bt_python/server.py:609`

## Expected JSON Request Fields (server -> /lerobot_bt/vlm_request)

Published by `SkillCommandServer._publish_vlm_request`:
`src/lerobot_bt_python/server.py:1062`

Fields written into the JSON payload:
- `event` with value `vlm_check_requested` (`src/lerobot_bt_python/server.py:1082`)
- `skill_name` (`src/lerobot_bt_python/server.py:1084`)
- `attempt_id` as `int(...)` (`src/lerobot_bt_python/server.py:1086`)
- `status` initialized as `VLM_PENDING` (`src/lerobot_bt_python/server.py:1088`)
- `message` (`src/lerobot_bt_python/server.py:1090`)
- `task` (`src/lerobot_bt_python/server.py:1092`)
- `allowed_statuses` list (`src/lerobot_bt_python/server.py:1094`)
- `allowed_next_actions` list (`src/lerobot_bt_python/server.py:1110`)

Manual protocol fixture mirrors this schema:
- `scripts/test_vlm_protocol.py:44`
- `scripts/test_vlm_protocol.py:45`
- `scripts/test_vlm_protocol.py:46`
- `scripts/test_vlm_protocol.py:47`
- `scripts/test_vlm_protocol.py:48`
- `scripts/test_vlm_protocol.py:50`
- `scripts/test_vlm_protocol.py:51`
- `scripts/test_vlm_protocol.py:55`

## Expected JSON Result Fields (/lerobot_bt/vlm_result -> server)

Server consumes result JSON in `_handle_vlm_result_topic`:
- Handler entrypoint: `src/lerobot_bt_python/server.py:1144`
- Requires JSON object payload and reads:
  - `skill_name` (`src/lerobot_bt_python/server.py:1167`)
  - `attempt_id` as `int(...)` (`src/lerobot_bt_python/server.py:1171`)
  - status/next-action/message via parser helpers (`src/lerobot_bt_python/server.py:184`, `src/lerobot_bt_python/server.py:201`, `src/lerobot_bt_python/server.py:213`, `src/lerobot_bt_python/server.py:229`)

Bridge-generated result payload contains:
- `skill_name` (`src/lerobot_bt_python/bt_vlm_bridge.py:260`)
- `attempt_id` as `int(...)` (`src/lerobot_bt_python/bt_vlm_bridge.py:262`)
- `status` (`src/lerobot_bt_python/bt_vlm_bridge.py:264`)
- `message` (`src/lerobot_bt_python/bt_vlm_bridge.py:266`)

## Status Vocabulary

Core status constants are defined in:
- `src/lerobot_bt_python/verification.py:24` (`PENDING`)
- `src/lerobot_bt_python/verification.py:26` (`RUNNING`)
- `src/lerobot_bt_python/verification.py:28` (`WAIT_HUMAN`)
- `src/lerobot_bt_python/verification.py:30` (`MANUAL_INTERVENTION_REQUIRED`)
- `src/lerobot_bt_python/verification.py:32` (`SUCCESS`)
- `src/lerobot_bt_python/verification.py:34` (`FAILURE`)
- Waiting set: `src/lerobot_bt_python/verification.py:48`

Bridge-to-BT mapping includes:
- `SUCCESS -> SUCCESS` (`src/lerobot_bt_python/bt_vlm_bridge.py:41`)
- `FAILED -> FAILURE` (`src/lerobot_bt_python/bt_vlm_bridge.py:43`)
- `STILL_RUNNING -> RUNNING` (`src/lerobot_bt_python/bt_vlm_bridge.py:47`)
- `RUNNING -> RUNNING` (`src/lerobot_bt_python/bt_vlm_bridge.py:49`)
- `PENDING -> PENDING` (`src/lerobot_bt_python/bt_vlm_bridge.py:51`)

Server also maps `next_action` tokens to statuses:
- Mapping table start: `src/lerobot_bt_python/server.py:116`
- Examples:
  - `CONTINUE -> SUCCESS` (`src/lerobot_bt_python/server.py:118`)
  - `RETRY_SKILL -> FAILURE` (`src/lerobot_bt_python/server.py:124`)
  - `WAIT_HUMAN -> WAIT_HUMAN` (`src/lerobot_bt_python/server.py:128`)
  - `REQUEST_MANUAL_INTERVENTION -> MANUAL_INTERVENTION_REQUIRED` (`src/lerobot_bt_python/server.py:130`)

## attempt_id Behavior

Request side:
- Outgoing request payload always writes `attempt_id` as integer: `src/lerobot_bt_python/server.py:1086`

Result ingest side:
- Incoming topic result parses `attempt_id` as integer: `src/lerobot_bt_python/server.py:1171`

Legacy/service registry behavior:
- Registry report API accepts optional `attempt_id` with default `0`:
  `src/lerobot_bt_python/verification.py:235`
- `attempt_id == 0` targets the latest attempt:
  `src/lerobot_bt_python/verification.py:270`

Bridge echo behavior:
- Bridge normalizes incoming request `attempt_id` to int:
  `src/lerobot_bt_python/bt_vlm_bridge.py:193`
- Bridge result publishes `attempt_id` copied from the active request state:
  `src/lerobot_bt_python/bt_vlm_bridge.py:262`

## Legacy Service Name/Config

- Config field is a service-name string and must be non-empty:
  - definition: `src/lerobot_bt_python/config.py:320`
  - non-empty validation: `src/lerobot_bt_python/config.py:496`
- Service type import includes `ReportSkillVerification`:
  - `src/lerobot_bt_python/server.py:498`
- Legacy service request handler:
  - `src/lerobot_bt_python/server.py:932`
