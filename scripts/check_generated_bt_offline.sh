#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
read -r -a PYTHON_CMD <<< "${PYTHON_BIN}"
GENERATED_BT_DIR="${GENERATED_BT_DIR:-generated_bt}"

TASKS=(
  "make_sandwich"
  "set_breakfast_table"
  "make_coffee"
  "prepare_picnic_bag"
  "items_in_drawer"
)

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

echo "writing generated BT artifacts to ${GENERATED_BT_DIR}"

for task in "${TASKS[@]}"; do
  "${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.generate \
    --task "${task}" \
    --planner template \
    --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
    --executor-yaml "src/lerobot_bt_python/${task}_executor.yaml" \
    --output-dir "${GENERATED_BT_DIR}"

  tree="${GENERATED_BT_DIR}/trees/${task}.xml"
  config="${GENERATED_BT_DIR}/config/${task}_bt.yaml"
  echo "generated ${task} OK"

  "${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.static_checks \
    --xml "${tree}" \
    --yaml "${config}" >/dev/null
  echo "checked ${tree}"
  echo "checked ${config}"
done

"${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --planner model-response \
  --model-response-file tests/assets/vlm_planner/make_sandwich_valid.json \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --output-dir "${GENERATED_BT_DIR}"
echo "generated make_sandwich model-response OK"

MODEL_TREE="${GENERATED_BT_DIR}/trees/make_sandwich.xml"
MODEL_CONFIG="${GENERATED_BT_DIR}/config/make_sandwich_bt.yaml"
"${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.static_checks \
  --xml "${MODEL_TREE}" \
  --yaml "${MODEL_CONFIG}" >/dev/null
echo "checked ${GENERATED_BT_DIR}/plans/make_sandwich_linear_ir.json"
echo "checked ${GENERATED_BT_DIR}/raw_model_responses/make_sandwich_raw_response.json"
echo "XML/YAML blackboard keys OK"

"${PYTHON_CMD[@]}" -m pytest \
  tests/lerobot_bt/test_bt_generation_cli.py \
  tests/lerobot_bt/test_bt_generation_all_runtime_tasks.py \
  tests/lerobot_bt/test_bt_generation_fake_execution.py \
  tests/lerobot_bt/test_bt_generation_planner.py \
  tests/lerobot_bt/test_bt_generation_registry.py \
  tests/lerobot_bt/test_bt_generation_renderer.py \
  tests/lerobot_bt/test_bt_generation_static_checks.py \
  tests/lerobot_bt/test_bt_generation_validator.py \
  tests/lerobot_bt/test_bt_generation_vlm_planner.py \
  tests/lerobot_bt/test_generated_bt_cpp_integration.py \
  -q >/dev/null
echo "pytest OK"
