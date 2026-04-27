#!/usr/bin/env bash
set -euo pipefail

# Bootstrap script for Sandwich BT stack on fresh machines.
# Expected usage:
#   1) conda activate <your_env>
#   2) bash useful_scripts/bootstrap_sandwich_bt.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SKIP_APT=0
SKIP_PYTHON=0
FULL_PYTHON=0
SKIP_BUILD=0
NO_CLEAN_CACHE=0
ASSUME_YES=0

log() {
  echo "[bootstrap] $*"
}

die() {
  echo "[bootstrap][error] $*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage:
  bash useful_scripts/bootstrap_sandwich_bt.sh [options]

Options:
  --skip-apt        Skip apt install of libzmq3-dev.
  --skip-python     Skip Python dependency install.
  --full-python     Install full Python stack from requirements-ubuntu.txt.
                    (default is minimal editable install with transformers extra)
  --skip-build      Skip colcon build.
  --no-clean-cache  Do not pass --cmake-clean-cache to colcon build.
  -y, --yes         Non-interactive apt install (-y).
  -h, --help        Show this help.

Notes:
  - Run this script after activating your conda env.
  - It installs conda ZeroMQ packages and exports CMake/pkg-config paths.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-apt)
      SKIP_APT=1
      ;;
    --skip-python)
      SKIP_PYTHON=1
      ;;
    --full-python)
      FULL_PYTHON=1
      ;;
    --skip-build)
      SKIP_BUILD=1
      ;;
    --no-clean-cache)
      NO_CLEAN_CACHE=1
      ;;
    -y|--yes)
      ASSUME_YES=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown option: $1"
      ;;
  esac
  shift
done

cd "${REPO_ROOT}"

if [[ -z "${CONDA_PREFIX:-}" ]]; then
  die "No active conda env. Run: conda activate <env_name>"
fi

if ! command -v colcon >/dev/null 2>&1; then
  die "colcon not found in PATH. Ensure your conda env provides ROS/colcon tools."
fi

log "Repo root: ${REPO_ROOT}"
log "Conda env: ${CONDA_DEFAULT_ENV:-unknown}"
log "Conda prefix: ${CONDA_PREFIX}"

if [[ "${SKIP_APT}" -eq 0 ]]; then
  if dpkg -s libzmq3-dev >/dev/null 2>&1; then
    log "libzmq3-dev already installed"
  else
    log "Installing system dependency: libzmq3-dev"
    if ! command -v sudo >/dev/null 2>&1; then
      die "sudo not available. Install libzmq3-dev manually or rerun with --skip-apt"
    fi
    if [[ "${ASSUME_YES}" -eq 1 ]]; then
      sudo apt install -y libzmq3-dev
    else
      sudo apt install libzmq3-dev
    fi
  fi
fi

if command -v conda >/dev/null 2>&1; then
  log "Installing conda deps: zeromq cppzmq pkg-config"
  conda install -y -c conda-forge zeromq cppzmq pkg-config
else
  die "conda command not available in this shell"
fi

# Persist env vars for future conda activations.
mkdir -p "${CONDA_PREFIX}/etc/conda/activate.d"
cat > "${CONDA_PREFIX}/etc/conda/activate.d/sandwich_bt_env.sh" <<'EOF'
#!/usr/bin/env bash
export PKG_CONFIG_PATH="$CONDA_PREFIX/lib/pkgconfig:$CONDA_PREFIX/share/pkgconfig:${PKG_CONFIG_PATH:-}"
export CMAKE_PREFIX_PATH="$CONDA_PREFIX:${CMAKE_PREFIX_PATH:-}"
EOF
chmod +x "${CONDA_PREFIX}/etc/conda/activate.d/sandwich_bt_env.sh"

# Apply env vars in current shell too.
export PKG_CONFIG_PATH="$CONDA_PREFIX/lib/pkgconfig:$CONDA_PREFIX/share/pkgconfig:${PKG_CONFIG_PATH:-}"
export CMAKE_PREFIX_PATH="$CONDA_PREFIX:${CMAKE_PREFIX_PATH:-}"

log "PKG_CONFIG_PATH and CMAKE_PREFIX_PATH configured"

if [[ "${SKIP_PYTHON}" -eq 0 ]]; then
  if [[ "${FULL_PYTHON}" -eq 1 ]]; then
    log "Installing full Python dependencies from requirements-ubuntu.txt"
    python -m pip install -r requirements-ubuntu.txt
  else
    log "Installing minimal Python dependencies for sandwich stack"
    python -m pip install -e ".[transformers-dep]"
  fi
fi

if [[ "${SKIP_BUILD}" -eq 0 ]]; then
  CLEAN_ARGS=()
  if [[ "${NO_CLEAN_CACHE}" -eq 0 ]]; then
    CLEAN_ARGS+=(--cmake-clean-cache)
  fi

  log "Building ROS packages: behaviortree_cpp -> sandwich_bt_runtime_cpp"
  colcon build --base-paths src \
    --packages-up-to behaviortree_cpp sandwich_bt_runtime_cpp \
    "${CLEAN_ARGS[@]}"
fi

if [[ -f "install/setup.bash" ]]; then
  # shellcheck disable=SC1091
  source install/setup.bash
fi

# Fallback for cases where overlay setup indexes only part of workspace.
export COLCON_PREFIX_PATH="${REPO_ROOT}/install/sandwich_bt_runtime_cpp:${REPO_ROOT}/install/sandwich_bt_interfaces:${REPO_ROOT}/install/behaviortree_cpp:${COLCON_PREFIX_PATH:-}"
export AMENT_PREFIX_PATH="${REPO_ROOT}/install/sandwich_bt_runtime_cpp:${REPO_ROOT}/install/sandwich_bt_interfaces:${REPO_ROOT}/install/behaviortree_cpp:${AMENT_PREFIX_PATH:-}"

log "Bootstrap completed"
log "Quick checks:"
log "  pkg-config --modversion libzmq"
log "  ros2 pkg list | grep sandwich"
log "  ros2 run sandwich_bt_runtime_cpp sandwich_bt_runner"
