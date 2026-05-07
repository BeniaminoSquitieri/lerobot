# Runtime Flows

## Robot Skill

1. BT runs `RunNamedCommand(kind="skill")`.
2. Python executes the learned skill.
3. Python opens a `PENDING` verification attempt.
4. BT polls `VerifySkillOutcome`.
5. VLM reports `SUCCESS` or `FAILURE`.
6. BT advances on `SUCCESS` or retries the same BC skill on `FAILURE`.

## Human Or Initial Scene Gate

1. BT runs `RunNamedCommand(kind="simulated_skill_pending")`.
2. Python opens a `PENDING` verification attempt without moving the robot.
3. BT polls `VerifySkillOutcome`.
4. VLM reports `SUCCESS` when the scene is ready.
