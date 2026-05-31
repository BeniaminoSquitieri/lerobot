# Generated BT Artifacts

This directory is the preferred repository-local place for runtime-generated
Behavior Tree artifacts.

The generator can still write to `/tmp` for quick experiments, but
`generated_bt/` keeps outputs visible and easy to inspect while developing.

Directory layout:

- `plans/`: validated Linear IR JSON plans used to generate BTs.
- `trees/`: generated BehaviorTree.CPP XML files.
- `config/`: generated BT parameter YAML files.
- `raw_model_responses/`: optional raw planner responses from model-response or
  future ROS-service planner modes, useful for debugging.


When using the `ros-service` planner mode, raw plan responses from the remote VLM server are saved in `raw_model_responses/` for debugging and inspection. This mode is now implemented and available in the CLI.

Generated files should generally not be committed unless they are intentionally
being added as fixtures or examples. The repository keeps this README and the
empty folders, while normal generated artifacts are ignored by git.
