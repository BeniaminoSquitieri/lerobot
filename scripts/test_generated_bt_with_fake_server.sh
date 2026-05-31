#!/usr/bin/env bash
set -euo pipefail

SCENARIO="${1:-success_all}"
EXPECTED="${2:-success}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GENERATED_BT_DIR="${GENERATED_BT_DIR:-generated_bt}"
TREE_PATH="${GENERATED_BT_DIR}/trees/make_sandwich.xml"
CONFIG_PATH="${GENERATED_BT_DIR}/config/make_sandwich_bt.yaml"
PYTHON_BIN="${PYTHON_BIN:-python}"
read -r -a PYTHON_CMD <<< "${PYTHON_BIN}"

cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}"

if ! command -v "${PYTHON_CMD[0]}" >/dev/null 2>&1; then
  if [[ "${PYTHON_BIN}" == "python" ]] && command -v conda >/dev/null 2>&1; then
    PYTHON_CMD=(conda run -n lerobot python)
  elif [[ "${PYTHON_BIN}" == "python" ]] && command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=(python3)
  else
    echo "ERROR: PYTHON_BIN command not found: ${PYTHON_BIN}" >&2
    exit 2
  fi
fi

command -v ros2 >/dev/null 2>&1 || {
  echo "ERROR: ROS2 not found. Source ROS2 before running C++ integration test." >&2
  echo "Example: source /opt/ros/<distro>/setup.bash" >&2
  exit 2
}

"${PYTHON_CMD[@]}" -c "import rclpy" >/dev/null 2>&1 || {
  echo "ERROR: rclpy not available in PYTHON_BIN environment: ${PYTHON_BIN}" >&2
  echo "Use a ROS2 Python environment or source the ROS2 workspace." >&2
  exit 2
}

ros2 pkg prefix lerobot_bt_runtime_cpp >/dev/null 2>&1 || {
  echo "ERROR: lerobot_bt_runtime_cpp package not found." >&2
  echo "Build and source the workspace:" >&2
  echo "  colcon build --symlink-install" >&2
  echo "  source install/setup.bash" >&2
  exit 2
}

"${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --output-dir "${GENERATED_BT_DIR}"

"${PYTHON_CMD[@]}" -m lerobot_bt_python.fakes.fake_bt_executor_server \
  --scenario "${SCENARIO}" \
  --running-polls-before-failure 3 &
SERVER_PID="$!"

cleanup() {
  if kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

sleep 1

set +e
ros2 run lerobot_bt_runtime_cpp lerobot_bt_runner \
  --ros-args \
  --params-file "${CONFIG_PATH}" \
  -p "tree_xml_path:=${TREE_PATH}" \
  -p "enable_groot_publisher:=false" \
  -p "tick_ms:=10"
RUNNER_STATUS="$?"
set -e

if [[ "${EXPECTED}" == "success" && "${RUNNER_STATUS}" -ne 0 ]]; then
  echo "Expected BT success for scenario ${SCENARIO}, got exit ${RUNNER_STATUS}" >&2
  exit 1
fi

if [[ "${EXPECTED}" == "failure" && "${RUNNER_STATUS}" -eq 0 ]]; then
  echo "Expected BT failure for scenario ${SCENARIO}, got success" >&2
  exit 1
fi

echo "Scenario ${SCENARIO} matched expected ${EXPECTED} outcome."
