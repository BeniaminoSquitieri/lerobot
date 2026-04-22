#!/usr/bin/env python

"""Utilities for resolving cub robot URDF paths consistently across controllers.

Logic:
1. Prefer a repo-local fallback URDF under `src/lerobot/motors/ergocub/urdf[s]/`.
2. If a robot-specific environment variable is set, expand `~`, resolve relative path, and use it if it exists.
3. Otherwise fall back to YARP's ResourceFinder with the configured filename.

This centralizes the behavior used by arm, bimanual, and neck controllers.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yarp

logger = logging.getLogger(__name__)
_LOCAL_URDF_DIRS = (
    Path(__file__).resolve().parent / "urdfs",
    Path(__file__).resolve().parent / "urdf",
)


def resolve_robot_urdf(
    env_vars: tuple[str, ...] = ("ROBOT_URDF_PATH",),
    fallback_filename: str = "model.urdf",
) -> str:
    """Resolve path to a cub robot URDF file.

    Args:
        env_vars: Environment variables that may point to a URDF file, in priority order.
        fallback_filename: Filename to look up via YARP ResourceFinder if env var is unset/invalid.

    Returns:
        Absolute path (string) to the URDF file.
    """
    for local_urdf_dir in _LOCAL_URDF_DIRS:
        local_candidate = (local_urdf_dir / fallback_filename).resolve()
        if local_candidate.exists():
            logger.info("Using repo-local URDF fallback: %s", local_candidate)
            return str(local_candidate)

    for env_var in env_vars:
        urdf_env = os.environ.get(env_var)
        if not urdf_env:
            continue

        candidate = Path(urdf_env).expanduser()
        if not candidate.is_absolute():
            candidate = (Path.cwd() / candidate).resolve()
        if candidate.exists():
            logger.info("Using URDF from %s: %s", env_var, candidate)
            return str(candidate)
        logger.warning(
            "%s is set to '%s' but file does not exist. Falling back to YARP ResourceFinder.",
            env_var,
            urdf_env,
        )

    # Fallback to YARP resources
    urdf_file = yarp.ResourceFinder().findFileByName(fallback_filename)
    logger.info(
        f"No valid URDF env var found. Using YARP ResourceFinder: {fallback_filename} -> {urdf_file}"
    )
    return urdf_file


def resolve_ergocub_urdf(env_var: str = "ROBOT_URDF_PATH", fallback_filename: str = "model.urdf") -> str:
    return resolve_robot_urdf((env_var,), fallback_filename)


__all__ = ["resolve_ergocub_urdf", "resolve_robot_urdf"]
