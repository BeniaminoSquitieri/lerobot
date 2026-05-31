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
  ROS-service planner modes, useful for debugging.


When using the `ros-service` planner mode, `lerobot` exports a planner payload
that includes `canonical_task_sequence` and `ordering_constraints`. The remote
VLM server should return Linear IR JSON following that sequence; `lerobot`
validates the returned order before writing XML/YAML.

`lerobot_bt_python.bt_generation.generate_and_run` uses these generated
`trees/` and `config/` files to launch the existing C++ BehaviorTree.CPP runner.
It generates the BT once before execution; it does not hot-swap or replan while
the tree is ticking.

Generated files should generally not be committed unless they are intentionally
being added as fixtures or examples. The repository keeps this README and the
empty folders, while normal generated artifacts are ignored by git.
