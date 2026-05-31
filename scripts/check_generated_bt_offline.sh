#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
read -r -a PYTHON_CMD <<< "${PYTHON_BIN}"

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

for task in "${TASKS[@]}"; do
  tree="/tmp/generated_${task}.xml"
  config="/tmp/generated_${task}_bt.yaml"
  "${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.generate \
    --task "${task}" \
    --planner template \
    --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
    --executor-yaml "src/lerobot_bt_python/${task}_executor.yaml" \
    --out-tree "${tree}" \
    --out-config "${config}" >/dev/null
  echo "generated ${task} OK"

  "${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.static_checks \
    --xml "${tree}" \
    --yaml "${config}" >/dev/null
done

MODEL_TREE="/tmp/generated_make_sandwich_model.xml"
MODEL_CONFIG="/tmp/generated_make_sandwich_model_bt.yaml"
"${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.generate \
  --task make_sandwich \
  --planner model-response \
  --model-response-file tests/assets/vlm_planner/make_sandwich_valid.json \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_sandwich_executor.yaml \
  --out-tree "${MODEL_TREE}" \
  --out-config "${MODEL_CONFIG}" >/dev/null
echo "generated make_sandwich model-response OK"

"${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.static_checks \
  --xml "${MODEL_TREE}" \
  --yaml "${MODEL_CONFIG}" >/dev/null
echo "XML/YAML blackboard keys OK"

"${PYTHON_CMD[@]}" -m pytest \
  tests/lerobot_bt/test_bt_generation_cli.py \
  tests/lerobot_bt/test_bt_generation_all_static_tasks.py \
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
