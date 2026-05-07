# Troubleshooting

## BT Does Not Advance

Check the VLM check state:

```bash
ros2 service call /sandwich_bt/vlm_state \
  sandwich_bt_interfaces/srv/GetSkillVerification \
  "{skill_name: place_first_toast}"
```

If the status is `PENDING`, `RUNNING`, `WAIT_HUMAN`, or
`MANUAL_INTERVENTION_REQUIRED`, the BT is correctly waiting for a VLM/manual
update.

## Manually Resolve A Gate

```bash
ros2 topic pub --once /sandwich_bt/vlm_result std_msgs/msg/String \
  "{data: '{\"skill_name\":\"place_first_toast\",\"attempt_id\":0,\"status\":\"SUCCESS\",\"message\":\"ok\"}'}"
```

## Unsupported Command Kind

The active server supports:

- `skill`
- `simulated_skill`
- `simulated_skill_pending`

`recovery` and `simulated_recovery` are intentionally unsupported in the active
runtime path.
