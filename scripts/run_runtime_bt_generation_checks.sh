#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
read -r -a PYTHON_CMD <<< "${PYTHON_BIN}"
OUTPUT_ROOT="${OUTPUT_ROOT:-$(mktemp -d -t lerobot-runtime-bt-generation.XXXXXX)}"

REGISTRY="src/lerobot_bt_python/bt_generation/skills_registry.yaml"
EXECUTOR="src/lerobot_bt_python/make_sandwich_executor.yaml"
VALID_RESPONSE="tests/assets/vlm_planner/make_sandwich_valid.json"

cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}"

if ! command -v "${PYTHON_CMD[0]}" >/dev/null 2>&1; then
  if [[ "${PYTHON_BIN}" == "python" ]] && command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=(python3)
  else
    echo "ERROR: PYTHON_BIN command not found: ${PYTHON_BIN}" >&2
    exit 2
  fi
fi

mkdir -p "${OUTPUT_ROOT}/fixtures" "${OUTPUT_ROOT}/logs"

log_path() {
  local name="$1"
  printf '%s/logs/%s.log' "${OUTPUT_ROOT}" "${name}"
}

contains_log() {
  local file="$1"
  local needle="$2"
  if command -v rg >/dev/null 2>&1; then
    rg --fixed-strings --quiet -- "${needle}" "${file}"
  else
    grep -Fq -- "${needle}" "${file}"
  fi
}

run_success() {
  local name="$1"
  shift
  local log
  log="$(log_path "${name}")"
  if "$@" >"${log}" 2>&1; then
    echo "PASS ${name}"
    return 0
  fi
  echo "FAIL ${name}; command was expected to pass" >&2
  sed -n '1,160p' "${log}" >&2
  exit 1
}

run_failure() {
  local name="$1"
  local expected="$2"
  shift 2
  local log
  log="$(log_path "${name}")"
  set +e
  "$@" >"${log}" 2>&1
  local status=$?
  set -e
  if [[ ${status} -eq 0 ]]; then
    echo "FAIL ${name}; command unexpectedly passed" >&2
    sed -n '1,160p' "${log}" >&2
    exit 1
  fi
  if ! contains_log "${log}" "${expected}"; then
    echo "FAIL ${name}; expected log fragment not found: ${expected}" >&2
    sed -n '1,160p' "${log}" >&2
    exit 1
  fi
  echo "PASS rejected ${name}"
}

assert_file() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    echo "FAIL missing expected file: ${path}" >&2
    exit 1
  fi
}

generate_args() {
  local planner="$1"
  local output_dir="$2"
  shift 2
  "${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.generate \
    --task make_sandwich \
    --planner "${planner}" \
    --registry "${REGISTRY}" \
    --executor-yaml "${EXECUTOR}" \
    --output-dir "${output_dir}" \
    "$@"
}

check_static() {
  local output_dir="$1"
  run_success "static_check_$(basename "${output_dir}")" \
    "${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.static_checks \
      --xml "${output_dir}/trees/make_sandwich.xml" \
      --yaml "${output_dir}/config/make_sandwich_bt.yaml"
}

write_fixture() {
  local name="$1"
  local path="${OUTPUT_ROOT}/fixtures/${name}"
  shift
  printf '%s\n' "$@" >"${path}"
  printf '%s' "${path}"
}

echo "Runtime BT generation offline checks"
echo "repo: ${REPO_ROOT}"
echo "output: ${OUTPUT_ROOT}"
echo

test_a_dir="${OUTPUT_ROOT}/test_a_template"
run_success "test_a_template" generate_args template "${test_a_dir}"
assert_file "${test_a_dir}/trees/make_sandwich.xml"
assert_file "${test_a_dir}/config/make_sandwich_bt.yaml"
assert_file "${test_a_dir}/manifests/make_sandwich_manifest.json"
check_static "${test_a_dir}"

test_b_dir="${OUTPUT_ROOT}/test_b_model_response"
run_success "test_b_model_response" \
  generate_args model-response "${test_b_dir}" --model-response-file "${VALID_RESPONSE}"
assert_file "${test_b_dir}/plans/make_sandwich_linear_ir.json"
assert_file "${test_b_dir}/trees/make_sandwich.xml"
assert_file "${test_b_dir}/config/make_sandwich_bt.yaml"
assert_file "${test_b_dir}/raw_model_responses/make_sandwich_raw_response.json"
assert_file "${test_b_dir}/manifests/make_sandwich_manifest.json"
run_success "test_b_plan_json" \
  "${PYTHON_CMD[@]}" -m json.tool "${test_b_dir}/plans/make_sandwich_linear_ir.json"
run_success "test_b_raw_json" \
  "${PYTHON_CMD[@]}" -m json.tool "${test_b_dir}/raw_model_responses/make_sandwich_raw_response.json"
check_static "${test_b_dir}"

