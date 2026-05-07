from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

EXPECTED_TREE_FILES = {
    "sandwich_tree.xml",
    "sandwich_tree_first_real_rest_simulated.xml",
    "sandwich_tree_two_real_skills_manual_vlm.xml",
}
VERIFY_NODE_TAGS = {"VerifySkillOutcome", "WaitForVLMDecision", "VLMReplanningDecision"}


def test_runtime_tree_directory_contains_only_supported_xml_files() -> None:
    tree_dir = Path(__file__).resolve().parents[2] / "src" / "sandwich_bt_runtime_cpp" / "trees"

    assert {path.name for path in tree_dir.glob("*.xml")} == EXPECTED_TREE_FILES


def test_runtime_tree_files_are_well_formed_xml() -> None:
    tree_dir = Path(__file__).resolve().parents[2] / "src" / "sandwich_bt_runtime_cpp" / "trees"

    for filename in EXPECTED_TREE_FILES:
        ElementTree.parse(tree_dir / filename)


def test_runtime_tree_files_expose_vlm_replanning_nodes_for_groot() -> None:
    tree_dir = Path(__file__).resolve().parents[2] / "src" / "sandwich_bt_runtime_cpp" / "trees"

    for filename in EXPECTED_TREE_FILES:
        tags = {node.tag for node in ElementTree.parse(tree_dir / filename).getroot().iter()}

        assert "VerifySkillOutcome" not in tags
        assert "WaitForVLMDecision" in tags
        assert "VLMReplanningDecision" in tags


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
    vlm_check_nodes = [
        (node.tag, node.attrib["skill_name"])
        for node in root.iter()
        if node.tag in VERIFY_NODE_TAGS
    ]
    retry_nodes = [
        node.attrib["name"]
        for node in root.iter()
        if node.tag == "RetryUntilSuccessful" and "name" in node.attrib
    ]

    assert commands == [
        ("simulated_skill_pending", "initial_scene_ready"),
        ("skill", "place_first_toast"),
        ("simulated_skill_pending", "pour_ingredient"),
        ("skill", "place_second_toast"),
    ]
    assert vlm_check_nodes == [
        ("WaitForVLMDecision", "initial_scene_ready"),
        ("VLMReplanningDecision", "place_first_toast"),
        ("WaitForVLMDecision", "pour_ingredient"),
        ("VLMReplanningDecision", "place_second_toast"),
    ]
    assert retry_nodes == [
        "retry_initial_scene_until_vlm_success",
        "retry_place_first_toast_on_vlm_retry_skill",
        "retry_human_pouring_until_vlm_success",
        "retry_place_second_toast_on_vlm_retry_skill",
    ]
