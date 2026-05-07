# Troubleshooting

## BT Does Not Advance

Check the verification state:

```bash
ros2 service call /sandwich_bt/get_skill_verification \
  sandwich_bt_interfaces/srv/GetSkillVerification \
  "{skill_name: place_first_toast}"
```

If the status is `PENDING`, the BT is correctly waiting for a VLM/manual
verdict.

## Manually Resolve A Gate

```bash
ros2 service call /sandwich_bt/report_skill_verification \
  sandwich_bt_interfaces/srv/ReportSkillVerification \
  "{skill_name: place_first_toast, attempt_id: 0, status: SUCCESS, message: 'ok', confidence: 0.95}"
```

## Unsupported Command Kind

The active server supports:

- `skill`
- `simulated_skill`
- `simulated_skill_pending`

`recovery` and `simulated_recovery` are intentionally unsupported in the active
runtime path.
