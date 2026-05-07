# Architecture

```text
sandwich_bt_runtime_cpp
  -> RunNamedCommand
  -> sandwich_bt_python
  -> GetSkillVerification
  -> waits while PENDING

VLM/manual verifier
  -> ReportSkillVerification
  -> sandwich_bt_python
```

There is no separate planning supervisor in the active runtime path.

The BT XML represents both robot actions and VLM gates:

- robot actions use `kind="skill"`;
- non-robot gates use `kind="simulated_skill_pending"`.

There are no deterministic Panda recovery motions in the active runtime path.
If the VLM reports `FAILURE`, the XML-level `RetryUntilSuccessful` node starts
the same BC skill again from the beginning.
