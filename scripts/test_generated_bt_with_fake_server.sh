#!/usr/bin/env bash
set -euo pipefail

SCENARIO="${1:-success_all}"
EXPECTED="${2:-success}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TREE_PATH="/tmp/generated_make_sandwich.xml"
CONFIG_PATH="/tmp/generated_make_sandwich_bt.yaml"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}"

"${PYTHON_BIN}" -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --out-tree "${TREE_PATH}" \
  --out-config "${CONFIG_PATH}"

"${PYTHON_BIN}" -m lerobot_bt_python.fakes.fake_bt_executor_server \
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
