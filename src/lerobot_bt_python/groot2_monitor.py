# Comment: executes this BT logic statement.
"""@file groot2_monitor.py
@brief Launch Groot2 with LeRobot BT monitor defaults.

Groot2 stores its connection fields in a Qt INI file. This entry point updates
that file before starting Groot2 so the real-time monitor opens on the BT.CPP
default endpoint used by `BT::Groot2Publisher`: localhost:1667.
"""

# Comment: imports dependencies or symbols required by the module.
from __future__ import annotations

# Comment: imports dependencies or symbols required by the module.
import argparse
# Comment: imports dependencies or symbols required by the module.
import os
# Comment: imports dependencies or symbols required by the module.
import shutil
# Comment: imports dependencies or symbols required by the module.
import sys
# Comment: imports dependencies or symbols required by the module.
from pathlib import Path

# Comment: assigns or prepares a value used by later statements.
DEFAULT_HOST = "localhost"
# Comment: assigns or prepares a value used by later statements.
DEFAULT_PORT = 1667
# Comment: assigns or prepares a value used by later statements.
DEFAULT_APPIMAGE_NAME = "Groot2-v1.9.0-x86_64.AppImage"

# Comment: assigns or prepares a value used by later statements.
QT_MONITOR_KEY = "APP%3A%3AMode"
# Comment: assigns or prepares a value used by later statements.
QT_HOST_KEY = "ZMQConnectionWidget%3A%3Ahost"
# Comment: assigns or prepares a value used by later statements.
QT_PORT_KEY = "ZMQConnectionWidget%3A%3Aport"


# Comment: defines the function or method _default_config_path.
def _default_config_path() -> Path:
    # Comment: executes this BT logic statement.
    """Return the Groot2 Qt settings path used on Linux."""
    # Comment: assigns or prepares a value used by later statements.
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    # Comment: returns the computed value to the caller.
    return config_home / "AurynRobotics" / "Groot2.ini"


# Comment: defines the function or method _set_qt_key.
def _set_qt_key(lines: list[str], key: str, value: str) -> list[str]:
    # Comment: executes this BT logic statement.
    """Set a single key in the `[General]` section without parsing Qt byte arrays."""
    # Comment: assigns or prepares a value used by later statements.
    key_prefix = f"{key}="
    # Comment: iterates over the elements of the selected sequence.
    for idx, line in enumerate(lines):
        # Comment: evaluates a condition and chooses the branch to run.
        if line.startswith(key_prefix):
            # Comment: assigns or prepares a value used by later statements.
            lines[idx] = f"{key}={value}\n"
            # Comment: returns the computed value to the caller.
            return lines

    # Comment: opens a protected block to catch possible errors.
    try:
        # Comment: assigns or prepares a value used by later statements.
        general_idx = next(idx for idx, line in enumerate(lines) if line.strip() == "[General]")
    # Comment: handles a specific exception raised by the protected block.
    except StopIteration:
        # Comment: evaluates a condition and chooses the branch to run.
        if lines and lines[-1].strip():
            # Comment: closes a call, data structure, or multiline block.
            lines.append("\n")
        # Comment: assigns or prepares a value used by later statements.
        lines.extend(["[General]\n", f"{key}={value}\n"])
        # Comment: returns the computed value to the caller.
        return lines

    # Comment: assigns or prepares a value used by later statements.
    insert_idx = general_idx + 1
    # Comment: assigns or prepares a value used by later statements.
    lines.insert(insert_idx, f"{key}={value}\n")
    # Comment: returns the computed value to the caller.
    return lines


# Comment: defines the function or method configure_groot2.
def configure_groot2(config_path: Path, *, host: str, port: int) -> None:
    # Comment: executes this BT logic statement.
    """Write monitor defaults to Groot2's Qt settings file."""
    # Comment: assigns or prepares a value used by later statements.
    config_path.parent.mkdir(parents=True, exist_ok=True)
    # Comment: evaluates a condition and chooses the branch to run.
    if config_path.exists():
        # Comment: assigns or prepares a value used by later statements.
        lines = config_path.read_text(encoding="utf-8", errors="surrogateescape").splitlines(keepends=True)
    # Comment: handles the fallback branch when previous conditions do not match.
    else:
        # Comment: assigns or prepares a value used by later statements.
        lines = ["[General]\n"]

    # Comment: assigns or prepares a value used by later statements.
    lines = _set_qt_key(lines, QT_MONITOR_KEY, "Monitor")
    # Comment: assigns or prepares a value used by later statements.
    lines = _set_qt_key(lines, QT_HOST_KEY, host)
    # Comment: assigns or prepares a value used by later statements.
    lines = _set_qt_key(lines, QT_PORT_KEY, str(port))
    # Comment: assigns or prepares a value used by later statements.
    config_path.write_text("".join(lines), encoding="utf-8", errors="surrogateescape")


