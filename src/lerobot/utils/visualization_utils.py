# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numbers
import os
from pathlib import Path
from typing import Any

import numpy as np

from lerobot.model.urdf_utils import prepare_urdf_for_placo, prepare_urdf_for_rerun
from lerobot.types import RobotAction, RobotObservation

from .constants import ACTION, ACTION_PREFIX, OBS_PREFIX, OBS_STR
from .import_utils import require_package


def init_rerun(
    session_name: str = "lerobot_control_loop", ip: str | None = None, port: int | None = None
) -> None:
    """
    Initializes the Rerun SDK for visualizing the control loop.

    Args:
        session_name: Name of the Rerun session.
        ip: Optional IP for connecting to a Rerun server.
        port: Optional port for connecting to a Rerun server.
    """

    require_package("rerun-sdk", extra="viz", import_name="rerun")
    import rerun as rr

    batch_size = os.getenv("RERUN_FLUSH_NUM_BYTES", "1048576")
    os.environ["RERUN_FLUSH_NUM_BYTES"] = batch_size
    rr.init(session_name)
    memory_limit = os.getenv("LEROBOT_RERUN_MEMORY_LIMIT", "10%")
    if ip and port:
        rr.connect_grpc(url=f"rerun+http://{ip}:{port}/proxy")
    else:
        rr.spawn(memory_limit=memory_limit)


def shutdown_rerun() -> None:
    """Shuts down the Rerun SDK gracefully."""

    require_package("rerun-sdk", extra="viz", import_name="rerun")
    import rerun as rr

    rr.rerun_shutdown()


def _is_scalar(x):
    return isinstance(x, (float | numbers.Real | np.integer | np.floating)) or (
        isinstance(x, np.ndarray) and x.ndim == 0
    )


def _convert_joint_value_for_rerun(joint: Any, value: float) -> float:
    """Convert live joint values to the units expected by rerun's URDF joint transforms."""

    if getattr(joint, "joint_type", None) in {"revolute", "continuous"}:
        return float(np.deg2rad(value))
    return float(value)


_ERGOCUB_RERUN_TREES: dict[str, Any] = {}
_ERGOCUB_RERUN_STEPS: dict[str, int] = {}
_ERGOCUB_XELA_FINGER_FRAMES = {
    "left": {
        "thumb": "l_hand_thumb_3",
        "index": "l_hand_index_3",
        "middle": "l_hand_middle_2",
        "ring": "l_hand_ring_2",
        "pinky": "l_hand_pinkie_2",
    },
    "right": {
        "thumb": "r_hand_thumb_3",
        "index": "r_hand_index_3",
        "middle": "r_hand_middle_2",
        "ring": "r_hand_ring_2",
        "pinky": "r_hand_pinkie_2",
    },
}
_ERGOCUB_XELA_RERUN_SCALE = float(os.getenv("LEROBOT_ERGOCUB_XELA_RERUN_SCALE", "5e-5"))
_ERGOCUB_XELA_RERUN_RADIUS = float(os.getenv("LEROBOT_ERGOCUB_XELA_RERUN_RADIUS", "0.004"))
_ERGOCUB_XELA_RERUN_ORIGIN = [0.0, 0.0, -0.035]
_ERGOCUB_XELA_RERUN_ROTATION = np.array(
    [
        [0.0, -1.0, 0.0],
        [0.0, 0.0, 1.0],
        [-1.0, 0.0, 0.0],
    ],
    dtype=float,
)


def _get_ergocub_xela_visualization_scale(robot: Any | None) -> np.ndarray:
    default_scale = np.array([_ERGOCUB_XELA_RERUN_SCALE] * 3, dtype=float)
    if robot is None or not hasattr(robot, "config"):
        return default_scale

    scale = getattr(robot.config, "xela_force_visualization_scale", None)
    if scale is None:
        return default_scale

    try:
        scale_arr = np.asarray(scale, dtype=float).reshape(-1)
    except (TypeError, ValueError):
        return default_scale

    if scale_arr.size == 1:
        return np.repeat(scale_arr, 3)
    if scale_arr.size == 3:
        return scale_arr
    return default_scale


def _log_ergocub_xela_forces(observation: RobotObservation | None, robot_name: str, robot: Any | None = None) -> None:
    if not observation:
        return

    require_package("rerun-sdk", extra="viz", import_name="rerun")
    import rerun as rr

    visualization_scale = _get_ergocub_xela_visualization_scale(robot)

    for side, frame_names in _ERGOCUB_XELA_FINGER_FRAMES.items():
        for finger_name, frame_name in frame_names.items():
            force = np.array(
                [float(observation.get(f"{side}_xela.{finger_name}.force.{axis}", 0.0)) for axis in ("x", "y", "z")],
                dtype=float,
            )
            display_force = _ERGOCUB_XELA_RERUN_ROTATION @ force
            magnitude = float(np.linalg.norm(force))
            if magnitude <= 0.0:
                continue

            rr.log(
                f"/{robot_name}/xela/{side}/{finger_name}_force",
                rr.Arrows3D(
                    origins=[_ERGOCUB_XELA_RERUN_ORIGIN],
                    vectors=[(visualization_scale * display_force).tolist()],
                    colors=[[255, 80, 80]],
                    radii=_ERGOCUB_XELA_RERUN_RADIUS,
                    labels=[f"|F|={magnitude:.1f}"],
                    show_labels=True,
                ),
                rr.CoordinateFrame(f"tf#/{robot_name}/{frame_name}"),
            )


