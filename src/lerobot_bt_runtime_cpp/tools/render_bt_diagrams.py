#!/usr/bin/env python3
# Comment: executes this BT logic statement.
"""Render BehaviorTree.CPP XML files to PNG diagrams.

The renderer is intentionally small and dependency-light: it parses the XML
trees with the standard library, resolves this package's simple `bt.*` YAML
profiles, writes temporary Graphviz DOT files, and calls `dot`.
"""

# Comment: imports dependencies or symbols required by the module.
from __future__ import annotations

# Comment: imports dependencies or symbols required by the module.
import argparse
# Comment: imports dependencies or symbols required by the module.
import html
# Comment: imports dependencies or symbols required by the module.
import shutil
# Comment: imports dependencies or symbols required by the module.
import subprocess
# Comment: imports dependencies or symbols required by the module.
import tempfile
# Comment: imports dependencies or symbols required by the module.
from dataclasses import dataclass, field
# Comment: imports dependencies or symbols required by the module.
from pathlib import Path
# Comment: imports dependencies or symbols required by the module.
from xml.etree import ElementTree

# Comment: imports dependencies or symbols required by the module.
from PIL import Image, ImageDraw, ImageFont

# Comment: assigns or prepares a value used by later statements.
TREE_TO_PROFILE = {
    # Comment: executes this BT logic statement.
    "make_sandwich.xml": "make_sandwich_bt.yaml",
    # Comment: executes this BT logic statement.
    "set_breakfast_table.xml": "set_breakfast_table_bt.yaml",
    # Comment: executes this BT logic statement.
    "prepare_picnic_bag.xml": "prepare_picnic_bag_bt.yaml",
    # Comment: executes this BT logic statement.
    "items_in_drawer.xml": "items_in_drawer_bt.yaml",
    # Comment: executes this BT logic statement.
    "make_coffee.xml": "make_coffee_bt.yaml",
# Comment: closes a call, data structure, or multiline block.
}


# Comment: assigns or prepares a value used by later statements.
NODE_STYLE = {
    # Comment: executes this BT logic statement.
    "Sequence": ("#e8f1ff", "#3f6ea8"),
    # Comment: executes this BT logic statement.
    "RetryUntilSuccessful": ("#fff4d6", "#b57900"),
    # Comment: executes this BT logic statement.
    "RunRobotSkill": ("#e4f8ec", "#16834a"),
    # Comment: executes this BT logic statement.
    "OpenVLMGate": ("#f2e9ff", "#7353b6"),
    # Comment: executes this BT logic statement.
    "WaitForVLMVerdict": ("#ffe8dc", "#b85c2e"),
    # Comment: executes this BT logic statement.
    "AwaitScene": ("#f2e9ff", "#7353b6"),
    # Comment: executes this BT logic statement.
    "DoSkill": ("#e4f8ec", "#16834a"),
# Comment: closes a call, data structure, or multiline block.
}
# Comment: assigns or prepares a value used by later statements.
DEFAULT_STYLE = ("#f6f7f9", "#667085")

# Human-friendly labels that replace technical C++ node-type names in rendered diagrams.
# Comment: assigns or prepares a value used by later statements.
TAG_HUMAN_LABEL: dict[str, str] = {
    # Comment: executes this BT logic statement.
    "Sequence": "",
    # Comment: executes this BT logic statement.
    "RetryUntilSuccessful": "↻ Retry on failure",
    # Comment: executes this BT logic statement.
    "OpenVLMGate": "Scene check",
    # Comment: executes this BT logic statement.
    "WaitForVLMVerdict": "Wait for OK",
    # Comment: executes this BT logic statement.
    "RunRobotSkill": "Robot action",
    # Comment: executes this BT logic statement.
    "AwaitScene": "Check & wait",
    # Comment: executes this BT logic statement.
    "DoSkill": "Action & verify",
# Comment: closes a call, data structure, or multiline block.
}

# Human-friendly attribute names shown in diagram nodes.
# Comment: assigns or prepares a value used by later statements.
ATTR_HUMAN_LABEL: dict[str, str] = {
    # Comment: executes this BT logic statement.
    "skill_name": "action",
    # Comment: executes this BT logic statement.
    "timeout_s": "timeout",
    # Comment: executes this BT logic statement.
    "num_attempts": "max tries",
# Comment: closes a call, data structure, or multiline block.
}

