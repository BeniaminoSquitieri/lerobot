#!/usr/bin/env python

"""Static architecture guards for the BT runtime packages."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BT_PYTHON = REPO_ROOT / "src/lerobot_bt_python"
BT_RUNTIME_CPP = REPO_ROOT / "src/lerobot_bt_runtime_cpp"


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = _resolve_import_from(path, node)
            if module:
                imports.add(module)
    return imports


def _resolve_import_from(path: Path, node: ast.ImportFrom) -> str:
    module = node.module or ""
    if node.level == 0:
        return module

    package_parts = path.relative_to(REPO_ROOT / "src").with_suffix("").parts[:-1]
    if node.level > len(package_parts):
        return module
    base_parts = package_parts[: len(package_parts) - node.level + 1]
    return ".".join((*base_parts, *module.split("."))).rstrip(".")


def _offending_imports(path: Path, forbidden_roots: tuple[str, ...]) -> list[str]:
    imports = _top_level_imports(path)
    return sorted(
        name
        for name in imports
        if any(name == root or name.startswith(root + ".") for root in forbidden_roots)
    )


@pytest.mark.parametrize(
    "path", _python_files(BT_PYTHON / "bt_generation"), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_bt_generation_has_no_robot_runtime_top_level_imports(path: Path) -> None:
    offenders = _offending_imports(
        path,
        (
            "lerobot.cameras",
            "lerobot.policies",
            "lerobot.robots",
            "lerobot_bt_python.executor",
            "lerobot_bt_python.perception",
            "lerobot_bt_python.server",
            "rclpy",
            "sensor_msgs",
            "torch",
        ),
    )

    assert not offenders, (
        f"{path.relative_to(REPO_ROOT)} imports runtime dependencies at module import time: {offenders}."
    )


@pytest.mark.parametrize(
    "path", _python_files(BT_PYTHON / "perception"), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_perception_does_not_import_vlm_semantics(path: Path) -> None:
    offenders = _offending_imports(path, ("lerobot_bt_python.vlm",))

    assert not offenders, (
        f"{path.relative_to(REPO_ROOT)} must not import VLM semantic verdict code: {offenders}."
    )


@pytest.mark.parametrize(
    "path", _python_files(BT_PYTHON / "vlm"), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_vlm_does_not_import_perception_or_ros_runtime(path: Path) -> None:
    offenders = _offending_imports(
        path,
        (
            "geometry_msgs",
            "lerobot_bt_python.perception",
            "rclpy",
            "sensor_msgs",
            "tf2_ros",
        ),
    )

    assert not offenders, (
        f"{path.relative_to(REPO_ROOT)} must stay free of perception/ROS runtime imports: {offenders}."
    )


def test_runtime_cpp_has_no_static_task_bt_sources() -> None:
    assert not (BT_RUNTIME_CPP / "trees").exists()
    static_task_files = sorted(
        path.relative_to(REPO_ROOT)
        for path in BT_RUNTIME_CPP.rglob("*")
        if path.is_file()
        and (path.name.endswith("_bt.yaml") or (path.suffix == ".xml" and path.name != "package.xml"))
    )

    assert static_task_files == [], (
        "Task BT XML/YAML must be generated under generated_bt/, not stored in "
        f"lerobot_bt_runtime_cpp: {static_task_files}."
    )
