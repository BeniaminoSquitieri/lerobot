"""Deterministic task-name to Linear IR planner for BT generation."""

from __future__ import annotations

from .registry import HUMAN_STEP, ROBOT_SKILL, VLM_GATE, Registry


TASK_TEMPLATES: dict[str, list[dict[str, str]]] = {
    # The sandwich sources expose place_first_toast/place_second_toast as real
    # executor skills, while pour_ingredient is an AwaitScene/manual gate.
    "make_sandwich": [
        {"kind": VLM_GATE, "name": "initial_scene_ready"},
        {"kind": ROBOT_SKILL, "name": "place_first_toast"},
        {"kind": HUMAN_STEP, "name": "pour_ingredient"},
        {"kind": VLM_GATE, "name": "second_toast_ready"},
        {"kind": ROBOT_SKILL, "name": "place_second_toast"},
        {"kind": VLM_GATE, "name": "make_sandwich.task_complete"},
    ],
    # Existing XML comments and VLM gate names show the human prepares the
    # tablecloth, tea box, and spoon; robot skills are only those in executor
    # YAML expected_skill_names/skills.
    "set_breakfast_table": [
        {"kind": HUMAN_STEP, "name": "breakfast_table.tablecloth_ready"},
        {"kind": ROBOT_SKILL, "name": "place_cereal_box"},
        {"kind": HUMAN_STEP, "name": "breakfast_table.tea_box_ready"},
        {"kind": ROBOT_SKILL, "name": "place_bottle"},
        {"kind": ROBOT_SKILL, "name": "place_cup"},
        {"kind": HUMAN_STEP, "name": "breakfast_table.spoon_ready"},
        {"kind": ROBOT_SKILL, "name": "place_bowl"},
        {"kind": VLM_GATE, "name": "breakfast_table.task_complete"},
    ],
    # Coffee XML has two human AwaitScene stages and two robot skills.
    "make_coffee": [
        {"kind": VLM_GATE, "name": "make_coffee.scene_0_ready"},
        {"kind": HUMAN_STEP, "name": "make_coffee.cup_under_dispenser"},
        {"kind": ROBOT_SKILL, "name": "pick_and_insert_capsule"},
        {"kind": ROBOT_SKILL, "name": "close_coffee_machine"},
        {"kind": HUMAN_STEP, "name": "make_coffee.human_press_start_button"},
    ],
    # Picnic bag XML alternates human bag/item steps with two robot insertions.
    "prepare_picnic_bag": [
        {"kind": VLM_GATE, "name": "prepare_picnic_bag.scene_0_ready"},
        {"kind": HUMAN_STEP, "name": "prepare_picnic_bag.human_open_bag"},
        {"kind": HUMAN_STEP, "name": "prepare_picnic_bag.human_insert_monster"},
        {"kind": ROBOT_SKILL, "name": "bag_bread"},
        {"kind": HUMAN_STEP, "name": "prepare_picnic_bag.human_insert_mustard"},
        {"kind": ROBOT_SKILL, "name": "bag_pear"},
    ],
    # The insertion skill is intentionally retried by RetryUntilSuccessful
    # until the VLM reports that all drawer items have been inserted.
    "items_in_drawer": [
        {"kind": VLM_GATE, "name": "items_in_drawer.scene_0_ready"},
        {"kind": HUMAN_STEP, "name": "items_in_drawer.drawer_open_ready"},
        {"kind": ROBOT_SKILL, "name": "insert_next_drawer_item"},
        {"kind": HUMAN_STEP, "name": "items_in_drawer.drawer_closed"},
        {"kind": VLM_GATE, "name": "items_in_drawer.task_complete"},
    ],
}


def build_linear_plan(
    task_name: str,
    registry: Registry,
    *,
    explicit_robot_postcondition_gates: bool = False,
) -> dict:
    """Build a deterministic Linear IR plan for a known task name."""

    if task_name not in TASK_TEMPLATES:
        known = ", ".join(sorted(TASK_TEMPLATES))
        raise ValueError(f"Unknown task_name {task_name!r}. Known tasks: {known}.")

    template = TASK_TEMPLATES[task_name]
    steps: list[dict[str, str]] = []
    for index, step in enumerate(template):
        kind = step["kind"]
        name = step["name"]
        _require_registry_match(registry, kind, name)
        steps.append({"kind": kind, "name": name})

        if kind not in {ROBOT_SKILL, HUMAN_STEP}:
            continue
        if kind == ROBOT_SKILL and not explicit_robot_postcondition_gates:
            _validate_verify_after_target(registry, kind, name)
            continue

        verify_after = registry.get(kind, name).verify_after
        if not verify_after:
            continue
        _require_registry_match(registry, VLM_GATE, verify_after)

        next_step = template[index + 1] if index + 1 < len(template) else None
        if next_step == {"kind": VLM_GATE, "name": verify_after}:
            continue
        steps.append({"kind": VLM_GATE, "name": verify_after})

    return {"task_name": task_name, "steps": steps}


def _validate_verify_after_target(registry: Registry, kind: str, name: str) -> None:
    verify_after = registry.get(kind, name).verify_after
    if verify_after:
        _require_registry_match(registry, VLM_GATE, verify_after)


def _require_registry_match(registry: Registry, kind: str, name: str) -> None:
    actual_kind = registry.kind_for_name(name)
    if actual_kind is None:
        raise ValueError(f"{name!r} is not present in the BT generation registry.")
    if actual_kind == "ambiguous":
        raise ValueError(f"{name!r} is ambiguous in the BT generation registry.")
    if actual_kind != kind:
        raise ValueError(
            f"Template classifies {name!r} as {kind!r}, but the registry classifies it "
            f"as {actual_kind!r}."
        )
