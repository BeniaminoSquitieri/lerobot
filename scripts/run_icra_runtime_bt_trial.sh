#!/usr/bin/env bash
#
# Run one ICRA runtime BT trial through the SAFE runtime path:
#   VLM/ROS service -> Linear IR JSON -> lerobot strict validation -> XML/YAML
#   -> BehaviorTree.CPP runner.
#
# This script never uses the direct-XML offline unsafe baseline. It always uses
# the constrained linear IR planner (planner=ros-service,
# planner_label=constrained_linear_ir).
#
# Usage:
#   scripts/run_icra_runtime_bt_trial.sh <task> <dry_run_no_run|robot_live>
#
# Conditions:
#   dry_run_no_run  Generate + validate artifacts, print runner command, do not
#                   execute the ROS runner (condition_label=dry_run_no_run).
#   robot_live      Generate + validate, then execute the ROS runner on the
#                   real robot (condition_label=robot_live).
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
read -r -a PYTHON_CMD <<< "${PYTHON_BIN}"

# Centralised ROS 2 + CycloneDDS env (ROS_DOMAIN_ID / RMW_IMPLEMENTATION /
# CYCLONEDDS_URI) so trials work without manual exports on every machine.
# shellcheck disable=SC1091
[ -f "${REPO_ROOT}/ros_env.sh" ] && source "${REPO_ROOT}/ros_env.sh"

usage() {
  echo "Usage: scripts/run_icra_runtime_bt_trial.sh <task> <dry_run_no_run|robot_live>" >&2
  echo "  tasks: make_sandwich make_coffee set_breakfast_table prepare_picnic_bag items_in_drawer" >&2
}

if [[ $# -ne 2 ]]; then
  usage
  exit 2
fi

TASK="$1"
CONDITION="$2"

# Map each known task to its executor YAML (used for consistency checks).
case "${TASK}" in
  make_sandwich)        EXECUTOR="src/lerobot_bt_python/make_sandwich_executor.yaml" ;;
  make_coffee)          EXECUTOR="src/lerobot_bt_python/make_coffee_executor.yaml" ;;
  set_breakfast_table)  EXECUTOR="src/lerobot_bt_python/set_breakfast_table_executor.yaml" ;;
  prepare_picnic_bag)   EXECUTOR="src/lerobot_bt_python/prepare_picnic_bag_executor.yaml" ;;
  items_in_drawer)      EXECUTOR="src/lerobot_bt_python/items_in_drawer_executor.yaml" ;;
  *)
    echo "ERROR: unknown task '${TASK}'." >&2
    usage
    exit 2
    ;;
esac

case "${CONDITION}" in
  dry_run_no_run|robot_live) ;;
  *)
    echo "ERROR: condition must be 'dry_run_no_run' or 'robot_live'." >&2
    usage
    exit 2
    ;;
esac

cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}"

REGISTRY="src/lerobot_bt_python/bt_generation/skills_registry.yaml"
OUTPUT_DIR="generated_bt"
LOG_PATH="${OUTPUT_DIR}/experiments/trials.jsonl"
PLANNER="ros-service"
PLANNER_LABEL="constrained_linear_ir"

# The robot_live condition needs a sourced ROS environment with the built
# workspace. Fail clearly instead of producing a confusing ros2 error.
if [[ "${CONDITION}" == "robot_live" ]]; then
  if ! command -v ros2 >/dev/null 2>&1; then
    echo "ERROR: ros2 not found. Source ROS and the built workspace first:" >&2
    echo "  source /opt/ros/\${ROS_DISTRO}/setup.bash" >&2
    echo "  source install/setup.bash" >&2
    exit 3
  fi
fi

GEN_AND_RUN_ARGS=(
  --task "${TASK}"
  --planner "${PLANNER}"
  --registry "${REGISTRY}"
  --executor-yaml "${EXECUTOR}"
  --output-dir "${OUTPUT_DIR}"
  --experiment-log "${LOG_PATH}"
  --planner-label "${PLANNER_LABEL}"
  --condition-label "${CONDITION}"
)

if [[ "${CONDITION}" == "dry_run_no_run" ]]; then
  GEN_AND_RUN_ARGS+=(--no-run)
fi

echo "Running ICRA trial: task=${TASK} condition=${CONDITION} planner_label=${PLANNER_LABEL}"
echo "Safe runtime path only (no direct-XML baseline)."

set +e
RUN_OUTPUT="$("${PYTHON_CMD[@]}" -m lerobot_bt_python.bt_generation.generate_and_run "${GEN_AND_RUN_ARGS[@]}" 2>&1)"
RUN_STATUS=$?
set -e

echo "${RUN_OUTPUT}"

# Recover the trial id printed by generate_and_run for the annotation step.
TRIAL_ID="$(printf '%s\n' "${RUN_OUTPUT}" | sed -n 's/^trial_id: //p' | head -n1)"

if [[ ${RUN_STATUS} -ne 0 ]]; then
  echo "WARNING: generate_and_run exited with status ${RUN_STATUS}." >&2
  echo "Experiment log (failures included): ${LOG_PATH}" >&2
fi

# Summarize after the run so trials.csv / summary.csv stay up to date.
"${PYTHON_CMD[@]}" scripts/summarize_runtime_bt_experiments.py --jsonl "${LOG_PATH}" || true

echo ""
echo "Next step: annotate this trial after observing it:"
if [[ -n "${TRIAL_ID}" ]]; then
  echo "  ${PYTHON_BIN} scripts/annotate_runtime_bt_trial.py \\"
  echo "    --jsonl ${LOG_PATH} \\"
  echo "    --trial-id ${TRIAL_ID} \\"
  echo "    --task-success success --outcome-label completed --failure-category none"
else
  echo "  (trial_id not captured; inspect ${LOG_PATH} for the trial_id)"
fi

exit "${RUN_STATUS}"
