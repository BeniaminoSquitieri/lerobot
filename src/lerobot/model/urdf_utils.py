#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import hashlib
import logging
import os
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

_RESOURCE_ATTRS = ("filename", "url")
_PACKAGE_URI_PREFIX = "package://"
_PACKAGE_PREFIX_ENV_VARS = ("AMENT_PREFIX_PATH", "COLCON_PREFIX_PATH", "CMAKE_PREFIX_PATH")
_PACKAGE_SEARCH_ENV_VARS = (
    "ROS_PACKAGE_PATH",
    "YARP_DATA_DIRS",
    "GZ_SIM_RESOURCE_PATH",
    "IGN_GAZEBO_RESOURCE_PATH",
    "GAZEBO_RESOURCE_PATH",
)
_PLACO_URDF_DIR = TemporaryDirectory(prefix="lerobot-placo-urdf-")


def prepare_urdf_for_placo(urdf_path: str) -> str:
    """Rewrite URDF resource references to absolute paths when placo cannot resolve them."""

    resolved_urdf_path = Path(urdf_path).expanduser().resolve()
    return _prepare_urdf_for_placo_cached(str(resolved_urdf_path), resolved_urdf_path.stat().st_mtime_ns)


@lru_cache(maxsize=None)
def _prepare_urdf_for_placo_cached(resolved_urdf_path_str: str, mtime_ns: int) -> str:
    del mtime_ns

    resolved_urdf_path = Path(resolved_urdf_path_str)
    tree = ET.parse(resolved_urdf_path)
    root = tree.getroot()
    modified = False

    for element in root.iter():
        for attr_name in _RESOURCE_ATTRS:
            resource_path = element.attrib.get(attr_name)
            if not resource_path:
                continue

            resolved_resource_path = _resolve_resource_reference(resource_path, resolved_urdf_path)
            if resolved_resource_path is None or resolved_resource_path == resource_path:
                continue

            element.attrib[attr_name] = resolved_resource_path
            modified = True

    if not modified:
        return resolved_urdf_path_str

    fingerprint = hashlib.sha1(resolved_urdf_path_str.encode("utf-8")).hexdigest()[:12]
    prepared_urdf_path = Path(_PLACO_URDF_DIR.name) / f"{resolved_urdf_path.stem}-{fingerprint}.urdf"
    tree.write(prepared_urdf_path, encoding="utf-8", xml_declaration=True)
    logger.info("Prepared temporary URDF for placo: %s", prepared_urdf_path)
    return str(prepared_urdf_path)


def _resolve_resource_reference(resource_path: str, urdf_path: Path) -> str | None:
    if resource_path.startswith(_PACKAGE_URI_PREFIX):
        return _resolve_package_resource(resource_path, urdf_path)

    if _has_uri_scheme(resource_path):
        return None

    expanded_resource_path = Path(resource_path).expanduser()
    if expanded_resource_path.is_absolute():
        return None

    return str((urdf_path.parent / expanded_resource_path).resolve())


def _resolve_package_resource(resource_path: str, urdf_path: Path) -> str | None:
    package_reference = resource_path.removeprefix(_PACKAGE_URI_PREFIX)
    package_name, separator, package_relative_path = package_reference.partition("/")
    if not separator or not package_name or not package_relative_path:
        logger.warning("Unsupported URDF package resource '%s' referenced by %s", resource_path, urdf_path)
        return None

    package_root = _find_package_root(package_name, urdf_path)
    if package_root is None:
        logger.warning(
            "Could not resolve package '%s' for URDF resource '%s' referenced by %s",
            package_name,
            resource_path,
            urdf_path,
        )
        return None

    resolved_resource_path = (package_root / package_relative_path).resolve()
    if not resolved_resource_path.exists():
        logger.warning("Resolved URDF resource '%s' to '%s', but the file does not exist", resource_path, resolved_resource_path)

    return str(resolved_resource_path)


def _find_package_root(package_name: str, urdf_path: Path) -> Path | None:
    for ancestor in urdf_path.parents:
        if ancestor.name == package_name and ancestor.is_dir():
            return ancestor

    share_root = next((ancestor for ancestor in urdf_path.parents if ancestor.name == "share"), None)
    if share_root is not None:
        share_candidate = share_root / package_name
        if share_candidate.is_dir():
            return share_candidate

    for env_var in _PACKAGE_PREFIX_ENV_VARS:
        for search_root in _iter_env_paths(env_var):
            for candidate in (search_root / "share" / package_name, search_root / package_name):
                if candidate.is_dir():
                    return candidate

    for env_var in _PACKAGE_SEARCH_ENV_VARS:
        for search_root in _iter_env_paths(env_var):
            for candidate in _candidate_package_paths(search_root, package_name):
                if candidate.is_dir():
                    return candidate

    return None


def _iter_env_paths(env_var: str) -> tuple[Path, ...]:
    env_value = os.environ.get(env_var, "")
    if not env_value:
        return ()

    paths: list[Path] = []
    for entry in env_value.split(os.pathsep):
        if not entry:
            continue
        candidate = Path(entry).expanduser()
        if candidate.exists():
            paths.append(candidate)
    return tuple(paths)


def _candidate_package_paths(search_root: Path, package_name: str) -> tuple[Path, ...]:
    candidates: list[Path] = []
    if search_root.name == package_name:
        candidates.append(search_root)
    else:
        candidates.extend((search_root / package_name, search_root / "share" / package_name))
    return tuple(candidates)


def _has_uri_scheme(resource_path: str) -> bool:
    scheme, separator, _ = resource_path.partition("://")
    return bool(separator) and bool(scheme)
