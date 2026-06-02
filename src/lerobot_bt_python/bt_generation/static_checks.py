"""Pre-run consistency checks for generated BT XML and parameter YAML.

This module runs on the real robot generation path after rendering and before
the runner loads artifacts. It compares blackboard keys referenced in XML with
the generated bt.* parameters in YAML and reports mismatches early. Main inputs
are rendered XML and YAML text; main output is a list of static errors. Do not
skip this boundary when changing renderer output or runner parameter names.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml

BLACKBOARD_KEY_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def extract_blackboard_keys_from_xml(xml_text: str) -> set[str]:
    """Return every BehaviorTree.CPP blackboard key reference in XML attributes."""

    root = ET.fromstring(xml_text)
    keys: set[str] = set()
    for element in root.iter():
        for value in element.attrib.values():
            keys.update(BLACKBOARD_KEY_RE.findall(value))
        if element.text:
            keys.update(BLACKBOARD_KEY_RE.findall(element.text))
    return keys


def extract_bt_params_from_yaml(yaml_text: str) -> set[str]:
    """Return generated `bt.*` parameter keys from a ROS2 params YAML string."""

    data = yaml.safe_load(yaml_text)
    if not isinstance(data, dict):
        raise ValueError("YAML must contain a mapping.")

    try:
        bt_params = data["lerobot_bt_runner"]["ros__parameters"]["bt"]
    except KeyError as exc:
        raise ValueError("YAML must contain lerobot_bt_runner.ros__parameters.bt.") from exc

    if not isinstance(bt_params, dict):
        raise ValueError("YAML lerobot_bt_runner.ros__parameters.bt must be a mapping.")
    return {str(key) for key in bt_params}


def validate_xml_yaml_blackboard_text(xml_text: str, yaml_text: str) -> list[str]:
    """Return static XML/YAML blackboard consistency errors."""

    errors: list[str] = []
    try:
        xml_keys = extract_blackboard_keys_from_xml(xml_text)
    except ET.ParseError as exc:
        return [f"Generated XML is not parseable: {exc}."]

    try:
        yaml_keys = extract_bt_params_from_yaml(yaml_text)
    except ValueError as exc:
        return [str(exc)]

    missing = sorted(xml_keys - yaml_keys)
    if missing:
        errors.append(f"Generated XML references missing BT YAML key(s): {missing}.")
    return errors


def validate_xml_yaml_blackboard_keys(xml_path: Path, yaml_path: Path) -> list[str]:
    """Return static XML/YAML blackboard consistency errors for generated files."""

    return validate_xml_yaml_blackboard_text(
        Path(xml_path).read_text(encoding="utf-8"),
        Path(yaml_path).read_text(encoding="utf-8"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate generated BT XML/YAML blackboard keys.")
    parser.add_argument("--xml", required=True, type=Path, help="Generated BehaviorTree.CPP XML path.")
    parser.add_argument("--yaml", required=True, type=Path, help="Generated ROS2 BT params YAML path.")
    args = parser.parse_args(argv)

    errors = validate_xml_yaml_blackboard_keys(args.xml, args.yaml)
    if errors:
        print("BT static check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"BT static check OK: {args.xml} <-> {args.yaml}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