def _should_log_ergocub_rerun_scalar(key: str) -> bool:
    if "_xela" not in key:
        return True

    parts = key.split(".")
    if len(parts) != 4:
        return False

    xela_name, _finger_name, taxel_name, axis_name = parts
    return xela_name.endswith("_xela") and taxel_name.startswith("taxel_") and axis_name in {"x", "y", "z"}


def log_rerun_data(
    observation: RobotObservation | None = None,
    action: RobotAction | None = None,
    compress_images: bool = False,
    robot: Any | None = None,
) -> None:
    """
    Logs observation and action data to Rerun for real-time visualization.

    This function iterates through the provided observation and action dictionaries and sends their contents
    to the Rerun viewer. It handles different data types appropriately:
    - Scalars values (floats, ints) are logged as `rr.Scalars`.
    - 3D NumPy arrays that resemble images (e.g., with 1, 3, or 4 channels first) are transposed
      from CHW to HWC format, (optionally) compressed to JPEG and logged as `rr.Image` or `rr.EncodedImage`.
    - 1D NumPy arrays are logged as a series of individual scalars, with each element indexed.
    - Other multi-dimensional arrays are flattened and logged as individual scalars.

    Keys are automatically namespaced with "observation." or "action." if not already present.

    Args:
        observation: An optional dictionary containing observation data to log.
        action: An optional dictionary containing action data to log.
        compress_images: Whether to compress images before logging to save bandwidth & memory in exchange for cpu and quality.
        robot: Optional robot handle accepted for API compatibility with specialized loggers.
    """

    del robot

    require_package("rerun-sdk", extra="viz", import_name="rerun")
    import rerun as rr

    if observation:
        for k, v in observation.items():
            if v is None:
                continue
            key = k if str(k).startswith(OBS_PREFIX) else f"{OBS_STR}.{k}"

            if _is_scalar(v):
                rr.log(key, rr.Scalars(float(v)))
            elif isinstance(v, np.ndarray):
                arr = v
                # Convert CHW -> HWC when needed
                if arr.ndim == 3 and arr.shape[0] in (1, 3, 4) and arr.shape[-1] not in (1, 3, 4):
                    arr = np.transpose(arr, (1, 2, 0))
                if arr.ndim == 1:
                    for i, vi in enumerate(arr):
                        rr.log(f"{key}_{i}", rr.Scalars(float(vi)))
                else:
                    img_entity = rr.Image(arr).compress() if compress_images else rr.Image(arr)
                    rr.log(key, entity=img_entity, static=True)

    if action:
        for k, v in action.items():
            if v is None:
                continue
            key = k if str(k).startswith(ACTION_PREFIX) else f"{ACTION}.{k}"

            if _is_scalar(v):
                rr.log(key, rr.Scalars(float(v)))
            elif isinstance(v, np.ndarray):
                if v.ndim == 1:
                    for i, vi in enumerate(v):
                        rr.log(f"{key}_{i}", rr.Scalars(float(vi)))
                else:
                    # Fall back to flattening higher-dimensional arrays
                    flat = v.flatten()
                    for i, vi in enumerate(flat):
                        rr.log(f"{key}_{i}", rr.Scalars(float(vi)))


def log_rerun_data_ergocub(
    observation: RobotObservation | None = None,
    action: RobotAction | None = None,
    compress_images: bool = False,
    robot: Any | None = None,
) -> None:
    """ErgoCub-specific visualization hook.

    Logs the robot URDF once and updates joint transforms when available,
    in addition to the generic scalar/image streams.
    """

    require_package("rerun-sdk", extra="viz", import_name="rerun")
    import rerun as rr
    from rerun.urdf import UrdfTree

    if robot is not None and getattr(robot, "urdf_path", None):
        raw_urdf_path = str(Path(robot.urdf_path).expanduser().resolve())
        urdf_path = prepare_urdf_for_rerun(raw_urdf_path)
        if urdf_path not in _ERGOCUB_RERUN_TREES:
            entity_path_prefix = robot.name
            frame_prefix = f"tf#/{robot.name}/"
            urdf_tree = UrdfTree.from_file_path(
                urdf_path,
                entity_path_prefix=entity_path_prefix,
                frame_prefix=frame_prefix,
            )
            urdf_tree.log_urdf_to_recording()
            _ERGOCUB_RERUN_TREES[urdf_path] = urdf_tree
            _ERGOCUB_RERUN_STEPS[urdf_path] = 0

        urdf_tree = _ERGOCUB_RERUN_TREES[urdf_path]
        _ERGOCUB_RERUN_STEPS[urdf_path] += 1
        rr.set_time("step", sequence=_ERGOCUB_RERUN_STEPS[urdf_path])

        joint_states: dict[str, float] = {}
        if hasattr(robot, "bus") and hasattr(robot.bus, "get_latest_joint_states"):
            joint_states = robot.bus.get_latest_joint_states()

        for i, joint in enumerate(urdf_tree.joints()):
            if joint.name not in joint_states:
                continue

            value = _convert_joint_value_for_rerun(joint, joint_states[joint.name])
            rr.log(f"{robot.name}/transforms/{joint.name}", joint.compute_transform(value))
            rr.log(f"/{robot.name}/joints/{joint.name}", rr.Scalars([value]))

    if robot is not None:
        _log_ergocub_xela_forces(observation=observation, robot_name=robot.name, robot=robot)

    filtered_observation = None
    if observation is not None:
        filtered_observation = {
            key: value for key, value in observation.items() if _should_log_ergocub_rerun_scalar(str(key))
        }

    log_rerun_data(observation=filtered_observation, action=action, compress_images=compress_images)