# Comment: assigns or prepares a value used by later statements.
BOX_RADIUS = 12
# Comment: assigns or prepares a value used by later statements.
BOX_GAP_X = 36
# Comment: assigns or prepares a value used by later statements.
BOX_GAP_Y = 64
# Comment: assigns or prepares a value used by later statements.
TEXT_PAD_X = 18
# Comment: assigns or prepares a value used by later statements.
TEXT_PAD_Y = 12
# Comment: assigns or prepares a value used by later statements.
LINE_GAP = 6
# Comment: assigns or prepares a value used by later statements.
TITLE_MARGIN_Y = 28
# Comment: assigns or prepares a value used by later statements.
CANVAS_MARGIN = 40


# Comment: applies a decorator to the following definition.
@dataclass
class LayoutNode:
    # Comment: executes this BT logic statement.
    """In-memory tree node used by the Pillow fallback renderer."""

    # Comment: closes a call, data structure, or multiline block.
    lines: list[str]
    # Comment: executes this BT logic statement.
    fill: str
    # Comment: executes this BT logic statement.
    border: str
    # Comment: assigns or prepares a value used by later statements.
    children: list["LayoutNode"] = field(default_factory=list)
    # Comment: assigns or prepares a value used by later statements.
    width: int = 0
    # Comment: assigns or prepares a value used by later statements.
    height: int = 0
    # Comment: assigns or prepares a value used by later statements.
    subtree_width: int = 0
    # Comment: assigns or prepares a value used by later statements.
    x: int = 0
    # Comment: assigns or prepares a value used by later statements.
    y: int = 0


# Comment: defines the function or method load_bt_profile.
def load_bt_profile(profile_path: Path) -> dict[str, str]:
    # Comment: executes this BT logic statement.
    """Load the flat `bt:` parameter block used by the runtime profiles."""
    # Comment: assigns or prepares a value used by later statements.
    values: dict[str, str] = {}
    # Comment: assigns or prepares a value used by later statements.
    in_bt_block = False
    # Comment: assigns or prepares a value used by later statements.
    bt_indent = 0

    # Comment: iterates over the elements of the selected sequence.
    for line in profile_path.read_text(encoding="utf-8").splitlines():
        # Comment: assigns or prepares a value used by later statements.
        stripped = line.strip()
        # Comment: evaluates a condition and chooses the branch to run.
        if not stripped or stripped.startswith("#"):
            # Comment: skips to the next cycle of the current iteration.
            continue

        # Comment: assigns or prepares a value used by later statements.
        indent = len(line) - len(line.lstrip(" "))
        # Comment: evaluates a condition and chooses the branch to run.
        if stripped == "bt:":
            # Comment: assigns or prepares a value used by later statements.
            in_bt_block = True
            # Comment: assigns or prepares a value used by later statements.
            bt_indent = indent
            # Comment: skips to the next cycle of the current iteration.
            continue

        # Comment: evaluates a condition and chooses the branch to run.
        if in_bt_block and indent <= bt_indent:
            # Comment: breaks out of the current loop.
            break
        # Comment: evaluates a condition and chooses the branch to run.
        if not in_bt_block or ":" not in stripped:
            # Comment: skips to the next cycle of the current iteration.
            continue

        # Comment: assigns or prepares a value used by later statements.
        key, raw_value = stripped.split(":", 1)
        # Comment: assigns or prepares a value used by later statements.
        values[key] = raw_value.strip().strip('"')

    # Comment: returns the computed value to the caller.
    return values


# Comment: defines the function or method resolve_value.
def resolve_value(raw_value: str, profile: dict[str, str]) -> str:
    # Comment: executes this BT logic statement.
    """Resolve `{placeholder}` values using the BT profile."""
    # Comment: evaluates a condition and chooses the branch to run.
    if raw_value.startswith("{") and raw_value.endswith("}"):
        # Comment: returns the computed value to the caller.
        return profile.get(raw_value[1:-1], raw_value)
    # Comment: returns the computed value to the caller.
    return raw_value