prose_json="$(
  write_fixture bad_prose_json.txt \
    "Here is the plan:" \
    "$(cat "${VALID_RESPONSE}")"
)"

bad_order="$(
  write_fixture bad_order.json \
    "{" \
    "  \"task_name\": \"make_sandwich\"," \
    "  \"steps\": [" \
    "    {\"kind\": \"vlm_gate\", \"name\": \"initial_scene_ready\"}," \
    "    {\"kind\": \"robot_skill\", \"name\": \"place_first_toast\"}," \
    "    {\"kind\": \"human_step\", \"name\": \"pour_ingredient\"}," \
    "    {\"kind\": \"vlm_gate\", \"name\": \"ingredient_poured\"}," \
    "    {\"kind\": \"robot_skill\", \"name\": \"place_second_toast\"}," \
    "    {\"kind\": \"vlm_gate\", \"name\": \"second_toast_placed\"}," \
    "    {\"kind\": \"vlm_gate\", \"name\": \"make_sandwich.task_complete\"}" \
    "  ]" \
    "}"
)"

bad_extra_step="$(
  write_fixture bad_extra_step.json \
    "{" \
    "  \"task_name\": \"make_sandwich\"," \
    "  \"steps\": [" \
    "    {\"kind\": \"vlm_gate\", \"name\": \"initial_scene_ready\"}," \
    "    {\"kind\": \"robot_skill\", \"name\": \"place_first_toast\"}," \
    "    {\"kind\": \"human_step\", \"name\": \"pour_ingredient\"}," \
    "    {\"kind\": \"vlm_gate\", \"name\": \"ingredient_poured\"}," \
    "    {\"kind\": \"robot_skill\", \"name\": \"place_second_toast\"}," \
    "    {\"kind\": \"vlm_gate\", \"name\": \"second_toast_placed\"}," \
    "    {\"kind\": \"vlm_gate\", \"name\": \"make_sandwich.task_complete\"}," \
    "    {\"kind\": \"vlm_gate\", \"name\": \"initial_scene_ready\"}" \
    "  ]" \
    "}"
)"

bad_raw_xml="$(
  write_fixture bad_raw_xml.json \
    "{" \
    "  \"task_name\": \"make_sandwich\"," \
    "  \"steps\": [" \
    "    {\"kind\": \"vlm_gate\", \"name\": \"initial_scene_ready\", \"raw_xml\": \"Sequence\"}," \
    "    {\"kind\": \"robot_skill\", \"name\": \"place_first_toast\"}," \
    "    {\"kind\": \"human_step\", \"name\": \"pour_ingredient\"}," \
    "    {\"kind\": \"vlm_gate\", \"name\": \"ingredient_poured\"}," \
    "    {\"kind\": \"robot_skill\", \"name\": \"place_second_toast\"}," \
    "    {\"kind\": \"vlm_gate\", \"name\": \"second_toast_placed\"}," \
    "    {\"kind\": \"vlm_gate\", \"name\": \"make_sandwich.task_complete\"}" \
    "  ]" \
    "}"
)"

run_failure "test_c_xml_response" "XML-like content is not allowed" \
  generate_args model-response "${OUTPUT_ROOT}/test_c_xml" \
    --model-response-file tests/assets/vlm_planner/make_sandwich_bad_xml_response.txt

run_failure "test_c_prose_json" "Planner response is not valid JSON" \
  generate_args model-response "${OUTPUT_ROOT}/test_c_prose" \
    --model-response-file "${prose_json}"

run_failure "test_c_invented_skill" "not present in the registry" \
  generate_args model-response "${OUTPUT_ROOT}/test_c_invented_skill" \
    --model-response-file tests/assets/vlm_planner/make_sandwich_bad_invented_skill.json

run_failure "test_c_wrong_kind" "in the registry, not" \
  generate_args model-response "${OUTPUT_ROOT}/test_c_wrong_kind" \
    --model-response-file tests/assets/vlm_planner/make_sandwich_bad_wrong_executor.json

run_failure "test_c_changed_order" "does not match canonical task sequence" \
  generate_args model-response "${OUTPUT_ROOT}/test_c_changed_order" \
    --model-response-file "${bad_order}"

run_failure "test_c_missing_step" "does not match canonical task sequence" \
  generate_args model-response "${OUTPUT_ROOT}/test_c_missing_step" \
    --model-response-file tests/assets/vlm_planner/make_sandwich_bad_missing_final_gate.json

run_failure "test_c_extra_step" "does not match canonical task sequence" \
  generate_args model-response "${OUTPUT_ROOT}/test_c_extra_step" \
    --model-response-file "${bad_extra_step}"

run_failure "test_c_raw_xml_field" "raw_xml" \
  generate_args model-response "${OUTPUT_ROOT}/test_c_raw_xml" \
    --model-response-file "${bad_raw_xml}"

echo
echo "All offline runtime BT generation checks passed."
echo "Logs and artifacts are in ${OUTPUT_ROOT}"
