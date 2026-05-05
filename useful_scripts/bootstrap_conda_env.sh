#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

ENV_NAME="lerobot"
PYTHON_VERSION="3.12"
PROFILE="sandwich"
INSTALL_FFMPEG=1
CREATE_ENV=0

log() {
  echo "[conda-bootstrap] $*"
}

die() {
  echo "[conda-bootstrap][error] $*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage:
  bash useful_scripts/bootstrap_conda_env.sh [options]

Options:
  --env-name NAME        Conda environment name. Default: lerobot
  --python VERSION       Python version for new envs. Default: 3.12
  --profile NAME         Dependency profile to install.
                         Available: base, dev, all, sandwich
                         Default: sandwich
  --create-env           Create the conda env if it does not exist.
  --no-ffmpeg            Skip ffmpeg install from conda-forge.
  -h, --help             Show this help.

Examples:
  conda activate lerobot
  bash useful_scripts/bootstrap_conda_env.sh

  bash useful_scripts/bootstrap_conda_env.sh --create-env --env-name lerobot --profile dev
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-name)
      ENV_NAME="${2:-}"
      shift
      ;;
    --python)
      PYTHON_VERSION="${2:-}"
      shift
      ;;
    --profile)
      PROFILE="${2:-}"
      shift
      ;;
    --create-env)
      CREATE_ENV=1
      ;;
    --no-ffmpeg)
      INSTALL_FFMPEG=0
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

if ! command -v conda >/dev/null 2>&1; then
  die "conda not found in PATH"
fi

case "${PROFILE}" in
  base)
    EXTRAS="core_scripts"
    ;;
  dev)
    EXTRAS="core_scripts,training,dev,test"
    ;;
  all)
    EXTRAS="all"
    ;;
  sandwich)
    EXTRAS="core_scripts,training,dev,test,pi,async"
    ;;
  *)
    die "Invalid profile '${PROFILE}'. Use: base, dev, all, sandwich"
    ;;
esac

if [[ "${CREATE_ENV}" -eq 1 ]]; then
  if conda env list | awk '{print $1}' | grep -Fxq "${ENV_NAME}"; then
    log "Conda env '${ENV_NAME}' already exists"
  else
    log "Creating conda env '${ENV_NAME}' with Python ${PYTHON_VERSION}"
    conda create -y -n "${ENV_NAME}" "python=${PYTHON_VERSION}"
  fi
fi

if [[ -z "${CONDA_PREFIX:-}" || "${CONDA_DEFAULT_ENV:-}" != "${ENV_NAME}" ]]; then
  die "Activate the target env first: conda activate ${ENV_NAME}"
fi

cd "${REPO_ROOT}"

log "Repo root: ${REPO_ROOT}"
log "Conda env: ${CONDA_DEFAULT_ENV}"
log "Installing base conda packages"
conda install -y -c conda-forge pip setuptools wheel

if [[ "${INSTALL_FFMPEG}" -eq 1 ]]; then
  log "Installing ffmpeg in the conda env"
  conda install -y -c conda-forge ffmpeg
fi

log "Installing editable Python package with extras: ${EXTRAS}"
python -m pip install -e ".[${EXTRAS}]"

if [[ "${PROFILE}" == "sandwich" ]]; then
  log "Installing sandwich/ROS helpers in the current conda env"
  conda install -y -c conda-forge zeromq cppzmq pkg-config
  python -m pip install empy
fi

log "Bootstrap completed"
log "Environment '${ENV_NAME}' now has profile '${PROFILE}' installed"
