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
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image, ImageDraw, ImageFont

TREE_TO_PROFILE = {
    "make_sandwich.xml": "make_sandwich_bt.yaml",
    "set_breakfast_table.xml": "set_breakfast_table_bt.yaml",
    "prepare_picnic_bag.xml": "prepare_picnic_bag_bt.yaml",
    "items_in_drawer.xml": "items_in_drawer_bt.yaml",
    "make_coffee.xml": "make_coffee_bt.yaml",
}


NODE_STYLE = {
    "Sequence": ("#e8f1ff", "#3f6ea8"),
    "RetryUntilSuccessful": ("#fff4d6", "#b57900"),
    "RunRobotSkill": ("#e4f8ec", "#16834a"),
    "OpenVLMGate": ("#f2e9ff", "#7353b6"),
    "WaitForVLMVerdict": ("#ffe8dc", "#b85c2e"),
}
DEFAULT_STYLE = ("#f6f7f9", "#667085")
BOX_RADIUS = 12
BOX_GAP_X = 36
BOX_GAP_Y = 64
TEXT_PAD_X = 18
TEXT_PAD_Y = 12
LINE_GAP = 6
TITLE_MARGIN_Y = 28
CANVAS_MARGIN = 40


@dataclass
class LayoutNode:
    """In-memory tree node used by the Pillow fallback renderer."""

    lines: list[str]
    fill: str
    border: str
    children: list["LayoutNode"] = field(default_factory=list)
    width: int = 0
    height: int = 0
    subtree_width: int = 0
    x: int = 0
    y: int = 0


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


def node_lines(element: ElementTree.Element, profile: dict[str, str]) -> list[str]:
    """Build plain-text lines shared by Graphviz and Pillow renderers."""
    rows = [element.attrib.get("name", element.tag), element.tag]

    for key in ("skill_name", "gate_name", "check_name", "timeout_s", "num_attempts"):
        if key in element.attrib:
            value = resolve_value(element.attrib[key], profile)
            rows.append(f"{key}={value}")

    if element.tag == "OpenVLMGate":
        rows.append("publish /lerobot_bt/vlm_request")
    if element.tag == "WaitForVLMVerdict":
        rows.append("wait /lerobot_bt/vlm_result to advance")

    return rows


def node_label(element: ElementTree.Element, profile: dict[str, str]) -> str:
    """Build a compact HTML label for a Graphviz node."""
    escaped_rows = []
    for index, row in enumerate(node_lines(element, profile)):
        if index == 0:
            escaped_rows.append(f"<B>{html.escape(row)}</B>")
        else:
            escaped_rows.append(f"<FONT POINT-SIZE='10'>{html.escape(row)}</FONT>")

    return "<" + "<BR/>".join(escaped_rows) + ">"


def _load_fonts() -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    """Load readable fonts for the Pillow fallback renderer."""
    try:
        return (
            ImageFont.truetype("DejaVuSans-Bold.ttf", 18),
            ImageFont.truetype("DejaVuSans.ttf", 14),
        )
    except OSError:
        default_font = ImageFont.load_default()
        return default_font, default_font