# Comment: defines the function or method node_lines.
def node_lines(element: ElementTree.Element, profile: dict[str, str]) -> list[str]:
    # Comment: executes this BT logic statement.
    """Build plain-text lines shared by Graphviz and Pillow renderers.

    Technical C++ node-type names and ROS-specific details are replaced with
    human-friendly labels so that every diagram reads like a natural task
    description.
    """
    # Comment: assigns or prepares a value used by later statements.
    rows = [element.attrib.get("name", element.tag)]

    # Second line: human-friendly node-type label (hidden for Sequence).
    # Comment: assigns or prepares a value used by later statements.
    human_tag = TAG_HUMAN_LABEL.get(element.tag, element.tag)
    # Comment: evaluates a condition and chooses the branch to run.
    if human_tag:
        # Comment: closes a call, data structure, or multiline block.
        rows.append(human_tag)

    # Show the action/scene name (not internal gate/checkpoint keys).
    # Comment: iterates over the elements of the selected sequence.
    for port in ("skill_name", "scene_name"):
        # Comment: evaluates a condition and chooses the branch to run.
        if port in element.attrib:
            # Comment: assigns or prepares a value used by later statements.
            value = resolve_value(element.attrib[port], profile)
            # Comment: closes a call, data structure, or multiline block.
            rows.append(f"action: {value}")

    # Timeout – only when it carries information.
    # Comment: evaluates a condition and chooses the branch to run.
    if "timeout_s" in element.attrib:
        # Comment: assigns or prepares a value used by later statements.
        value = resolve_value(element.attrib["timeout_s"], profile)
        # Comment: closes a call, data structure, or multiline block.
        rows.append(f"timeout: {value}s")

    # Max attempts – skip the "-1" (infinite) placeholder.
    # Comment: evaluates a condition and chooses the branch to run.
    if "num_attempts" in element.attrib:
        # Comment: assigns or prepares a value used by later statements.
        value = resolve_value(element.attrib["num_attempts"], profile)
        # Comment: evaluates a condition and chooses the branch to run.
        if value != "-1":
            # Comment: closes a call, data structure, or multiline block.
            rows.append(f"max tries: {value}")

    # Human-friendly descriptions instead of ROS topic internals.
    # Comment: evaluates a condition and chooses the branch to run.
    if element.tag == "OpenVLMGate":
        # Comment: closes a call, data structure, or multiline block.
        rows.append("→ asks for scene verification")
    # Comment: evaluates a condition and chooses the branch to run.
    if element.tag == "WaitForVLMVerdict":
        # Comment: closes a call, data structure, or multiline block.
        rows.append("→ waits for confirmation")

    # Comment: returns the computed value to the caller.
    return rows


# Comment: defines the function or method node_label.
def node_label(element: ElementTree.Element, profile: dict[str, str]) -> str:
    # Comment: executes this BT logic statement.
    """Build a compact HTML label for a Graphviz node."""
    # Comment: assigns or prepares a value used by later statements.
    escaped_rows = []
    # Comment: iterates over the elements of the selected sequence.
    for index, row in enumerate(node_lines(element, profile)):
        # Comment: evaluates a condition and chooses the branch to run.
        if index == 0:
            # Comment: closes a call, data structure, or multiline block.
            escaped_rows.append(f"<B>{html.escape(row)}</B>")
        # Comment: handles the fallback branch when previous conditions do not match.
        else:
            # Comment: assigns or prepares a value used by later statements.
            escaped_rows.append(f"<FONT POINT-SIZE='10'>{html.escape(row)}</FONT>")

    # Comment: returns the computed value to the caller.
    return "<" + "<BR/>".join(escaped_rows) + ">"


# Comment: defines the function or method _load_fonts.
def _load_fonts() -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    # Comment: executes this BT logic statement.
    """Load readable fonts for the Pillow fallback renderer."""
    # Comment: opens a protected block to catch possible errors.
    try:
        # Comment: returns the computed value to the caller.
        return (
            # Comment: executes this BT logic statement.
            ImageFont.truetype("DejaVuSans-Bold.ttf", 18),
            # Comment: executes this BT logic statement.
            ImageFont.truetype("DejaVuSans.ttf", 14),
        # Comment: closes a call, data structure, or multiline block.
        )
    # Comment: handles a specific exception raised by the protected block.
    except OSError:
        # Comment: assigns or prepares a value used by later statements.
        default_font = ImageFont.load_default()
        # Comment: returns the computed value to the caller.
        return default_font, default_font


