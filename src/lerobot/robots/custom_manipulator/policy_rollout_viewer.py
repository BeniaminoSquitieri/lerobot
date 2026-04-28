from typing import Any

import rerun as rr
from scipy.spatial.transform import Rotation as R

from lerobot.policies.utils import make_robot_action
from lerobot.processor import PolicyAction, PolicyProcessorPipeline

HOME_ROT = R.from_rotvec([3.141592653589793, 0.0, 0.0])
ROOT_FRAME = "tf#/panda/panda_link0"
TRAJECTORY_PATH = "/target_eef/policy_rollout/trajectory"
FINAL_FRAME_PATH = "/target_eef/policy_rollout/final_frame"


def log_policy_rollout(
    current_action: PolicyAction,
    queued_actions: list[PolicyAction],
    dataset_features: dict[str, dict[str, Any]],
    postprocessor: PolicyProcessorPipeline[PolicyAction, PolicyAction],
) -> None:
    rollout_actions = [make_robot_action(current_action, dataset_features)]
    for queued_action in queued_actions:
        rollout_actions.append(make_robot_action(postprocessor(queued_action), dataset_features))

    positions = [
        [
            float(action["position.x"]),
            float(action["position.y"]),
            float(action["position.z"]),
        ]
        for action in rollout_actions
    ]

    if len(positions) > 1:
        rr.log(
            TRAJECTORY_PATH,
            rr.LineStrips3D([positions], colors=[[255, 80, 80]], radii=0.002),
            rr.CoordinateFrame(ROOT_FRAME),
        )

    final_action = rollout_actions[-1]
    final_orientation = [
        float(final_action["orientation.x"]),
        float(final_action["orientation.y"]),
        float(final_action["orientation.z"]),
    ]
    rr.log(
        FINAL_FRAME_PATH,
        rr.Arrows3D(
            origins=[positions[-1]] * 3,
            vectors=(0.04 * (HOME_ROT * R.from_rotvec(final_orientation)).as_matrix().T).tolist(),
            colors=[[255, 0, 0], [0, 255, 0], [0, 0, 255]],
            radii=0.002,
        ),
        rr.CoordinateFrame(ROOT_FRAME),
    )
