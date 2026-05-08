"""@file groot2_monitor.py
@brief Launch Groot2 with sandwich BT monitor defaults.

Groot2 stores its connection fields in a Qt INI file. This entry point updates
that file before starting Groot2 so the real-time monitor opens on the BT.CPP
default endpoint used by `BT::Groot2Publisher`: localhost:1667.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


DEFAULT_HOST = "localhost"
DEFAULT_PORT = 1667
DEFAULT_APPIMAGE_NAME = "Groot2-v1.9.0-x86_64.AppImage"

QT_MONITOR_KEY = "APP%3A%3AMode"
QT_HOST_KEY = "ZMQConnectionWidget%3A%3Ahost"
QT_PORT_KEY = "ZMQConnectionWidget%3A%3Aport"


def _default_config_path() -> Path:
    """Return the Groot2 Qt settings path used on Linux."""
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / "AurynRobotics" / "Groot2.ini"


def _set_qt_key(lines: list[str], key: str, value: str) -> list[str]:
    """Set a single key in the `[General]` section without parsing Qt byte arrays."""
    key_prefix = f"{key}="
    for idx, line in enumerate(lines):
        if line.startswith(key_prefix):
            lines[idx] = f"{key}={value}\n"
            return lines

    try:
        general_idx = next(idx for idx, line in enumerate(lines) if line.strip() == "[General]")
    except StopIteration:
        if lines and lines[-1].strip():
            lines.append("\n")
        lines.extend(["[General]\n", f"{key}={value}\n"])
        return lines

    insert_idx = general_idx + 1
    lines.insert(insert_idx, f"{key}={value}\n")
    return lines


def configure_groot2(config_path: Path, *, host: str, port: int) -> None:
    """Write monitor defaults to Groot2's Qt settings file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        lines = config_path.read_text(encoding="utf-8", errors="surrogateescape").splitlines(keepends=True)
    else:
        lines = ["[General]\n"]

    lines = _set_qt_key(lines, QT_MONITOR_KEY, "Monitor")
    lines = _set_qt_key(lines, QT_HOST_KEY, host)
    lines = _set_qt_key(lines, QT_PORT_KEY, str(port))
    config_path.write_text("".join(lines), encoding="utf-8", errors="surrogateescape")


def _candidate_apps(explicit_app: str | None) -> list[Path]:
    """Return possible Groot2 executables in priority order."""
    candidates: list[Path] = []
    if explicit_app:
        candidates.append(Path(explicit_app).expanduser())
    env_app = os.environ.get("GROOT2_APP")
    if env_app:
        candidates.append(Path(env_app).expanduser())

    for command in ("Groot2", "Groot"):
        resolved = shutil.which(command)
        if resolved:
            candidates.append(Path(resolved))

    applications = Path.home() / "Applications"
    candidates.append(applications / DEFAULT_APPIMAGE_NAME)
    candidates.extend(sorted(applications.glob("Groot2*.AppImage"), reverse=True))
    candidates.extend(sorted(applications.glob("Groot*.AppImage"), reverse=True))

    deduped: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved_candidate = candidate.resolve()
        except OSError:
            resolved_candidate = candidate
        if resolved_candidate not in seen:
            deduped.append(candidate)
            seen.add(resolved_candidate)
    return deduped


def find_groot2_app(explicit_app: str | None) -> Path | None:
    """Find the Groot2 executable or AppImage."""
    for candidate in _candidate_apps(explicit_app):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Open Groot2 monitor on the sandwich BT default port.")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Groot2 monitor host (default: {DEFAULT_HOST}).")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Groot2 monitor port (default: {DEFAULT_PORT}).")
    parser.add_argument("--app", help="Path to the Groot2 executable/AppImage.")
    parser.add_argument(
        "--config",
        type=Path,
        default=_default_config_path(),
        help="Path to Groot2.ini.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write the Groot2 defaults and print the command without launching the GUI.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Console entry point for `lerobot-bt-groot2`."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    configure_groot2(args.config.expanduser(), host=args.host, port=args.port)
    app = find_groot2_app(args.app)

    print(f"Groot2 config: {args.config.expanduser()}")
    print(f"Groot2 monitor: host={args.host} port={args.port}")
    if app is None:
        print(
            "Could not find Groot2. Install the AppImage in ~/Applications, "
            "put Groot2/Groot on PATH, or pass --app /path/to/Groot2.AppImage.",
            file=sys.stderr,
        )
        return 1

    print(f"Groot2 app: {app}")
    if args.dry_run:
        return 0

    os.execv(str(app), [str(app)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