# Comment: defines the function or method _measure_multiline.
def _measure_multiline(
    # Comment: executes this BT logic statement.
    draw: ImageDraw.ImageDraw,
    # Comment: executes this BT logic statement.
    lines: list[str],
    # Comment: executes this BT logic statement.
    title_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    # Comment: executes this BT logic statement.
    body_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
# Comment: executes this BT logic statement.
) -> tuple[int, int]:
    # Comment: executes this BT logic statement.
    """Measure one node box for the Pillow fallback renderer."""
    # Comment: assigns or prepares a value used by later statements.
    widths: list[int] = []
    # Comment: assigns or prepares a value used by later statements.
    heights: list[int] = []
    # Comment: iterates over the elements of the selected sequence.
    for index, line in enumerate(lines):
        # Comment: assigns or prepares a value used by later statements.
        font = title_font if index == 0 else body_font
        # Comment: assigns or prepares a value used by later statements.
        bbox = draw.textbbox((0, 0), line, font=font)
        # Comment: closes a call, data structure, or multiline block.
        widths.append(bbox[2] - bbox[0])
        # Comment: closes a call, data structure, or multiline block.
        heights.append(bbox[3] - bbox[1])
    # Comment: assigns or prepares a value used by later statements.
    width = max(widths, default=0) + (2 * TEXT_PAD_X)
    # Comment: assigns or prepares a value used by later statements.
    text_height = sum(heights) + (LINE_GAP * max(0, len(lines) - 1))
    # Comment: assigns or prepares a value used by later statements.
    height = text_height + (2 * TEXT_PAD_Y)
    # Comment: returns the computed value to the caller.
    return width, height


# Comment: defines the function or method _build_layout_tree.
def _build_layout_tree(element: ElementTree.Element, profile: dict[str, str]) -> LayoutNode:
    # Comment: executes this BT logic statement.
    """Convert an XML node into a drawable layout tree."""
    # Comment: assigns or prepares a value used by later statements.
    fill, border = NODE_STYLE.get(element.tag, DEFAULT_STYLE)
    # Comment: returns the computed value to the caller.
    return LayoutNode(
        # Comment: assigns or prepares a value used by later statements.
        lines=node_lines(element, profile),
        # Comment: assigns or prepares a value used by later statements.
        fill=fill,
        # Comment: assigns or prepares a value used by later statements.
        border=border,
        # Comment: assigns or prepares a value used by later statements.
        children=[_build_layout_tree(child, profile) for child in list(element)],
    # Comment: closes a call, data structure, or multiline block.
    )


# Comment: defines the function or method _measure_layout.
def _measure_layout(
    # Comment: executes this BT logic statement.
    node: LayoutNode,
    # Comment: executes this BT logic statement.
    draw: ImageDraw.ImageDraw,
    # Comment: executes this BT logic statement.
    title_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    # Comment: executes this BT logic statement.
    body_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
# Comment: executes this BT logic statement.
) -> None:
    # Comment: executes this BT logic statement.
    """Populate node dimensions and subtree widths recursively."""
    # Comment: assigns or prepares a value used by later statements.
    node.width, node.height = _measure_multiline(draw, node.lines, title_font, body_font)
    # Comment: iterates over the elements of the selected sequence.
    for child in node.children:
        # Comment: closes a call, data structure, or multiline block.
        _measure_layout(child, draw, title_font, body_font)
    # Comment: evaluates a condition and chooses the branch to run.
    if not node.children:
        # Comment: assigns or prepares a value used by later statements.
        node.subtree_width = node.width
        # Comment: returns the computed value to the caller.
        return

    # Comment: assigns or prepares a value used by later statements.
    children_width = sum(child.subtree_width for child in node.children)
    # Comment: assigns or prepares a value used by later statements.
    children_width += BOX_GAP_X * max(0, len(node.children) - 1)
    # Comment: assigns or prepares a value used by later statements.
    node.subtree_width = max(node.width, children_width)


