"""Environment and command snapshot helpers for experiment provenance.

These capture just enough context (git, host, ROS distro, command line) to make
a logged trial reproducible. All git access uses subprocess with shell=False and
fails soft: if git is unavailable, helpers return None instead of raising.
"""

from __future__ import annotations

import os
import shlex
import socket
import subprocess
from pathlib import Path


def _run_git(repo_root: Path, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(repo_root),
            check=False,
            capture_output=True,
            text=True,
            shell=False,
        )
    except Exception:  # noqa: BLE001 - provenance is best-effort; never raise.
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def get_git_branch(repo_root: Path) -> str | None:
    """Return the current git branch name, or None if unavailable."""

    return _run_git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"])


def get_git_commit(repo_root: Path) -> str | None:
    """Return the current git commit hash, or None if unavailable."""

    return _run_git(repo_root, ["rev-parse", "HEAD"])


def get_hostname() -> str:
    """Return the machine hostname."""

    try:
        return socket.gethostname()
    except OSError:
        return "unknown"


def get_ros_distro() -> str | None:
    """Return the active ROS distro from the environment, or None."""

    value = os.environ.get("ROS_DISTRO", "").strip()
    return value or None


def command_to_string(argv: list[str]) -> str:
    """Return a shell-safe single-line reconstruction of a command."""

    return " ".join(shlex.quote(str(part)) for part in argv)


def build_environment_snapshot(repo_root: Path, argv: list[str]) -> dict:
    """Return a provenance snapshot dict for inclusion in experiment events."""

    return {
        "git_branch": get_git_branch(repo_root),
        "git_commit": get_git_commit(repo_root),
        "hostname": get_hostname(),
        "ros_distro": get_ros_distro(),
        "command": command_to_string(argv),
    }
