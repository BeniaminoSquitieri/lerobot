#!/usr/bin/env python3
"""Render BehaviorTree.CPP XML files to PNG diagrams.

The renderer is intentionally small and dependency-light: it parses the XML
trees with the standard library, resolves this package's simple `bt.*` YAML
profiles, writes temporary Graphviz DOT files, and calls `dot`.
"""

from __future__ import annotations

import argparse
import html
import shutil
import subprocess
import tempfile
from pathlib import Path
from xml.etree import ElementTree

TREE_TO_PROFILE = {
    "makesandwitch.xml": "makesandwitch_bt.yaml",
    "lunch_table_bussing.xml": "lunch_table_bussing_bt.yaml",
    "grocery_bagging.xml": "grocery_bagging_bt.yaml",
    "items_in_drawer.xml": "items_in_drawer_bt.yaml",
    "make_coffee.xml": "make_coffee_bt.yaml",
}


NODE_STYLE = {
    "Sequence": ("#e8f1ff", "#3f6ea8"),
    "RetryUntilSuccessful": ("#fff4d6", "#b57900"),
    "RunRobotSkill": ("#e4f8ec", "#16834a"),
    "PlaceFirstToast": ("#e4f8ec", "#16834a"),
    "PlaceSecondToast": ("#e4f8ec", "#16834a"),
    "OpenVLMGate": ("#f2e9ff", "#7353b6"),
    "PrepareInitialScene": ("#f2e9ff", "#7353b6"),
    "PrepareSecondToast": ("#f2e9ff", "#7353b6"),
    "WaitForGateVerdict": ("#ffe8dc", "#b85c2e"),
    "WaitForSkillVerdict": ("#ffe8dc", "#b85c2e"),
}
DEFAULT_STYLE = ("#f6f7f9", "#667085")


def load_bt_profile(profile_path: Path) -> dict[str, str]:
    """Load the flat `bt:` parameter block used by the runtime profiles."""
    values: dict[str, str] = {}
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
        values[key] = raw_value.strip().strip('"')

    return values


def resolve_value(raw_value: str, profile: dict[str, str]) -> str:
    """Resolve `{placeholder}` values using the BT profile."""
    if raw_value.startswith("{") and raw_value.endswith("}"):
        return profile.get(raw_value[1:-1], raw_value)
    return raw_value


def node_label(element: ElementTree.Element, profile: dict[str, str]) -> str:
    """Build a compact HTML label for a Graphviz node."""
    title = html.escape(element.attrib.get("name", element.tag))
    rows = [f"<B>{title}</B>", f"<FONT POINT-SIZE='10'>{html.escape(element.tag)}</FONT>"]

    for key in ("skill_name", "gate_name", "timeout_s", "num_attempts"):
        if key in element.attrib:
            value = resolve_value(element.attrib[key], profile)
            rows.append(
                f"<FONT POINT-SIZE='10'>{html.escape(key)}={html.escape(value)}</FONT>"
            )

    return "<" + "<BR/>".join(rows) + ">"


def iter_behavior_tree_nodes(root: ElementTree.Element) -> ElementTree.Element:
    """Return the main BehaviorTree node, failing clearly if it is missing."""
    behavior_tree = root.find("BehaviorTree")
    if behavior_tree is None:
        raise ValueError("XML file does not contain a BehaviorTree element.")
    return behavior_tree


def build_dot(tree_path: Path, profile_path: Path) -> str:
    """Convert one XML tree into a DOT graph."""
    profile = load_bt_profile(profile_path)
    root = ElementTree.parse(tree_path).getroot()
    behavior_tree = iter_behavior_tree_nodes(root)
    graph_lines = [
        "digraph BehaviorTree {",
        "  graph [rankdir=TB, bgcolor=\"white\", pad=\"0.3\", nodesep=\"0.45\", ranksep=\"0.55\"];",
        "  node [shape=box, style=\"rounded,filled\", fontname=\"DejaVu Sans\", fontsize=11, margin=\"0.10,0.08\"];",
        "  edge [color=\"#667085\", arrowsize=0.7];",
        "  labelloc=\"t\";",
        f"  label=<{html.escape(tree_path.stem.replace('_', ' ').title())}>;",
    ]
    counter = 0

    def add_node(element: ElementTree.Element, parent_id: str | None = None) -> None:
        nonlocal counter
        node_id = f"n{counter}"
        counter += 1
        fill, border = NODE_STYLE.get(element.tag, DEFAULT_STYLE)
        graph_lines.append(
            f"  {node_id} [label={node_label(element, profile)}, fillcolor=\"{fill}\", color=\"{border}\"];"
        )
        if parent_id is not None:
            graph_lines.append(f"  {parent_id} -> {node_id};")
        for child in list(element):
            add_node(child, node_id)

    for top_child in list(behavior_tree):
        add_node(top_child)

    graph_lines.append("}")
    return "\n".join(graph_lines) + "\n"


def render_tree(tree_path: Path, profile_path: Path, output_path: Path) -> None:
    """Render one tree to PNG through Graphviz."""
    dot_source = build_dot(tree_path, profile_path)
    with tempfile.NamedTemporaryFile("w", suffix=".dot", encoding="utf-8", delete=False) as dot_file:
        dot_file.write(dot_source)
        dot_path = Path(dot_file.name)
    try:
        subprocess.run(
            ["dot", "-Tpng", str(dot_path), "-o", str(output_path)],
            check=True,
        )
    finally:
        dot_path.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    package_dir = Path(__file__).resolve().parents[1]
    parser.add_argument("--tree-dir", type=Path, default=package_dir / "trees")
    parser.add_argument("--config-dir", type=Path, default=package_dir / "config")
    parser.add_argument("--output-dir", type=Path, default=package_dir / "diagrams")
    return parser.parse_args()


def main() -> None:
    if shutil.which("dot") is None:
        raise RuntimeError("Graphviz 'dot' executable was not found.")

    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for tree_name, profile_name in TREE_TO_PROFILE.items():
        output_path = args.output_dir / f"{Path(tree_name).stem}_bt.png"
        render_tree(
            tree_path=args.tree_dir / tree_name,
            profile_path=args.config_dir / profile_name,
            output_path=output_path,
        )
        print(output_path)


if __name__ == "__main__":
    main()
