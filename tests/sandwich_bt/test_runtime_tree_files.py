from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

EXPECTED_TREE_FILES = {
    "grocery_bagging.xml",
    "items_in_drawer.xml",
    "lunch_table_bussing.xml",
    "make_coffee.xml",
    "makesandwitch.xml",
}
VERDICT_NODE_TAGS = {"WaitForGateVerdict", "WaitForSkillVerdict"}
EXPECTED_BT_PROFILE = {
    "initial_scene_ready_gate": "initial_scene_ready",
    "place_first_toast_skill": "place_first_toast",
    "place_first_toast_timeout_s": 120.0,
    "pour_ingredient_gate": "pour_ingredient",
    "second_toast_ready_gate": "second_toast_ready",
    "place_second_toast_skill": "place_second_toast",
    "place_second_toast_timeout_s": 30.0,
}
EXPECTED_SCENE_TASK_SKILLS = {
    "lunch_table_bussing.xml": [
        "pick_and_dispose_trash",
        "clear_plate",
        "pick_and_store_cutlery",
        "pick_and_store_dishware",
    ],
    "grocery_bagging.xml": [
        "bag_rigid_or_cylindrical_item",
        "bag_flat_or_long_item",
        "bag_soft_or_fragile_item",
    ],
    "items_in_drawer.xml": [
        "open_drawer",
        "pick_object_for_drawer",
        "insert_object_in_drawer",
        "close_drawer",
    ],
    "make_coffee.xml": [
        "place_cup_under_dispenser",
        "pick_and_insert_capsule",
        "press_start_button",
    ],
}
EXPECTED_SCENE_TASK_GATES = {
    "lunch_table_bussing.xml": ["lunch_table_bussing.scene_0_ready"],
    "grocery_bagging.xml": ["grocery_bagging.scene_0_ready"],
    "items_in_drawer.xml": ["items_in_drawer.scene_0_ready"],
    "make_coffee.xml": ["make_coffee.scene_0_ready", "make_coffee.scene_4_ready"],
}
EXPECTED_SCENE_TASK_BT_PROFILES = {
    "lunch_table_bussing.xml": "lunch_table_bussing_bt.yaml",
    "grocery_bagging.xml": "grocery_bagging_bt.yaml",
    "items_in_drawer.xml": "items_in_drawer_bt.yaml",
    "make_coffee.xml": "make_coffee_bt.yaml",
}
EXPECTED_SCENE_TASK_EXECUTOR_PROFILES = {
    "lunch_table_bussing.xml": "lunch_table_bussing_executor.yaml",
    "grocery_bagging.xml": "grocery_bagging_executor.yaml",
    "items_in_drawer.xml": "items_in_drawer_executor.yaml",
    "make_coffee.xml": "make_coffee_executor.yaml",
}


def _runtime_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "sandwich_bt_runtime_cpp"


def _python_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "sandwich_bt_python"


def _load_executor_profile_skill_names(profile_path: Path) -> list[str]:
    skill_names: list[str] = []
    for line in profile_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- name:"):
            skill_names.append(stripped.split(":", 1)[1].strip().strip('"'))
    return skill_names


def _load_executor_profile_pretrained_paths(profile_path: Path) -> list[str]:
    pretrained_paths: list[str] = []
    for line in profile_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("pretrained_path:"):
            pretrained_paths.append(stripped.split(":", 1)[1].strip().strip('"'))
    return pretrained_paths


def _load_simple_bt_profile(profile_path: Path) -> dict[str, float | str]:
    """Parse the small ROS2 params profile without adding a test dependency."""
    values: dict[str, float | str] = {}
    in_bt_block = False
    bt_indent = 0

    for line in profile_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        if stripped == "bt:":
            in_bt_block = True
            bt_indent = indent
            continue

        if in_bt_block and indent <= bt_indent:
            break
        if not in_bt_block or ":" not in stripped:
            continue

        key, raw_value = stripped.split(":", 1)
        raw_value = raw_value.strip()
        if raw_value.startswith('"') and raw_value.endswith('"'):
            values[key] = raw_value[1:-1]
        else:
            values[key] = float(raw_value)

    return values


def _resolve_bt_refs(refs: list[str], profile: dict[str, float | str]) -> list[str]:
    resolved_refs: list[str] = []
    for ref in refs:
        if ref.startswith("{") and ref.endswith("}"):
            resolved_refs.append(str(profile[ref[1:-1]]))
        else:
            resolved_refs.append(ref)
    return resolved_refs


def _tree_placeholders(root) -> set[str]:
    return {
        value[1:-1]
        for node in root.iter()
        for value in node.attrib.values()
        if value.startswith("{") and value.endswith("}")
    }


def test_runtime_tree_directory_contains_only_supported_xml_files() -> None:
    tree_dir = _runtime_dir() / "trees"

    assert {path.name for path in tree_dir.glob("*.xml")} == EXPECTED_TREE_FILES


def test_runtime_tree_files_are_well_formed_xml() -> None:
    tree_dir = _runtime_dir() / "trees"

    for filename in EXPECTED_TREE_FILES:
        ElementTree.parse(tree_dir / filename)


