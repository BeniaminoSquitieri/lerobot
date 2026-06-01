#!/usr/bin/env python3
"""
@file bt_preflight_check.py
@brief Pre-flight validation for the LeRobot Behavior Tree (BT) stack.

Runs minimal but thorough checks before launching a BT task. Covers:
  1. ROS 2 environment (Jazzy)
  2. Colcon workspace build
  3. Python / conda environment
  4. YAML configuration consistency (BT params ↔ executor skills)
  5. Policy checkpoint availability (local HuggingFace cache)
  6. Robot hardware readiness (optional, with --real)

Usage:
  # Dry-run validation (no hardware checks):
  python scripts/bt_preflight_check.py --task make_sandwich

  # Full validation including robot/camera checks:
  python scripts/bt_preflight_check.py --task make_sandwich --real

  # Validate all available BT tasks:
  python scripts/bt_preflight_check.py --all

Output:
  - Prints a colour-coded report to the terminal.
  - Exits with code 0 when every mandatory check passes.
  - Exits with code 1 when any mandatory check fails (warnings are non-fatal).

How to swap policy models:
  You only need to edit the executor YAML file (see --executor-yaml).
  - Change ``policy_variant`` (per-skill or top-level) to select the variant.
  - Change ``pretrained_path`` inside each variant to point to your model.
  The BT XML and BT param YAML never reference specific policies.
"""

from __future__ import annotations

import argparse
import importlib
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]  # lerobot/
SRC_DIR = WORKSPACE_ROOT / "src"
INSTALL_SETUP = WORKSPACE_ROOT / "install" / "setup.bash"

# ROS 2 may be installed via apt (/opt/ros/jazzy) or via conda.
# We detect it dynamically rather than hardcoding one path.
ROS2_SETUP_CANDIDATES = [
    Path("/opt/ros/jazzy/setup.bash"),
    Path("/opt/ros/humble/setup.bash"),
]

BT_PYTHON_DIR = SRC_DIR / "lerobot_bt_python"
BT_CPP_DIR = SRC_DIR / "lerobot_bt_runtime_cpp"
PLANNER_SERVICE_NAME = "/lerobot_bt/generate_plan"
PLANNER_SERVICE_TYPE = "lerobot_bt_interfaces/srv/GenerateTaskPlan"

# Known conda/venv environment names (prefix match).
EXPECTED_CONDA_ENVS = ["lerobot"]

