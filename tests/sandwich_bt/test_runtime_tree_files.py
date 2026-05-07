from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

EXPECTED_TREE_FILES = {
    "place_first_toast_subtree.xml",
    "place_second_toast_subtree.xml",
    "sandwich_tree.xml",
    "sandwich_tree_first_primitive_only.xml",
    "sandwich_tree_first_real_rest_simulated.xml",
    "sandwich_tree_two_real_skills_manual_vlm.xml",
}


def test_runtime_tree_directory_contains_only_supported_xml_files() -> None:
    tree_dir = Path(__file__).resolve().parents[2] / "src" / "sandwich_bt_runtime_cpp" / "trees"

    assert {path.name for path in tree_dir.glob("*.xml")} == EXPECTED_TREE_FILES


def test_runtime_tree_files_are_well_formed_xml() -> None:
    tree_dir = Path(__file__).resolve().parents[2] / "src" / "sandwich_bt_runtime_cpp" / "trees"

    for filename in EXPECTED_TREE_FILES:
        ElementTree.parse(tree_dir / filename)


def test_two_real_skills_manual_vlm_tree_matches_current_task() -> None:
    tree_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "sandwich_bt_runtime_cpp"
        / "trees"
        / "sandwich_tree_two_real_skills_manual_vlm.xml"
    )
    root = ElementTree.parse(tree_path).getroot()

    commands = [
        (node.attrib["kind"], node.attrib["command_name"])
        for node in root.iter()
        if node.tag == "RunNamedCommand"
    ]
    verifications = [node.attrib["skill_name"] for node in root.iter() if node.tag == "VerifySkillOutcome"]

    assert commands == [
        ("simulated_skill_pending", "initial_scene_ready"),
        ("skill", "place_first_toast"),
        ("simulated_skill_pending", "pour_ingredient"),
        ("skill", "place_second_toast"),
    ]
    assert verifications == [
        "initial_scene_ready",
        "place_first_toast",
        "pour_ingredient",
        "place_second_toast",
    ]
