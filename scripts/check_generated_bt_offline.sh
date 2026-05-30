#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
read -r -a PYTHON_CMD <<< "${PYTHON_BIN}"

MAKE_TREE="/tmp/generated_make_sandwich.xml"
MAKE_CONFIG="/tmp/generated_make_sandwich_bt.yaml"
BREAKFAST_TREE="/tmp/generated_set_breakfast_table.xml"
BREAKFAST_CONFIG="/tmp/generated_set_breakfast_table_bt.yaml"

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

"${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --out-tree "${MAKE_TREE}" \
  --out-config "${MAKE_CONFIG}" >/dev/null
echo "generated make_sandwich OK"

"${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.generate \
  --task set_breakfast_table \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/set_breakfast_table_executor.yaml \
  --out-tree "${BREAKFAST_TREE}" \
  --out-config "${BREAKFAST_CONFIG}" >/dev/null
echo "generated set_breakfast_table OK"

"${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.static_checks \
  --xml "${MAKE_TREE}" \
  --yaml "${MAKE_CONFIG}" >/dev/null
"${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.static_checks \
  --xml "${BREAKFAST_TREE}" \
  --yaml "${BREAKFAST_CONFIG}" >/dev/null
echo "XML/YAML blackboard keys OK"

"${PYTHON_CMD[@]}" -m pytest \
  tests/lerobot_bt/test_bt_generation_cli.py \
  tests/lerobot_bt/test_bt_generation_fake_execution.py \
  tests/lerobot_bt/test_bt_generation_planner.py \
  tests/lerobot_bt/test_bt_generation_registry.py \
  tests/lerobot_bt/test_bt_generation_renderer.py \
  tests/lerobot_bt/test_bt_generation_static_checks.py \
  tests/lerobot_bt/test_bt_generation_validator.py \
  tests/lerobot_bt/test_generated_bt_cpp_integration.py \
  -q >/dev/null
echo "pytest OK"