# Known BT tasks and their config files
KNOWN_TASKS: dict[str, dict[str, str]] = {
    "make_sandwich": {
        "executor_yaml": "make_sandwich_executor.yaml",
        "bt_yaml": "make_sandwich_bt.yaml",
        "tree_xml": "make_sandwich.xml",
        "launch": "make_sandwich.launch.py",
    },
    "make_coffee": {
        "executor_yaml": "make_coffee_executor.yaml",
        "bt_yaml": "make_coffee_bt.yaml",
        "tree_xml": "make_coffee.xml",
        "launch": "make_coffee.launch.py",
    },
    "set_breakfast_table": {
        "executor_yaml": "set_breakfast_table_executor.yaml",
        "bt_yaml": "set_breakfast_table_bt.yaml",
        "tree_xml": "set_breakfast_table.xml",
        "launch": "set_breakfast_table.launch.py",
    },
    "prepare_picnic_bag": {
        "executor_yaml": "prepare_picnic_bag_executor.yaml",
        "bt_yaml": "prepare_picnic_bag_bt.yaml",
        "tree_xml": "prepare_picnic_bag.xml",
        "launch": "prepare_picnic_bag.launch.py",
    },
    "items_in_drawer": {
        "executor_yaml": "items_in_drawer_executor.yaml",
        "bt_yaml": "items_in_drawer_bt.yaml",
        "tree_xml": "items_in_drawer.xml",
        "launch": "items_in_drawer.launch.py",
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    name: str
    passed: bool
    mandatory: bool
    detail: str = ""
    fix: str = ""


@dataclass
class PreflightReport:
    results: list[CheckResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add(self, result: CheckResult) -> None:
        self.results.append(result)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def all_mandatory_passed(self) -> bool:
        return all(r.passed for r in self.results if r.mandatory)

    def print(self) -> None:
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}  LeRobot BT Preflight Report{RESET}")
        print(f"{BOLD}{'='*60}{RESET}\n")

        for r in self.results:
            icon = f"{GREEN}✓{RESET}" if r.passed else f"{RED}✗{RESET}"
            tag = "[MANDATORY]" if r.mandatory else "[optional]"
            print(f"  {icon} {tag} {r.name}")
            if r.detail:
                print(f"     {r.detail}")
            if not r.passed and r.fix:
                print(f"     {YELLOW}→ Fix: {r.fix}{RESET}")

        if self.warnings:
            print(f"\n  {YELLOW}{BOLD}Warnings:{RESET}")
            for w in self.warnings:
                print(f"    {YELLOW}⚠  {w}{RESET}")

        # Summary
        mandatory_failed = sum(1 for r in self.results if r.mandatory and not r.passed)
        optional_failed = sum(1 for r in self.results if not r.mandatory and not r.passed)
        print(f"\n{BOLD}{'='*60}{RESET}")
        if mandatory_failed == 0:
            print(f"  {GREEN}All mandatory checks passed.{RESET}")
        else:
            print(f"  {RED}{mandatory_failed} mandatory check(s) FAILED.{RESET}")
        if optional_failed:
            print(f"  {YELLOW}{optional_failed} optional check(s) failed (non-blocking).{RESET}")
        print(f"{BOLD}{'='*60}{RESET}\n")


# ---------------------------------------------------------------------------
# Check implementations
# ---------------------------------------------------------------------------


def _check_ros2_environment(report: PreflightReport) -> None:
    """Validate ROS 2 installation (apt or conda) and sourcing."""
    # 1. Check if ros2 command is available
    ros2_path = None
    try:
        result = subprocess.run(["which", "ros2"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            ros2_path = result.stdout.strip()
    except Exception:
        pass

    # 2. Check ROS_DISTRO
    ros_distro = os.environ.get("ROS_DISTRO", "")

    if ros2_path and ros_distro:
        report.add(CheckResult("ROS 2 environment", True, True,
                               f"ros2={ros2_path}, ROS_DISTRO={ros_distro}"))
    elif ros2_path:
        report.add(CheckResult("ROS 2 environment", False, True,
                               f"ros2 found at {ros2_path} but ROS_DISTRO not set. "
                               "Source your ROS 2 setup.bash.",
                               "Run: source /opt/ros/jazzy/setup.bash  or  conda activate <env>"))
        return
    else:
        # Check if any candidate setup.bash exists
        found_candidate = None
        for candidate in ROS2_SETUP_CANDIDATES:
            if candidate.exists():
                found_candidate = candidate
                break
        if found_candidate:
            report.add(CheckResult("ROS 2 environment", False, True,
                                   f"ros2 not in PATH, but {found_candidate} exists. "
                                   "Source it first.",
                                   f"Run: source {found_candidate}"))
        else:
            report.add(CheckResult("ROS 2 environment", False, True,
                                   "ros2 not found in PATH and no setup.bash found. "
                                   "Install ROS 2 Jazzy or activate the correct conda env.",
                                   "Install: https://docs.ros.org/en/jazzy/Installation.html"))
        return

    # 3. ros2 command works
    try:
        result = subprocess.run(["ros2", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            report.add(CheckResult("ros2 CLI works", True, True,
                                   f"Version: {result.stdout.strip()}"))
        else:
            report.add(CheckResult("ros2 CLI works", False, True,
                                   f"ros2 --version returned {result.returncode}"))
    except FileNotFoundError:
        report.add(CheckResult("ros2 CLI works", False, True,
                               "'ros2' command not found in PATH"))
    except Exception as e:
        report.add(CheckResult("ros2 CLI works", False, True, str(e)))


def _check_plan_service(report: PreflightReport) -> None:
    """Validate the optional VLM planner ROS service contract."""

    if shutil.which("ros2") is None:
        report.add(CheckResult(
            "Planner service: ros2 available",
            False,
            True,
            "ros2 command not found in PATH.",
            "Source ROS 2 and the built workspace: source /opt/ros/<distro>/setup.bash && source install/setup.bash",
        ))
        return
    report.add(CheckResult("Planner service: ros2 available", True, True))

    try:
        service_list = subprocess.run(
            ["ros2", "service", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as e:
        report.add(CheckResult(
            f"Planner service listed: {PLANNER_SERVICE_NAME}",
            False,
            True,
            str(e),
            "Start ROS 2 and the planner bridge, then rerun with --check-plan-service.",
        ))
        return

    if service_list.returncode != 0:
        detail = service_list.stderr.strip() or service_list.stdout.strip()
        report.add(CheckResult(
            f"Planner service listed: {PLANNER_SERVICE_NAME}",
            False,
            True,
            detail or f"ros2 service list returned {service_list.returncode}.",
            "Source ROS 2, source install/setup.bash, and start the planner service node.",
        ))
        return

    service_names = {line.strip() for line in service_list.stdout.splitlines() if line.strip()}
    if PLANNER_SERVICE_NAME not in service_names:
        report.add(CheckResult(
            f"Planner service listed: {PLANNER_SERVICE_NAME}",
            False,
            True,
            f"Available services: {sorted(service_names)[:10]}",
            "Start panda_live_viewer or the bridge node exposing /lerobot_bt/generate_plan.",
        ))
        return
    report.add(CheckResult(f"Planner service listed: {PLANNER_SERVICE_NAME}", True, True))

    try:
        service_type = subprocess.run(
            ["ros2", "service", "type", PLANNER_SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as e:
        report.add(CheckResult(
            "Planner service type",
            False,
            True,
            str(e),
            "Confirm the service is still running and the workspace is sourced.",
        ))
        return

    if service_type.returncode != 0:
        detail = service_type.stderr.strip() or service_type.stdout.strip()
        report.add(CheckResult(
            "Planner service type",
            False,
            True,
            detail or f"ros2 service type returned {service_type.returncode}.",
            "Rebuild/source lerobot_bt_interfaces and restart the planner service node.",
        ))
        return

    actual_type = service_type.stdout.strip().splitlines()[0] if service_type.stdout.strip() else ""
    if actual_type != PLANNER_SERVICE_TYPE:
        report.add(CheckResult(
            "Planner service type",
            False,
            True,
            f"Expected {PLANNER_SERVICE_TYPE}, got {actual_type!r}.",
            "Use lerobot_bt_interfaces/srv/GenerateTaskPlan on /lerobot_bt/generate_plan.",
        ))
        return
    report.add(CheckResult("Planner service type", True, True, PLANNER_SERVICE_TYPE))


def _check_workspace_build(report: PreflightReport) -> None:
    """Verify the colcon workspace has been built."""
    if INSTALL_SETUP.exists():
        report.add(CheckResult("Workspace install/ found", True, True,
                               f"Path: {INSTALL_SETUP}"))
    else:
        report.add(CheckResult("Workspace install/ found", False, True,
                               f"Missing: {INSTALL_SETUP}",
                               "Run: cd ~/users/sben/lerobot && colcon build --base-paths src --packages-up-to lerobot_bt_runtime_cpp"))

    # Check key ROS2 packages exist in install
    for pkg in ["lerobot_bt_interfaces", "lerobot_bt_runtime_cpp"]:
        pkg_share = WORKSPACE_ROOT / "install" / pkg / "share" / pkg
        if pkg_share.exists():
            report.add(CheckResult(f"Package built: {pkg}", True, True))
        else:
            report.add(CheckResult(f"Package built: {pkg}", False, True,
                                   f"Missing share dir: {pkg_share}",
                                   "Run: colcon build --base-paths src --packages-up-to lerobot_bt_runtime_cpp"))


def _check_python_environment(report: PreflightReport) -> None:
    """Check conda env and critical Python imports."""
    # 1. conda environment
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "")
    if any(conda_env.startswith(prefix) for prefix in EXPECTED_CONDA_ENVS):
        report.add(CheckResult("Conda env OK", True, True,
                               f"Active env: '{conda_env}'"))
    elif conda_env:
        report.add(CheckResult("Conda env OK", False, True,
                               f"Active env is '{conda_env}', expected one starting with {EXPECTED_CONDA_ENVS}",
                               f"Run: conda activate lerobot"))
    else:
        report.warn("CONDA_DEFAULT_ENV not set. Are you in the correct environment?")

    # 2. Python version
    py_version = sys.version_info
    if py_version >= (3, 10):
        report.add(CheckResult(f"Python {py_version.major}.{py_version.minor}.{py_version.micro}", True, True))
    else:
        report.add(CheckResult("Python >= 3.10", False, True,
                               f"Found Python {py_version.major}.{py_version.minor}",
                               "Use Python 3.10+ with the lerobot conda environment"))

    # 3. Key imports
    for mod_name, desc in [
        ("lerobot", "lerobot core"),
        ("rclpy", "ROS 2 Python (rclpy)"),
        ("torch", "PyTorch"),
        ("lerobot_bt_python", "lerobot_bt_python (BT execution layer)"),
    ]:
        try:
            importlib.import_module(mod_name)
            report.add(CheckResult(f"Import: {desc}", True, True))
        except ImportError:
            report.add(CheckResult(f"Import: {desc}", False, True,
                                   f"Cannot import '{mod_name}'",
                                   "Run: pip install -e .  (from the lerobot workspace root)"))


def _check_yaml_consistency(report: PreflightReport, task: str) -> None:
    """Cross-validate skill names between BT YAML params and executor YAML."""
    import yaml

    task_info = KNOWN_TASKS[task]
    executor_yaml_path = BT_PYTHON_DIR / task_info["executor_yaml"]
    bt_yaml_path = BT_CPP_DIR / "config" / task_info["bt_yaml"]
    tree_xml_path = BT_CPP_DIR / "trees" / task_info["tree_xml"]

    # 1. Files exist
    for label, path in [("Executor YAML", executor_yaml_path),
                        ("BT params YAML", bt_yaml_path),
                        ("BT tree XML", tree_xml_path)]:
        if path.exists():
            report.add(CheckResult(f"{label} exists", True, True, f"Path: {path}"))
        else:
            report.add(CheckResult(f"{label} exists", False, True,
                                   f"Missing: {path}"))
            return

    # 2. Parse executor YAML → skill names
    try:
        with open(executor_yaml_path) as fh:
            executor_cfg = yaml.safe_load(fh)
    except Exception as e:
        report.add(CheckResult("Parse executor YAML", False, True, str(e)))
        return

    executor_skill_names: set[str] = set()
    for skill in executor_cfg.get("skills", []):
        name = skill.get("name")
        if name:
            executor_skill_names.add(name)

    expected_skill_names: set[str] = set(executor_cfg.get("expected_skill_names", []))

    if executor_skill_names:
        report.add(CheckResult("Executor YAML has skills", True, True,
                               f"Skills: {sorted(executor_skill_names)}"))
    else:
        report.add(CheckResult("Executor YAML has skills", False, True,
                               "No skills defined in executor YAML"))

    # 3. Parse BT params YAML → skill references (values ending in _skill)
    try:
        with open(bt_yaml_path) as fh:
            bt_cfg = yaml.safe_load(fh)
    except Exception as e:
        report.add(CheckResult("Parse BT params YAML", False, True, str(e)))
        return

    bt_params = bt_cfg.get("lerobot_bt_runner", {}).get("ros__parameters", {}).get("bt", {})
    bt_skill_names: set[str] = set()
    for key, value in bt_params.items():
        if key.endswith("_skill") and isinstance(value, str):
            bt_skill_names.add(value)

    if bt_skill_names:
        report.add(CheckResult("BT params YAML has skill refs", True, True,
                               f"Skills: {sorted(bt_skill_names)}"))
    else:
        report.add(CheckResult("BT params YAML has skill refs", False, True,
                               "No *_skill entries found in BT params YAML"))

    # 4. CROSS-VALIDATE: BT skill names ⊆ executor skill names
    missing_in_executor = bt_skill_names - executor_skill_names
    if not missing_in_executor:
        report.add(CheckResult("BT→Executor skill name match", True, True,
                               "All BT-referenced skills exist in executor YAML"))
    else:
        report.add(CheckResult("BT→Executor skill name match", False, True,
                               f"BT references skills not in executor: {sorted(missing_in_executor)}",
                               "Add missing skill entries to executor YAML or fix BT params YAML"))

    # 5. CROSS-VALIDATE: expected_skill_names match BT skills
    if expected_skill_names:
        unexpected = expected_skill_names - bt_skill_names
        missing_expected = bt_skill_names - expected_skill_names
        if not unexpected and not missing_expected:
            report.add(CheckResult("expected_skill_names ↔ BT skills match", True, True))
        else:
            msg_parts = []
            if unexpected:
                msg_parts.append(f"Extra in expected: {sorted(unexpected)}")
            if missing_expected:
                msg_parts.append(f"Missing from expected: {sorted(missing_expected)}")
            report.add(CheckResult("expected_skill_names ↔ BT skills match", False, True,
                                   "; ".join(msg_parts),
                                   "Update 'expected_skill_names' in executor YAML to match BT params"))

    # 6. Parse XML tree → verify tree structure is valid
    try:
        tree_text = tree_xml_path.read_text()
        if "<BehaviorTree" in tree_text and "</root>" in tree_text:
            report.add(CheckResult("BT XML tree syntax valid", True, True))
        else:
            report.add(CheckResult("BT XML tree syntax valid", False, True,
                                   "XML missing expected BehaviorTree/root tags"))
    except Exception as e:
        report.add(CheckResult("BT XML tree readable", False, True, str(e)))


def _check_policy_checkpoints(report: PreflightReport, task: str) -> None:
    """Verify that referenced HuggingFace policy checkpoints are cached locally."""
    import yaml

    task_info = KNOWN_TASKS[task]
    executor_yaml_path = BT_PYTHON_DIR / task_info["executor_yaml"]

    try:
        with open(executor_yaml_path) as fh:
            executor_cfg = yaml.safe_load(fh)
    except Exception:
        return  # Already reported in YAML consistency check

    # Determine HF cache dir
    hf_home = os.environ.get("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
    hf_hub_cache = os.environ.get("HUGGINGFACE_HUB_CACHE", str(Path(hf_home) / "hub"))

    skills = executor_cfg.get("skills", [])
    default_variant = executor_cfg.get("policy_variant", "")

    total_checked = 0
    available = 0
    missing_paths: list[str] = []

    for skill in skills:
        skill_name = skill.get("name", "?")
        active_variant = skill.get("policy_variant", default_variant)
        variants = skill.get("policy_variants", {})

        # Also check legacy direct policy
        direct_policy = skill.get("policy")
        if direct_policy:
            pp = direct_policy.get("pretrained_path", "")
            if pp and not pp.startswith("TODO_"):
                total_checked += 1
                # Check local cache
                org_repo = pp.replace("/", "--") if "/" in pp else pp
                # Handle paths like "HSP-IIT/act_toast_pick_and_place"
                # HF cache structure: <cache>/models--<org>--<repo>/snapshots/...
                expected_dir = Path(hf_hub_cache) / f"models--{pp.replace('/', '--')}"
                # Also check old-style cache
                alt_dir = Path(hf_home) / "hub" / f"models--{pp.replace('/', '--')}"
                if expected_dir.exists() or alt_dir.exists():
                    available += 1
                else:
                    missing_paths.append(f"{skill_name}: {pp} (direct policy)")

        if active_variant and active_variant in variants:
            v = variants[active_variant]
            pp = v.get("pretrained_path", "")
            if pp and not pp.startswith("TODO_"):
                total_checked += 1
                expected_dir = Path(hf_hub_cache) / f"models--{pp.replace('/', '--')}"
                alt_dir = Path(hf_home) / "hub" / f"models--{pp.replace('/', '--')}"
                if expected_dir.exists() or alt_dir.exists():
                    available += 1
                else:
                    missing_paths.append(f"{skill_name} ({active_variant}): {pp}")

    if total_checked == 0:
        report.add(CheckResult("Policy checkpoints cached", True, False,
                               "No non-TODO pretrained_path entries found; nothing to check"))
    elif missing_paths:
        report.add(CheckResult("Policy checkpoints cached", False, False,
                               f"{available}/{total_checked} cached locally. Missing: {', '.join(missing_paths[:3])}{'...' if len(missing_paths) > 3 else ''}",
                               "Models will be auto-downloaded from HuggingFace Hub at runtime. "
                               "Pre-download with: python -c \"from huggingface_hub import snapshot_download; snapshot_download('ORG/MODEL')\""))
        report.warn(f"Missing checkpoints: {', '.join(missing_paths)}")
    else:
        report.add(CheckResult("Policy checkpoints cached", True, False,
                               f"All {available} checkpoints found in HF cache"))


def _check_robot_hardware(report: PreflightReport, task: str) -> None:
    """Detect robot and camera hardware (requires real hardware connected)."""
    import yaml

    task_info = KNOWN_TASKS[task]
    executor_yaml_path = BT_PYTHON_DIR / task_info["executor_yaml"]

    try:
        with open(executor_yaml_path) as fh:
            executor_cfg = yaml.safe_load(fh)
    except Exception:
        return

    robot_cfg = executor_cfg.get("robot", {})

    # 1. Camera detection via lerobot-find-cameras
    required_cameras = executor_cfg.get("required_cameras", [])
    if required_cameras:
        try:
            result = subprocess.run(
                ["lerobot-find-cameras"],
                capture_output=True, text=True, timeout=30,
                env={**os.environ, "PYTHONUNBUFFERED": "1"}
            )
            if result.returncode == 0:
                report.add(CheckResult("Camera detection script ran", True, False,
                                       f"Output: {result.stdout.strip()[:200]}"))
            else:
                report.add(CheckResult("Camera detection script ran", False, False,
                                       f"Return code {result.returncode}: {result.stderr.strip()[:200]}"))
        except FileNotFoundError:
            report.add(CheckResult("Camera detection script", False, False,
                                   "'lerobot-find-cameras' not found in PATH",
                                   "Install: pip install -e ."))
        except Exception as e:
            report.add(CheckResult("Camera detection script", False, False, str(e)))

    # 2. Check configured cameras
    cameras = robot_cfg.get("cameras", {})
    for cam_name in required_cameras:
        if cam_name in cameras:
            cam_cfg = cameras[cam_name]
            serial = cam_cfg.get("serial_number_or_name", "?")
            report.add(CheckResult(f"Camera '{cam_name}' configured", True, False,
                                   f"Type: {cam_cfg.get('type')}, Serial: {serial}"))
        else:
            report.add(CheckResult(f"Camera '{cam_name}' configured", False, False,
                                   f"required_cameras lists '{cam_name}' but it's not in robot.cameras"))

    # 3. Robot arm config
    arm = robot_cfg.get("arm", {})
    if arm:
        report.add(CheckResult("Robot arm configured", True, False,
                               f"Type: {arm.get('type')}, Visualize: {arm.get('visualize')}"))
    else:
        report.warn("No robot arm configuration found in executor YAML")

    # 4. Gripper config
    gripper = robot_cfg.get("gripper", {})
    if gripper:
        report.add(CheckResult("Gripper configured", True, False,
                               f"Type: {gripper.get('type')}"))
    else:
        report.warn("No gripper configuration found in executor YAML")

    # 5. Check if panda robot is reachable (via ping to typical IP)
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", "172.16.0.2"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            report.add(CheckResult("Panda robot reachable (172.16.0.2)", True, False))
        else:
            report.add(CheckResult("Panda robot reachable (172.16.0.2)", False, False,
                                   "Could not ping Panda at 172.16.0.2. Is the robot on and connected?",
                                   "Check Ethernet connection to the Franka Panda arm."))
    except Exception:
        report.add(CheckResult("Panda robot reachable (172.16.0.2)", False, False,
                               "Ping check failed (network may be unavailable)"))


def _print_policy_swap_guide(task: str) -> None:
    """Print a quick-reference guide for swapping policy models."""
    task_info = KNOWN_TASKS[task]
    executor_yaml_path = BT_PYTHON_DIR / task_info["executor_yaml"]
    bt_yaml_path = BT_CPP_DIR / "config" / task_info["bt_yaml"]

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           HOW TO SWAP POLICY MODELS — QUICK GUIDE           ║
╠══════════════════════════════════════════════════════════════╣
║                                                            ║
║  You only need to edit ONE file:                           ║
║    {executor_yaml_path.name:<50}║
║                                                            ║
║  These files NEVER need changes for policy swaps:          ║
║    {bt_yaml_path.name:<50}║
║    {task_info['tree_xml']:<50}║
║                                                            ║
║  ── Option A: Change the active variant ──                 ║
║  Set policy_variant (per-skill or top-level) to one of:    ║
║    act | smolvla | diffusion | pi0 | pi0_fast | pi05       ║
║    groot | xvla | vqbet | tdmpc | wall_x | sac | sarm      ║
║                                                            ║
║  ── Option B: Update a pretrained_path ──                  ║
║  Under policy_variants.<variant>, change pretrained_path   ║
║  to your HuggingFace model id:                             ║
║    pretrained_path: "YourOrg/your-model-name"              ║
║                                                            ║
║  ── Option C: Add a new variant ──                         ║
║  Add a new entry under policy_variants with type, device,  ║
║  pretrained_path, and policy-specific parameters.          ║
║  Then set policy_variant to the new variant name.          ║
║                                                            ║
╚══════════════════════════════════════════════════════════════╝
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LeRobot BT preflight check — validate everything before launching a BT task.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/bt_preflight_check.py --task make_sandwich
  python scripts/bt_preflight_check.py --task make_sandwich --real
  python scripts/bt_preflight_check.py --all
  python scripts/bt_preflight_check.py --task make_sandwich --guide-only
        """,
    )
    parser.add_argument(
        "--task", type=str, choices=list(KNOWN_TASKS),
        help="BT task to validate (e.g., make_sandwich, make_coffee)."
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Validate all known BT tasks."
    )
    parser.add_argument(
        "--real", action="store_true",
        help="Include real-robot hardware checks (cameras, Panda ping)."
    )
    parser.add_argument(
        "--guide-only", action="store_true",
        help="Only print the policy-swap guide and exit."
    )
    parser.add_argument(
        "--check-plan-service", action="store_true",
        help="Also validate the optional /lerobot_bt/generate_plan ROS planner service."
    )
    args = parser.parse_args()

    # Determine tasks to validate
    if args.all:
        tasks = list(KNOWN_TASKS)
    elif args.task:
        tasks = [args.task]
    else:
        parser.print_help()
        sys.exit(1)

    # Guide-only mode
    if args.guide_only:
        for task in tasks:
            _print_policy_swap_guide(task)
        return

    for task in tasks:
        if task not in KNOWN_TASKS:
            print(f"Unknown task: {task}")
            continue

        report = PreflightReport()

        print(f"\nRunning preflight checks for task: {task} ...")

        # Mandatory checks (in order of dependency)
        _check_ros2_environment(report)
        _check_workspace_build(report)
        _check_python_environment(report)
        _check_yaml_consistency(report, task)

        # Optional checks
        _check_policy_checkpoints(report, task)
        if args.check_plan_service:
            _check_plan_service(report)

        if args.real:
            _check_robot_hardware(report, task)

        report.print()
        _print_policy_swap_guide(task)

        if not report.all_mandatory_passed:
            sys.exit(1)

    print("All preflight checks completed.")


if __name__ == "__main__":
    main()
