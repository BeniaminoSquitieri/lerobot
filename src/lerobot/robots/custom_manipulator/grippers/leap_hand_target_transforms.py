from __future__ import annotations

import numpy as np

QUEST_PALM_FROM_LEAP_PALM = np.array([
    [0.0, -1.0, 0.0],
    [0.0, 0.0, 1.0],
    [-1.0, 0.0, 0.0],
])
RETARGETING_FRAME_FROM_LEAP_PALM = np.array([
    [0.0, 0.0, -1.0],
    [0.0, 1.0, 0.0],
    [1.0, 0.0, 0.0],
])


def transform_targets_for_leap_retargeting(
    target_positions: dict[str, list[float]],
    quest_palm_from_leap_palm: np.ndarray,
) -> dict[str, list[float]]:

    wrist = target_positions["wrist"]

    wrist_relative_targets = {
        name: pos - wrist
        for name, pos in target_positions.items()
    }

    retargeting_frame_from_quest_palm = (
        RETARGETING_FRAME_FROM_LEAP_PALM @ quest_palm_from_leap_palm.T
    )

    return {
        name: retargeting_frame_from_quest_palm @ pos
        for name, pos in wrist_relative_targets.items()
    }
