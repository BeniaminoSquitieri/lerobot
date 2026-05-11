from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

EXPECTED_TREE_FILES = {
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


def _runtime_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "sandwich_bt_runtime_cpp"


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