# Comment: defines the function or method _place_layout.
def _place_layout(node: LayoutNode, left: int, top: int) -> None:
    # Comment: executes this BT logic statement.
    """Assign top-left coordinates recursively."""
    # Comment: assigns or prepares a value used by later statements.
    node.x = left + (node.subtree_width - node.width) // 2
    # Comment: assigns or prepares a value used by later statements.
    node.y = top
    # Comment: evaluates a condition and chooses the branch to run.
    if not node.children:
        # Comment: returns the computed value to the caller.
        return

    # Comment: assigns or prepares a value used by later statements.
    total_children_width = sum(child.subtree_width for child in node.children)
    # Comment: assigns or prepares a value used by later statements.
    total_children_width += BOX_GAP_X * max(0, len(node.children) - 1)
    # Comment: assigns or prepares a value used by later statements.
    child_left = left + (node.subtree_width - total_children_width) // 2
    # Comment: assigns or prepares a value used by later statements.
    child_top = top + node.height + BOX_GAP_Y
    # Comment: iterates over the elements of the selected sequence.
    for child in node.children:
        # Comment: closes a call, data structure, or multiline block.
        _place_layout(child, child_left, child_top)
        # Comment: assigns or prepares a value used by later statements.
        child_left += child.subtree_width + BOX_GAP_X


# Comment: defines the function or method _tree_bounds.
def _tree_bounds(node: LayoutNode) -> tuple[int, int]:
    # Comment: executes this BT logic statement.
    """Return the maximum x/y extents of one layout tree."""
    # Comment: assigns or prepares a value used by later statements.
    max_x = node.x + node.width
    # Comment: assigns or prepares a value used by later statements.
    max_y = node.y + node.height
    # Comment: iterates over the elements of the selected sequence.
    for child in node.children:
        # Comment: assigns or prepares a value used by later statements.
        child_max_x, child_max_y = _tree_bounds(child)
        # Comment: assigns or prepares a value used by later statements.
        max_x = max(max_x, child_max_x)
        # Comment: assigns or prepares a value used by later statements.
        max_y = max(max_y, child_max_y)
    # Comment: returns the computed value to the caller.
    return max_x, max_y


