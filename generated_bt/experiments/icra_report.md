# Runtime BT ICRA experiment report

## Overview

- Total trials: 10
- Annotated trials: 3

## Conditions tested

| task | planner_label | condition_label | trials |
| --- | --- | --- | --- |
| make_sandwich | template | offline_template_no_run | 2 |
| make_sandwich | constrained_linear_ir | robot_live | 4 |
| make_coffee | constrained_linear_ir | robot_live | 1 |
| set_breakfast_table | constrained_linear_ir | robot_live | 1 |
| prepare_picnic_bag | constrained_linear_ir | robot_live | 1 |
| items_in_drawer | constrained_linear_ir | robot_live | 1 |

## Summary

| task_name | planner_label | condition_label | count_trials | generation_success_rate | runner_success_rate | task_success_rate | annotated_trial_count | parse_failure_count | validation_failure_count | static_check_failure_count | runner_failure_count | top_failure_categories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| make_sandwich | template | offline_template_no_run | 2 | 1.0000 |  |  | 0 | 0 | 0 | 0 | 0 |  |
| make_sandwich | constrained_linear_ir | robot_live | 4 | 0.5000 | 1.0000 | 0.3333 | 3 | 0 | 0 | 0 | 0 | service_unavailable:2 |
| make_coffee | constrained_linear_ir | robot_live | 1 | 1.0000 | 1.0000 |  | 0 | 0 | 0 | 0 | 0 |  |
| set_breakfast_table | constrained_linear_ir | robot_live | 1 | 1.0000 | 1.0000 |  | 0 | 0 | 0 | 0 | 0 |  |
| prepare_picnic_bag | constrained_linear_ir | robot_live | 1 | 1.0000 | 1.0000 |  | 0 | 0 | 0 | 0 | 0 |  |
| items_in_drawer | constrained_linear_ir | robot_live | 1 | 1.0000 | 1.0000 |  | 0 | 0 | 0 | 0 | 0 |  |

## Failure categories

| failure_category | count |
| --- | --- |
| service_unavailable | 2 |

## Trials

| trial_id | task_name | planner_label | condition_label | generation_success | runner_success | task_success | outcome_label | failure_category |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| make_sandwich__template__20260601T154002__78b6c636 | make_sandwich | template | offline_template_no_run | True |  |  |  |  |
| make_sandwich__template__20260601T154036__a77c1f27 | make_sandwich | template | offline_template_no_run | True |  |  |  |  |
| make_sandwich__ros-service__20260601T154514__a9d21c87 | make_sandwich | constrained_linear_ir | robot_live | False |  | failure | aborted | service_unavailable |
| make_sandwich__ros-service__20260601T155336__0c77a9df | make_sandwich | constrained_linear_ir | robot_live | False |  | failure | aborted | service_unavailable |
| make_sandwich__ros-service__20260601T160013__8f93444d | make_sandwich | constrained_linear_ir | robot_live | True | True | success | completed | none |
| make_sandwich__ros-service__20260601T160226__d0249ae8 | make_sandwich | constrained_linear_ir | robot_live | True | True |  |  |  |
| make_coffee__ros-service__20260601T160230__7eb0c492 | make_coffee | constrained_linear_ir | robot_live | True | True |  |  |  |
| set_breakfast_table__ros-service__20260601T160234__e5e308f0 | set_breakfast_table | constrained_linear_ir | robot_live | True | True |  |  |  |
| prepare_picnic_bag__ros-service__20260601T160240__e65f6d73 | prepare_picnic_bag | constrained_linear_ir | robot_live | True | True |  |  |  |
| items_in_drawer__ros-service__20260601T160245__f3c44304 | items_in_drawer | constrained_linear_ir | robot_live | True | True |  |  |  |

## Notes

- Direct XML is an offline unsafe baseline only and is not executable through the safe runtime path.
