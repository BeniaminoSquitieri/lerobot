# Runtime Flows

## Robot Skill

1. BT runs `RunNamedCommand(kind="skill")`.
2. Python executes the learned skill.
3. Python opens a `PENDING` VLM check attempt.
4. BT polls `VerifySkillOutcome`.
5. VLM reports a waiting status, `SUCCESS`, or `FAILURE`.
6. BT keeps waiting on `RUNNING`, `WAIT_HUMAN`, or
   `MANUAL_INTERVENTION_REQUIRED`.
7. BT advances on `SUCCESS` or retries the same BC skill on `FAILURE`.

## Human Or Initial Scene Gate

1. BT runs `RunNamedCommand(kind="simulated_skill_pending")`.
2. Python opens a `PENDING` VLM check attempt without moving the robot.
3. BT polls `VerifySkillOutcome`.
4. VLM reports `RUNNING`/`WAIT_HUMAN` while the scene or human action is still
   in progress.
5. VLM reports `SUCCESS` when the scene is ready.
