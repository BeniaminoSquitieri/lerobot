"""@file bt_interface_paths.py
@brief Resolve generated ROS2 interface bindings for `lerobot_bt_interfaces`.

The editable repository ships a source-only ROS package at
`src/lerobot_bt_interfaces`, while colcon generates the importable Python
bindings under `install/.../site-packages`. Because `src/` is on `sys.path`
in editable installs, Python may see the source package first and miss the
generated `.srv` modules. This module isolates that ordering fix so
`server.py` only has to call one function.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def prepend_generated_interface_paths() -> None:
    """@brief Put generated ROS2 interface packages before source packages."""
    python_dir = f"python{sys.version_info.major}.{sys.version_info.minor}"
    repo_root = Path(__file__).resolve().parents[2]
    prefixes = [Path(path) for path in os.environ.get("COLCON_PREFIX_PATH", "").split(os.pathsep) if path]
    prefixes.extend(
        [
            repo_root / "install" / "lerobot_bt_interfaces",
            repo_root / "install",
        ]
    )

    for prefix in prefixes:
        site_packages = prefix / "lib" / python_dir / "site-packages"
        if (site_packages / "lerobot_bt_interfaces" / "srv").exists():
            site_packages_str = str(site_packages)
            if site_packages_str not in sys.path:
                sys.path.insert(0, site_packages_str)


def load_bt_services():
    """@brief Import generated LeRobot BT ROS2 service classes.

    @return `(RunNamedCommand, GetSkillVerification, ReportSkillVerification)`.
    @throws ImportError if the workspace has not been built or sourced.
    """
    prepend_generated_interface_paths()
    for module_name in list(sys.modules):
        if module_name == "lerobot_bt_interfaces" or module_name.startswith("lerobot_bt_interfaces."):
            del sys.modules[module_name]

    try:
        from lerobot_bt_interfaces.srv import GetSkillVerification, ReportSkillVerification, RunNamedCommand

        return RunNamedCommand, GetSkillVerification, ReportSkillVerification
    except ImportError as import_error:
        raise ImportError(
            "Could not import the lerobot_bt_interfaces service bindings. "
            "Source install/local_setup.bash or rebuild lerobot_bt_interfaces."
        ) from import_error


def load_query_object_pose_service():
    """@brief Import the generated `QueryObjectPose` ROS2 service class.

    @return The `QueryObjectPose` service type.
    @throws ImportError if the workspace has not been built or sourced.
    """
    prepend_generated_interface_paths()
    try:
        from lerobot_bt_interfaces.srv import QueryObjectPose

        return QueryObjectPose
    except ImportError as import_error:
        raise ImportError(
            "Could not import the lerobot_bt_interfaces QueryObjectPose binding. "
            "Source install/local_setup.bash or rebuild lerobot_bt_interfaces."
        ) from import_error