def _measure_multiline(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    title_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    body_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> tuple[int, int]:
    """Measure one node box for the Pillow fallback renderer."""
    widths: list[int] = []
    heights: list[int] = []
    for index, line in enumerate(lines):
        font = title_font if index == 0 else body_font
        bbox = draw.textbbox((0, 0), line, font=font)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    width = max(widths, default=0) + (2 * TEXT_PAD_X)
    text_height = sum(heights) + (LINE_GAP * max(0, len(lines) - 1))
    height = text_height + (2 * TEXT_PAD_Y)
    return width, height


def _build_layout_tree(element: ElementTree.Element, profile: dict[str, str]) -> LayoutNode:
    """Convert an XML node into a drawable layout tree."""
    fill, border = NODE_STYLE.get(element.tag, DEFAULT_STYLE)
    return LayoutNode(
        lines=node_lines(element, profile),
        fill=fill,
        border=border,
        children=[_build_layout_tree(child, profile) for child in list(element)],
    )


def _measure_layout(
    node: LayoutNode,
    draw: ImageDraw.ImageDraw,
    title_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    body_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    """Populate node dimensions and subtree widths recursively."""
    node.width, node.height = _measure_multiline(draw, node.lines, title_font, body_font)
    for child in node.children:
        _measure_layout(child, draw, title_font, body_font)
    if not node.children:
        node.subtree_width = node.width
        return

    children_width = sum(child.subtree_width for child in node.children)
    children_width += BOX_GAP_X * max(0, len(node.children) - 1)
    node.subtree_width = max(node.width, children_width)


def _place_layout(node: LayoutNode, left: int, top: int) -> None:
    """Assign top-left coordinates recursively."""
    node.x = left + (node.subtree_width - node.width) // 2
    node.y = top
    if not node.children:
        return

    total_children_width = sum(child.subtree_width for child in node.children)
    total_children_width += BOX_GAP_X * max(0, len(node.children) - 1)
    child_left = left + (node.subtree_width - total_children_width) // 2
    child_top = top + node.height + BOX_GAP_Y
    for child in node.children:
        _place_layout(child, child_left, child_top)
        child_left += child.subtree_width + BOX_GAP_X


def _tree_bounds(node: LayoutNode) -> tuple[int, int]:
    """Return the maximum x/y extents of one layout tree."""
    max_x = node.x + node.width
    max_y = node.y + node.height
    for child in node.children:
        child_max_x, child_max_y = _tree_bounds(child)
        max_x = max(max_x, child_max_x)
        max_y = max(max_y, child_max_y)
    return max_x, max_y


def _draw_layout(
    draw: ImageDraw.ImageDraw,
    node: LayoutNode,
    title_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    body_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    """Draw the laid-out tree nodes and edges."""
    parent_mid_x = node.x + (node.width // 2)
    parent_bottom_y = node.y + node.height
    for child in node.children:
        child_mid_x = child.x + (child.width // 2)
        child_top_y = child.y
        draw.line(
            [(parent_mid_x, parent_bottom_y), (parent_mid_x, parent_bottom_y + 18)],
            fill="#667085",
            width=3,
        )
        draw.line(
            [(parent_mid_x, parent_bottom_y + 18), (child_mid_x, child_top_y - 18)],
            fill="#667085",
            width=3,
        )
        draw.line(
            [(child_mid_x, child_top_y - 18), (child_mid_x, child_top_y)],
            fill="#667085",
            width=3,
        )
        _draw_layout(draw, child, title_font, body_font)

    draw.rounded_rectangle(
        [node.x, node.y, node.x + node.width, node.y + node.height],
        radius=BOX_RADIUS,
        fill=node.fill,
        outline=node.border,
        width=3,
    )

    text_y = node.y + TEXT_PAD_Y
    for index, line in enumerate(node.lines):
        font = title_font if index == 0 else body_font
        fill = "#0f172a" if index == 0 else "#334155"
        draw.text((node.x + TEXT_PAD_X, text_y), line, font=font, fill=fill)
        bbox = draw.textbbox((node.x + TEXT_PAD_X, text_y), line, font=font)
        text_y = bbox[3] + LINE_GAP


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
    top_children = list(behavior_tree)
    if top_children:
        graph_title = top_children[0].attrib.get(
            "name",
            tree_path.stem.replace("_", " ").title(),
        )
    else:
        graph_title = tree_path.stem.replace("_", " ").title()
    graph_lines = [
        "digraph BehaviorTree {",
        "  graph [rankdir=TB, bgcolor=\"white\", pad=\"0.3\", nodesep=\"0.45\", ranksep=\"0.55\"];",
        "  node [shape=box, style=\"rounded,filled\", fontname=\"DejaVu Sans\", fontsize=11, margin=\"0.10,0.08\"];",
        "  edge [color=\"#667085\", arrowsize=0.7];",
        "  labelloc=\"t\";",
        f"  label=<{html.escape(graph_title)}>;",
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

    for top_child in top_children:
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


def render_tree_with_pillow(tree_path: Path, profile_path: Path, output_path: Path) -> None:
    """Render one tree to PNG without Graphviz, using Pillow only."""
    profile = load_bt_profile(profile_path)
    root = ElementTree.parse(tree_path).getroot()
    behavior_tree = iter_behavior_tree_nodes(root)
    top_children = list(behavior_tree)
    title = top_children[0].attrib.get("name", tree_path.stem.replace("_", " ").title())
    title_font, body_font = _load_fonts()

    measure_image = Image.new("RGB", (10, 10), "white")
    measure_draw = ImageDraw.Draw(measure_image)
    layout_roots = [_build_layout_tree(child, profile) for child in top_children]
    for layout_root in layout_roots:
        _measure_layout(layout_root, measure_draw, title_font, body_font)

    title_bbox = measure_draw.textbbox((0, 0), title, font=title_font)
    title_height = (title_bbox[3] - title_bbox[1]) + TITLE_MARGIN_Y
    current_left = CANVAS_MARGIN
    current_top = CANVAS_MARGIN + title_height
    max_x = 0
    max_y = 0
    for layout_root in layout_roots:
        _place_layout(layout_root, current_left, current_top)
        root_max_x, root_max_y = _tree_bounds(layout_root)
        max_x = max(max_x, root_max_x)
        max_y = max(max_y, root_max_y)
        current_left = root_max_x + BOX_GAP_X

    image = Image.new(
        "RGB",
        (max(max_x + CANVAS_MARGIN, 1400), max(max_y + CANVAS_MARGIN, 900)),
        "white",
    )
    draw = ImageDraw.Draw(image)
    draw.text((CANVAS_MARGIN, CANVAS_MARGIN), title, font=title_font, fill="#0f172a")
    for layout_root in layout_roots:
        _draw_layout(draw, layout_root, title_font, body_font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    package_dir = Path(__file__).resolve().parents[1]
    parser.add_argument("--tree-dir", type=Path, default=package_dir / "trees")
    parser.add_argument("--config-dir", type=Path, default=package_dir / "config")
    parser.add_argument("--output-dir", type=Path, default=package_dir / "diagrams")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    has_dot = shutil.which("dot") is not None
    for tree_name, profile_name in TREE_TO_PROFILE.items():
        output_path = args.output_dir / f"{Path(tree_name).stem}_bt.png"
        if has_dot:
            render_tree(
                tree_path=args.tree_dir / tree_name,
                profile_path=args.config_dir / profile_name,
                output_path=output_path,
            )
        else:
            render_tree_with_pillow(
                tree_path=args.tree_dir / tree_name,
                profile_path=args.config_dir / profile_name,
                output_path=output_path,
            )
        print(output_path)


if __name__ == "__main__":
    main()
