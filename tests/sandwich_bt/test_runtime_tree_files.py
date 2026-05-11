from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

EXPECTED_TREE_FILES = {
    "makesandwitch.xml",
}
VERDICT_NODE_TAGS = {"WaitForGateVerdict", "WaitForSkillVerdict"}


def test_runtime_tree_directory_contains_only_supported_xml_files() -> None:
    tree_dir = Path(__file__).resolve().parents[2] / "src" / "sandwich_bt_runtime_cpp" / "trees"

    assert {path.name for path in tree_dir.glob("*.xml")} == EXPECTED_TREE_FILES


def test_runtime_tree_files_are_well_formed_xml() -> None:
    tree_dir = Path(__file__).resolve().parents[2] / "src" / "sandwich_bt_runtime_cpp" / "trees"

    for filename in EXPECTED_TREE_FILES:
        ElementTree.parse(tree_dir / filename)


def test_runtime_tree_files_expose_readable_verdict_nodes_for_groot() -> None:
    tree_dir = Path(__file__).resolve().parents[2] / "src" / "sandwich_bt_runtime_cpp" / "trees"

    for filename in EXPECTED_TREE_FILES:
        tags = {node.tag for node in ElementTree.parse(tree_dir / filename).getroot().iter()}

        assert "VerifySkillOutcome" not in tags
        assert "WaitForVLMDecision" not in tags
        assert "VLMReplanningDecision" not in tags
        assert "WaitForGateVerdict" in tags
        assert "WaitForSkillVerdict" in tags


def test_makesandwitch_tree_matches_current_task() -> None:
    tree_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "sandwich_bt_runtime_cpp"
        / "trees"
        / "makesandwitch.xml"
    )
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
        ("PrepareInitialScene", "initial_scene_ready"),
        ("PlaceFirstToast", "place_first_toast"),
        ("OpenVLMGate", "pour_ingredient"),
        ("PrepareSecondToast", "second_toast_ready"),
        ("PlaceSecondToast", "place_second_toast"),
    ]
    assert verdict_nodes == [
        ("WaitForGateVerdict", "initial_scene_ready"),
        ("WaitForSkillVerdict", "place_first_toast"),
        ("WaitForGateVerdict", "pour_ingredient"),
        ("WaitForGateVerdict", "second_toast_ready"),
        ("WaitForSkillVerdict", "place_second_toast"),
    ]
    assert retry_nodes == [
        "STAGE 0 - Initial scene ready",
        "STAGE 1 - Place first toast",
        "STAGE 2 - Human pours ingredient",
        "STAGE 3 - Second toast ready",
        "STAGE 4 - Place second toast",
    ]
