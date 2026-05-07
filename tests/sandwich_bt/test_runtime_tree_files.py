from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

EXPECTED_TREE_FILES = {
    "place_first_toast_subtree.xml",
    "place_second_toast_subtree.xml",
    "sandwich_tree.xml",
    "sandwich_tree_first_primitive_only.xml",
    "sandwich_tree_first_real_rest_simulated.xml",
}


def test_runtime_tree_directory_contains_only_supported_xml_files() -> None:
    tree_dir = Path(__file__).resolve().parents[2] / "src" / "sandwich_bt_runtime_cpp" / "trees"

    assert {path.name for path in tree_dir.glob("*.xml")} == EXPECTED_TREE_FILES


def test_runtime_tree_files_are_well_formed_xml() -> None:
    tree_dir = Path(__file__).resolve().parents[2] / "src" / "sandwich_bt_runtime_cpp" / "trees"

    for filename in EXPECTED_TREE_FILES:
        ElementTree.parse(tree_dir / filename)
