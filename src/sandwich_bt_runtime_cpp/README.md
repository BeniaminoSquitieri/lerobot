# Sandwich BT Runtime C++

C++ BehaviorTree.CPP runtime for the sandwich BT stack.

For build/run instructions and the architecture overview, use the shared guide:

- [`../sandwich_bt_README.md`](../sandwich_bt_README.md)

## Responsibility

This package owns BT orchestration.

It owns:

- loading BT XML trees
- registering the `RunNamedCommand` BT leaf
- ticking the tree until success or failure
- converting service replies into BT `SUCCESS` or `FAILURE`
- publishing to Groot when supported by the installed BehaviorTree.CPP version

It does not own:

- policy loading
- robot connection
- scripted recovery implementation

Those belong to `sandwich_bt_python`.

## Files

- `src/sandwich_bt_main.cpp`: runner executable
- `src/run_named_command_node.cpp`: service-backed BT leaf implementation
- `include/sandwich_bt_runtime_cpp/run_named_command_node.hpp`: BT leaf declaration
- `trees/sandwich_tree.xml`: full sandwich task tree
- `trees/sandwich_tree_first_primitive_only.xml`: bring-up tree for only `place_first_toast`
- `trees/place_first_toast_subtree.xml`: retry/recovery subtree for the first toast step
- `trees/pour_subtree.xml`: retry/recovery subtree for the pouring step
- `trees/place_second_toast_subtree.xml`: retry/recovery subtree for the second toast step