def test_runtime_tree_files_expose_readable_verdict_nodes_for_groot() -> None:
    tree_dir = _runtime_dir() / "trees"

    for filename in EXPECTED_TREE_FILES:
        tags = {node.tag for node in ElementTree.parse(tree_dir / filename).getroot().iter()}

        assert "VerifySkillOutcome" not in tags
        assert "WaitForVLMDecision" not in tags
        assert "VLMReplanningDecision" not in tags
        assert "WaitForGateVerdict" in tags
        assert "WaitForSkillVerdict" in tags


def test_makesandwitch_tree_matches_current_task() -> None:
    tree_path = _runtime_dir() / "trees" / "makesandwitch.xml"
    root = ElementTree.parse(tree_path).getroot()

    start_nodes = [
        (node.tag, node.attrib.get("gate_name", node.attrib.get("skill_name")))
        for node in root.iter()
        if node.tag in {
            "PrepareInitialScene",
            "PlaceFirstToast",
            "OpenVLMGate",
            "PrepareSecondToast",
            "PlaceSecondToast",
        }
    ]
    verdict_nodes = [
        (node.tag, node.attrib.get("gate_name", node.attrib.get("skill_name")))
        for node in root.iter()
        if node.tag in VERDICT_NODE_TAGS
    ]
    retry_nodes = [
        node.attrib["name"]
        for node in root.iter()
        if node.tag == "RetryUntilSuccessful" and "name" in node.attrib
    ]

    assert start_nodes == [
        ("PrepareInitialScene", "{initial_scene_ready_gate}"),
        ("PlaceFirstToast", "{place_first_toast_skill}"),
        ("OpenVLMGate", "{pour_ingredient_gate}"),
        ("PrepareSecondToast", "{second_toast_ready_gate}"),
        ("PlaceSecondToast", "{place_second_toast_skill}"),
    ]
    assert verdict_nodes == [
        ("WaitForGateVerdict", "{initial_scene_ready_gate}"),
        ("WaitForSkillVerdict", "{place_first_toast_skill}"),
        ("WaitForGateVerdict", "{pour_ingredient_gate}"),
        ("WaitForGateVerdict", "{second_toast_ready_gate}"),
        ("WaitForSkillVerdict", "{place_second_toast_skill}"),
    ]
    assert retry_nodes == [
        "STAGE 0 - Initial scene ready",
        "STAGE 1 - Place first toast",
        "STAGE 2 - Human pours ingredient",
        "STAGE 3 - Second toast ready",
        "STAGE 4 - Place second toast",
    ]


def test_scene_gated_task_trees_match_expected_task_order() -> None:
    tree_dir = _runtime_dir() / "trees"
    config_dir = _runtime_dir() / "config"

    for filename, expected_skills in EXPECTED_SCENE_TASK_SKILLS.items():
        root = ElementTree.parse(tree_dir / filename).getroot()
        profile = _load_simple_bt_profile(config_dir / EXPECTED_SCENE_TASK_BT_PROFILES[filename])

        skill_refs = [node.attrib["skill_name"] for node in root.iter("RunRobotSkill")]
        gate_refs = [node.attrib["gate_name"] for node in root.iter("OpenVLMGate")]

        assert _resolve_bt_refs(skill_refs, profile) == expected_skills
        assert _resolve_bt_refs(gate_refs, profile) == EXPECTED_SCENE_TASK_GATES[filename]
        assert _tree_placeholders(root) <= set(profile)


def test_scene_gated_executor_profiles_cover_xml_skill_names() -> None:
    profile_dir = _python_dir()

    for filename, profile_name in EXPECTED_SCENE_TASK_EXECUTOR_PROFILES.items():
        profile_path = profile_dir / profile_name
        expected_skills = EXPECTED_SCENE_TASK_SKILLS[filename]

        assert profile_path.exists()
        pretrained_paths = _load_executor_profile_pretrained_paths(profile_path)
        assert _load_executor_profile_skill_names(profile_path) == expected_skills
        assert len(pretrained_paths) == len(expected_skills)
        assert all(pretrained_paths)


def test_makesandwitch_profile_matches_current_robot_task() -> None:
    profile_path = _runtime_dir() / "config" / "makesandwitch_bt.yaml"

    assert _load_simple_bt_profile(profile_path) == EXPECTED_BT_PROFILE


def test_makesandwitch_tree_placeholders_are_defined_in_profile() -> None:
    tree_path = _runtime_dir() / "trees" / "makesandwitch.xml"
    profile_keys = set(_load_simple_bt_profile(_runtime_dir() / "config" / "makesandwitch_bt.yaml"))
    root = ElementTree.parse(tree_path).getroot()

    placeholders = {
        value[1:-1]
        for node in root.iter()
        for value in node.attrib.values()
        if value.startswith("{") and value.endswith("}")
    }

    assert placeholders == {
        "initial_scene_ready_gate",
        "place_first_toast_skill",
        "place_first_toast_timeout_s",
        "pour_ingredient_gate",
        "second_toast_ready_gate",
        "place_second_toast_skill",
        "place_second_toast_timeout_s",
    }
    assert placeholders <= profile_keys