# Comment: defines the function or method _draw_layout.
def _draw_layout(
    # Comment: executes this BT logic statement.
    draw: ImageDraw.ImageDraw,
    # Comment: executes this BT logic statement.
    node: LayoutNode,
    # Comment: executes this BT logic statement.
    title_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    # Comment: executes this BT logic statement.
    body_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
# Comment: executes this BT logic statement.
) -> None:
    # Comment: executes this BT logic statement.
    """Draw the laid-out tree nodes and edges."""
    # Comment: assigns or prepares a value used by later statements.
    parent_mid_x = node.x + (node.width // 2)
    # Comment: assigns or prepares a value used by later statements.
    parent_bottom_y = node.y + node.height
    # Comment: iterates over the elements of the selected sequence.
    for child in node.children:
        # Comment: assigns or prepares a value used by later statements.
        child_mid_x = child.x + (child.width // 2)
        # Comment: assigns or prepares a value used by later statements.
        child_top_y = child.y
        # Comment: executes this BT logic statement.
        draw.line(
            # Comment: executes this BT logic statement.
            [(parent_mid_x, parent_bottom_y), (parent_mid_x, parent_bottom_y + 18)],
            # Comment: assigns or prepares a value used by later statements.
            fill="#667085",
            # Comment: assigns or prepares a value used by later statements.
            width=3,
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: executes this BT logic statement.
        draw.line(
            # Comment: executes this BT logic statement.
            [(parent_mid_x, parent_bottom_y + 18), (child_mid_x, child_top_y - 18)],
            # Comment: assigns or prepares a value used by later statements.
            fill="#667085",
            # Comment: assigns or prepares a value used by later statements.
            width=3,
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: executes this BT logic statement.
        draw.line(
            # Comment: executes this BT logic statement.
            [(child_mid_x, child_top_y - 18), (child_mid_x, child_top_y)],
            # Comment: assigns or prepares a value used by later statements.
            fill="#667085",
            # Comment: assigns or prepares a value used by later statements.
            width=3,
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: closes a call, data structure, or multiline block.
        _draw_layout(draw, child, title_font, body_font)

    # Comment: executes this BT logic statement.
    draw.rounded_rectangle(
        # Comment: executes this BT logic statement.
        [node.x, node.y, node.x + node.width, node.y + node.height],
        # Comment: assigns or prepares a value used by later statements.
        radius=BOX_RADIUS,
        # Comment: assigns or prepares a value used by later statements.
        fill=node.fill,
        # Comment: assigns or prepares a value used by later statements.
        outline=node.border,
        # Comment: assigns or prepares a value used by later statements.
        width=3,
    # Comment: closes a call, data structure, or multiline block.
    )

    # Comment: assigns or prepares a value used by later statements.
    text_y = node.y + TEXT_PAD_Y
    # Comment: iterates over the elements of the selected sequence.
    for index, line in enumerate(node.lines):
        # Comment: assigns or prepares a value used by later statements.
        font = title_font if index == 0 else body_font
        # Comment: assigns or prepares a value used by later statements.
        fill = "#0f172a" if index == 0 else "#334155"
        # Comment: assigns or prepares a value used by later statements.
        draw.text((node.x + TEXT_PAD_X, text_y), line, font=font, fill=fill)
        # Comment: assigns or prepares a value used by later statements.
        bbox = draw.textbbox((node.x + TEXT_PAD_X, text_y), line, font=font)
        # Comment: assigns or prepares a value used by later statements.
        text_y = bbox[3] + LINE_GAP


# Comment: defines the function or method iter_behavior_tree_nodes.
def iter_behavior_tree_nodes(root: ElementTree.Element) -> ElementTree.Element:
    # Comment: executes this BT logic statement.
    """Return the main BehaviorTree node, failing clearly if it is missing."""
    # Comment: assigns or prepares a value used by later statements.
    behavior_tree = root.find("BehaviorTree")
    # Comment: evaluates a condition and chooses the branch to run.
    if behavior_tree is None:
        # Comment: raises an explicit error for the caller.
        raise ValueError("XML file does not contain a BehaviorTree element.")
    # Comment: returns the computed value to the caller.
    return behavior_tree


# Comment: defines the function or method build_dot.
def build_dot(tree_path: Path, profile_path: Path) -> str:
    # Comment: executes this BT logic statement.
    """Convert one XML tree into a DOT graph."""
    # Comment: assigns or prepares a value used by later statements.
    profile = load_bt_profile(profile_path)
    # Comment: assigns or prepares a value used by later statements.
    root = ElementTree.parse(tree_path).getroot()
    # Comment: assigns or prepares a value used by later statements.
    behavior_tree = iter_behavior_tree_nodes(root)
    # Comment: assigns or prepares a value used by later statements.
    top_children = list(behavior_tree)
    # Comment: evaluates a condition and chooses the branch to run.
    if top_children:
        # Comment: assigns or prepares a value used by later statements.
        graph_title = top_children[0].attrib.get(
            # Comment: executes this BT logic statement.
            "name",
            # Comment: executes this BT logic statement.
            tree_path.stem.replace("_", " ").title(),
        # Comment: closes a call, data structure, or multiline block.
        )
    # Comment: handles the fallback branch when previous conditions do not match.
    else:
        # Comment: assigns or prepares a value used by later statements.
        graph_title = tree_path.stem.replace("_", " ").title()
    # Comment: assigns or prepares a value used by later statements.
    graph_lines = [
        # Comment: executes this BT logic statement.
        "digraph BehaviorTree {",
        # Comment: assigns or prepares a value used by later statements.
        "  graph [rankdir=TB, bgcolor=\"white\", pad=\"0.3\", nodesep=\"0.45\", ranksep=\"0.55\"];",
        # Comment: assigns or prepares a value used by later statements.
        "  node [shape=box, style=\"rounded,filled\", fontname=\"DejaVu Sans\", fontsize=11, margin=\"0.10,0.08\"];",
        # Comment: assigns or prepares a value used by later statements.
        "  edge [color=\"#667085\", arrowsize=0.7];",
        # Comment: assigns or prepares a value used by later statements.
        "  labelloc=\"t\";",
        # Comment: assigns or prepares a value used by later statements.
        f"  label=<{html.escape(graph_title)}>;",
    # Comment: closes a call, data structure, or multiline block.
    ]
    # Comment: assigns or prepares a value used by later statements.
    counter = 0

    # Comment: defines the function or method add_node.
    def add_node(element: ElementTree.Element, parent_id: str | None = None) -> None:
        # Comment: executes this BT logic statement.
        nonlocal counter
        # Comment: assigns or prepares a value used by later statements.
        node_id = f"n{counter}"
        # Comment: assigns or prepares a value used by later statements.
        counter += 1
        # Comment: assigns or prepares a value used by later statements.
        fill, border = NODE_STYLE.get(element.tag, DEFAULT_STYLE)
        # Comment: executes this BT logic statement.
        graph_lines.append(
            # Comment: assigns or prepares a value used by later statements.
            f"  {node_id} [label={node_label(element, profile)}, fillcolor=\"{fill}\", color=\"{border}\"];"
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: evaluates a condition and chooses the branch to run.
        if parent_id is not None:
            # Comment: closes a call, data structure, or multiline block.
            graph_lines.append(f"  {parent_id} -> {node_id};")
        # Comment: iterates over the elements of the selected sequence.
        for child in list(element):
            # Comment: closes a call, data structure, or multiline block.
            add_node(child, node_id)

    # Comment: iterates over the elements of the selected sequence.
    for top_child in top_children:
        # Comment: closes a call, data structure, or multiline block.
        add_node(top_child)

    # Comment: closes a call, data structure, or multiline block.
    graph_lines.append("}")
    # Comment: returns the computed value to the caller.
    return "\n".join(graph_lines) + "\n"


# Comment: defines the function or method render_tree.
def render_tree(tree_path: Path, profile_path: Path, output_path: Path) -> None:
    # Comment: executes this BT logic statement.
    """Render one tree to PNG through Graphviz."""
    # Comment: assigns or prepares a value used by later statements.
    dot_source = build_dot(tree_path, profile_path)
    # Comment: opens a managed context and guarantees its cleanup.
    with tempfile.NamedTemporaryFile("w", suffix=".dot", encoding="utf-8", delete=False) as dot_file:
        # Comment: closes a call, data structure, or multiline block.
        dot_file.write(dot_source)
        # Comment: assigns or prepares a value used by later statements.
        dot_path = Path(dot_file.name)
    # Comment: opens a protected block to catch possible errors.
    try:
        # Comment: executes this BT logic statement.
        subprocess.run(
            # Comment: executes this BT logic statement.
            ["dot", "-Tpng", str(dot_path), "-o", str(output_path)],
            # Comment: assigns or prepares a value used by later statements.
            check=True,
        # Comment: closes a call, data structure, or multiline block.
        )
    # Comment: always runs the final cleanup for the protected block.
    finally:
        # Comment: assigns or prepares a value used by later statements.
        dot_path.unlink(missing_ok=True)


# Comment: defines the function or method render_tree_with_pillow.
def render_tree_with_pillow(tree_path: Path, profile_path: Path, output_path: Path) -> None:
    # Comment: executes this BT logic statement.
    """Render one tree to PNG without Graphviz, using Pillow only."""
    # Comment: assigns or prepares a value used by later statements.
    profile = load_bt_profile(profile_path)
    # Comment: assigns or prepares a value used by later statements.
    root = ElementTree.parse(tree_path).getroot()
    # Comment: assigns or prepares a value used by later statements.
    behavior_tree = iter_behavior_tree_nodes(root)
    # Comment: assigns or prepares a value used by later statements.
    top_children = list(behavior_tree)
    # Comment: assigns or prepares a value used by later statements.
    title = top_children[0].attrib.get("name", tree_path.stem.replace("_", " ").title())
    # Comment: assigns or prepares a value used by later statements.
    title_font, body_font = _load_fonts()

    # Comment: assigns or prepares a value used by later statements.
    measure_image = Image.new("RGB", (10, 10), "white")
    # Comment: assigns or prepares a value used by later statements.
    measure_draw = ImageDraw.Draw(measure_image)
    # Comment: assigns or prepares a value used by later statements.
    layout_roots = [_build_layout_tree(child, profile) for child in top_children]
    # Comment: iterates over the elements of the selected sequence.
    for layout_root in layout_roots:
        # Comment: closes a call, data structure, or multiline block.
        _measure_layout(layout_root, measure_draw, title_font, body_font)

    # Comment: assigns or prepares a value used by later statements.
    title_bbox = measure_draw.textbbox((0, 0), title, font=title_font)
    # Comment: assigns or prepares a value used by later statements.
    title_height = (title_bbox[3] - title_bbox[1]) + TITLE_MARGIN_Y
    # Comment: assigns or prepares a value used by later statements.
    current_left = CANVAS_MARGIN
    # Comment: assigns or prepares a value used by later statements.
    current_top = CANVAS_MARGIN + title_height
    # Comment: assigns or prepares a value used by later statements.
    max_x = 0
    # Comment: assigns or prepares a value used by later statements.
    max_y = 0
    # Comment: iterates over the elements of the selected sequence.
    for layout_root in layout_roots:
        # Comment: closes a call, data structure, or multiline block.
        _place_layout(layout_root, current_left, current_top)
        # Comment: assigns or prepares a value used by later statements.
        root_max_x, root_max_y = _tree_bounds(layout_root)
        # Comment: assigns or prepares a value used by later statements.
        max_x = max(max_x, root_max_x)
        # Comment: assigns or prepares a value used by later statements.
        max_y = max(max_y, root_max_y)
        # Comment: assigns or prepares a value used by later statements.
        current_left = root_max_x + BOX_GAP_X

    # Comment: assigns or prepares a value used by later statements.
    image = Image.new(
        # Comment: executes this BT logic statement.
        "RGB",
        # Comment: executes this BT logic statement.
        (max(max_x + CANVAS_MARGIN, 1400), max(max_y + CANVAS_MARGIN, 900)),
        # Comment: executes this BT logic statement.
        "white",
    # Comment: closes a call, data structure, or multiline block.
    )
    # Comment: assigns or prepares a value used by later statements.
    draw = ImageDraw.Draw(image)
    # Comment: assigns or prepares a value used by later statements.
    draw.text((CANVAS_MARGIN, CANVAS_MARGIN), title, font=title_font, fill="#0f172a")
    # Comment: iterates over the elements of the selected sequence.
    for layout_root in layout_roots:
        # Comment: closes a call, data structure, or multiline block.
        _draw_layout(draw, layout_root, title_font, body_font)
    # Comment: assigns or prepares a value used by later statements.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Comment: assigns or prepares a value used by later statements.
    image.save(output_path, format="PNG")


# Comment: defines the function or method parse_args.
def parse_args() -> argparse.Namespace:
    # Comment: assigns or prepares a value used by later statements.
    parser = argparse.ArgumentParser(description=__doc__)
    # Comment: assigns or prepares a value used by later statements.
    package_dir = Path(__file__).resolve().parents[1]
    # Comment: assigns or prepares a value used by later statements.
    parser.add_argument("--tree-dir", type=Path, default=package_dir / "trees")
    # Comment: assigns or prepares a value used by later statements.
    parser.add_argument("--config-dir", type=Path, default=package_dir / "config")
    # Comment: assigns or prepares a value used by later statements.
    parser.add_argument("--output-dir", type=Path, default=package_dir / "diagrams")
    # Comment: returns the computed value to the caller.
    return parser.parse_args()


# Comment: defines the function or method main.
def main() -> None:
    # Comment: assigns or prepares a value used by later statements.
    args = parse_args()
    # Comment: assigns or prepares a value used by later statements.
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # Comment: assigns or prepares a value used by later statements.
    has_dot = shutil.which("dot") is not None
    # Comment: iterates over the elements of the selected sequence.
    for tree_name, profile_name in TREE_TO_PROFILE.items():
        # Comment: assigns or prepares a value used by later statements.
        output_path = args.output_dir / f"{Path(tree_name).stem}_bt.png"
        # Comment: evaluates a condition and chooses the branch to run.
        if has_dot:
            # Comment: executes this BT logic statement.
            render_tree(
                # Comment: assigns or prepares a value used by later statements.
                tree_path=args.tree_dir / tree_name,
                # Comment: assigns or prepares a value used by later statements.
                profile_path=args.config_dir / profile_name,
                # Comment: assigns or prepares a value used by later statements.
                output_path=output_path,
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: handles the fallback branch when previous conditions do not match.
        else:
            # Comment: executes this BT logic statement.
            render_tree_with_pillow(
                # Comment: assigns or prepares a value used by later statements.
                tree_path=args.tree_dir / tree_name,
                # Comment: assigns or prepares a value used by later statements.
                profile_path=args.config_dir / profile_name,
                # Comment: assigns or prepares a value used by later statements.
                output_path=output_path,
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: closes a call, data structure, or multiline block.
        print(output_path)


# Comment: evaluates a condition and chooses the branch to run.
if __name__ == "__main__":
    # Comment: closes a call, data structure, or multiline block.
    main()