# Comment: defines the function or method _candidate_apps.
def _candidate_apps(explicit_app: str | None) -> list[Path]:
    # Comment: executes this BT logic statement.
    """Return possible Groot2 executables in priority order."""
    # Comment: assigns or prepares a value used by later statements.
    candidates: list[Path] = []
    # Comment: evaluates a condition and chooses the branch to run.
    if explicit_app:
        # Comment: closes a call, data structure, or multiline block.
        candidates.append(Path(explicit_app).expanduser())
    # Comment: assigns or prepares a value used by later statements.
    env_app = os.environ.get("GROOT2_APP")
    # Comment: evaluates a condition and chooses the branch to run.
    if env_app:
        # Comment: closes a call, data structure, or multiline block.
        candidates.append(Path(env_app).expanduser())

    # Comment: iterates over the elements of the selected sequence.
    for command in ("Groot2", "Groot"):
        # Comment: assigns or prepares a value used by later statements.
        resolved = shutil.which(command)
        # Comment: evaluates a condition and chooses the branch to run.
        if resolved:
            # Comment: closes a call, data structure, or multiline block.
            candidates.append(Path(resolved))

    # Comment: assigns or prepares a value used by later statements.
    applications = Path.home() / "Applications"
    # Comment: closes a call, data structure, or multiline block.
    candidates.append(applications / DEFAULT_APPIMAGE_NAME)
    # Comment: assigns or prepares a value used by later statements.
    candidates.extend(sorted(applications.glob("Groot2*.AppImage"), reverse=True))
    # Comment: assigns or prepares a value used by later statements.
    candidates.extend(sorted(applications.glob("Groot*.AppImage"), reverse=True))

    # Comment: assigns or prepares a value used by later statements.
    deduped: list[Path] = []
    # Comment: assigns or prepares a value used by later statements.
    seen: set[Path] = set()
    # Comment: iterates over the elements of the selected sequence.
    for candidate in candidates:
        # Comment: opens a protected block to catch possible errors.
        try:
            # Comment: assigns or prepares a value used by later statements.
            resolved_candidate = candidate.resolve()
        # Comment: handles a specific exception raised by the protected block.
        except OSError:
            # Comment: assigns or prepares a value used by later statements.
            resolved_candidate = candidate
        # Comment: evaluates a condition and chooses the branch to run.
        if resolved_candidate not in seen:
            # Comment: closes a call, data structure, or multiline block.
            deduped.append(candidate)
            # Comment: closes a call, data structure, or multiline block.
            seen.add(resolved_candidate)
    # Comment: returns the computed value to the caller.
    return deduped


# Comment: defines the function or method find_groot2_app.
def find_groot2_app(explicit_app: str | None) -> Path | None:
    # Comment: executes this BT logic statement.
    """Find the Groot2 executable or AppImage."""
    # Comment: iterates over the elements of the selected sequence.
    for candidate in _candidate_apps(explicit_app):
        # Comment: evaluates a condition and chooses the branch to run.
        if candidate.is_file() and os.access(candidate, os.X_OK):
            # Comment: returns the computed value to the caller.
            return candidate
    # Comment: returns the computed value to the caller.
    return None


# Comment: defines the function or method _build_parser.
def _build_parser() -> argparse.ArgumentParser:
    # Comment: assigns or prepares a value used by later statements.
    parser = argparse.ArgumentParser(description="Open Groot2 monitor on the LeRobot BT default port.")
    # Comment: assigns or prepares a value used by later statements.
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Groot2 monitor host (default: {DEFAULT_HOST}).")
    # Comment: assigns or prepares a value used by later statements.
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Groot2 monitor port (default: {DEFAULT_PORT}).")
    # Comment: assigns or prepares a value used by later statements.
    parser.add_argument("--app", help="Path to the Groot2 executable/AppImage.")
    # Comment: executes this BT logic statement.
    parser.add_argument(
        # Comment: executes this BT logic statement.
        "--config",
        # Comment: assigns or prepares a value used by later statements.
        type=Path,
        # Comment: assigns or prepares a value used by later statements.
        default=_default_config_path(),
        # Comment: assigns or prepares a value used by later statements.
        help="Path to Groot2.ini.",
    # Comment: closes a call, data structure, or multiline block.
    )
    # Comment: executes this BT logic statement.
    parser.add_argument(
        # Comment: executes this BT logic statement.
        "--dry-run",
        # Comment: assigns or prepares a value used by later statements.
        action="store_true",
        # Comment: assigns or prepares a value used by later statements.
        help="Write the Groot2 defaults and print the command without launching the GUI.",
    # Comment: closes a call, data structure, or multiline block.
    )
    # Comment: returns the computed value to the caller.
    return parser


# Comment: defines the function or method main.
def main(argv: list[str] | None = None) -> int:
    # Comment: executes this BT logic statement.
    """Console entry point for `lerobot-bt-groot2`."""
    # Comment: assigns or prepares a value used by later statements.
    parser = _build_parser()
    # Comment: assigns or prepares a value used by later statements.
    args = parser.parse_args(argv)

    # Comment: assigns or prepares a value used by later statements.
    configure_groot2(args.config.expanduser(), host=args.host, port=args.port)
    # Comment: assigns or prepares a value used by later statements.
    app = find_groot2_app(args.app)

    # Comment: closes a call, data structure, or multiline block.
    print(f"Groot2 config: {args.config.expanduser()}")
    # Comment: assigns or prepares a value used by later statements.
    print(f"Groot2 monitor: host={args.host} port={args.port}")
    # Comment: evaluates a condition and chooses the branch to run.
    if app is None:
        # Comment: executes this BT logic statement.
        print(
            # Comment: executes this BT logic statement.
            "Could not find Groot2. Install the AppImage in ~/Applications, "
            # Comment: executes this BT logic statement.
            "put Groot2/Groot on PATH, or pass --app /path/to/Groot2.AppImage.",
            # Comment: assigns or prepares a value used by later statements.
            file=sys.stderr,
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: returns the computed value to the caller.
        return 1

    # Comment: closes a call, data structure, or multiline block.
    print(f"Groot2 app: {app}")
    # Comment: evaluates a condition and chooses the branch to run.
    if args.dry_run:
        # Comment: returns the computed value to the caller.
        return 0

    # Comment: closes a call, data structure, or multiline block.
    os.execv(str(app), [str(app)])
    # Comment: returns the computed value to the caller.
    return 0


# Comment: evaluates a condition and chooses the branch to run.
if __name__ == "__main__":
    # Comment: raises an explicit error for the caller.
    raise SystemExit(main())
