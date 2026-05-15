#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
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

import importlib
import logging
import pickle  # nosec B403
import threading
import time
from dataclasses import asdict
from pathlib import Path
from pprint import pformat
from threading import Event, Lock, Thread
from typing import Any, List

import numpy as np
from queue import Queue

import grpc
import torch
from pyparsing import Optional

from lerobot.async_inference.configs import get_aggregate_function
from lerobot.async_inference.helpers import RemotePolicyConfig, TimedAction, TimedObservation
from lerobot.configs import parser
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.pipeline_features import aggregate_pipeline_dataset_features, create_initial_features
from lerobot.utils.feature_utils import combine_feature_dicts, build_dataset_frame
from lerobot.datasets.video_utils import VideoEncodingManager
from lerobot.processor import ProcessorStepRegistry, RobotAction, RobotObservation, RobotProcessorPipeline
from lerobot.processor.converters import (
    observation_to_transition,
    robot_action_observation_to_transition,
    transition_to_observation,
    transition_to_robot_action,
)
from lerobot.robots.custom_manipulator.custom_manipulator import CustomManipulator
from lerobot.robots.custom_manipulator.episode_start_overlay import make_episode_start_overlay
from lerobot.robots.custom_manipulator.policy_rollout_viewer import log_policy_rollout
from lerobot.robots.custom_manipulator.record_config import (
    RecordConfig,
    RosEnvironmentStateConfig,
    RosObservationTopicConfig,
    get_missing_remote_policy_source_message,
    get_missing_policy_source_message,
    get_remote_policy_loading_source,
    get_policy_loading_source,
)
from lerobot.common.control_utils import (
    init_keyboard_listener,
    is_headless,
    sanity_check_dataset_name,
    sanity_check_dataset_robot_compatibility,
)
from lerobot.utils.utils import log_say, init_logging
from lerobot.utils.device_utils import get_safe_torch_device
from lerobot.utils.visualization_utils import init_rerun, log_rerun_data
from lerobot.utils.constants import ACTION, HF_LEROBOT_HOME, OBS_ENV_STATE, OBS_STR
from lerobot.utils.robot_utils import precise_sleep
from lerobot.policies.utils import make_robot_action
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.processor.rename_processor import rename_stats
from lerobot.datasets.image_writer import safe_stop_image_writer
from lerobot.teleoperators import Teleoperator, make_teleoperator_from_config
from lerobot.policies.pretrained import PreTrainedPolicy
from lerobot.processor import PolicyAction, PolicyProcessorPipeline
from lerobot.common.control_utils import predict_action
from lerobot.transport import services_pb2, services_pb2_grpc
from lerobot.transport.utils import grpc_channel_options, send_bytes_in_chunks
from typing import Any, List

import rerun as rr
from lerobot.utils.rotation import Rotation as R

try:
    import rclpy  # type: ignore
    from rclpy.executors import SingleThreadedExecutor  # type: ignore
    from rclpy.node import Node  # type: ignore

    _ros_import_error: Exception | None = None
except Exception as e:
    rclpy = None  # type: ignore[assignment]
    SingleThreadedExecutor = None  # type: ignore[assignment,misc]
    Node = None  # type: ignore[assignment,misc]
    _ros_import_error = e

# import debugpy
# debugpy.listen(5678)
# print('Waiting for client...')
# debugpy.wait_for_client()


def _normalize_ros_message_type_path(message_type: str) -> str:
    if "/msg/" in message_type:
        return message_type.replace("/msg/", ".msg.")
    if message_type.count("/") == 2:
        package, namespace, name = message_type.split("/")
        return f"{package}.{namespace}.{name}"
    if message_type.count("/") == 1:
        package, name = message_type.split("/")
        return f"{package}.msg.{name}"
    return message_type


def _load_ros_message_type(message_type: str) -> type[Any]:
    normalized = _normalize_ros_message_type_path(message_type)
    module_path, class_name = normalized.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _extract_ros_message_value(message: Any, field_path: str) -> float:
    value = message
    for field_name in field_path.split("."):
        value = getattr(value, field_name)
    return float(value)


def _build_ros_env_state_dataset_features(config: RosEnvironmentStateConfig) -> dict[str, dict]:
    if not config.enabled:
        return {}

    source_keys = config.ordered_output_keys
    return {
        OBS_ENV_STATE: {
        "dtype": "float32",
        "shape": (len(source_keys),),
        "names": source_keys,
        }
    }


class _RosEnvironmentStateReader:
    def __init__(self, config: RosEnvironmentStateConfig):
        self.config = config
        self._latest_values: dict[str, np.float32] = {}
        self._lock = Lock()
        self._stop_event = Event()
        self._spin_thread: Thread | None = None
        self._executor = None
        self._node = None
        self._subscriptions: list[Any] = []

    def _make_callback(self, topic_config: RosObservationTopicConfig):
        def _callback(message: Any) -> None:
            extracted = {
                key: np.float32(_extract_ros_message_value(message, field_path))
                for key, field_path in zip(topic_config.output_keys, topic_config.value_fields, strict=True)
            }
            with self._lock:
                self._latest_values.update(extracted)

        return _callback

    @property
    def is_ready(self) -> bool:
        with self._lock:
            return all(key in self._latest_values for key in self.config.ordered_output_keys)

    def connect(self) -> None:
        if not self.config.enabled:
            return
        if rclpy is None or Node is None or SingleThreadedExecutor is None:
            raise ImportError("ROS2 support is unavailable in this environment.") from _ros_import_error

        if not rclpy.ok():
            rclpy.init(args=None)

        self._node = Node("lerobot_custom_manipulator_env_state")
        self._executor = SingleThreadedExecutor()
        self._executor.add_node(self._node)

        for topic_config in self.config.topics:
            message_type = _load_ros_message_type(topic_config.message_type)
            subscription = self._node.create_subscription(
                message_type,
                topic_config.topic,
                self._make_callback(topic_config),
                topic_config.queue_size,
            )
            self._subscriptions.append(subscription)

        self._spin_thread = Thread(
            target=self._spin,
            name="lerobot_ros_env_state",
            daemon=True,
        )
        self._spin_thread.start()

    def _spin(self) -> None:
        if self._executor is None:
            return
        while not self._stop_event.is_set():
            self._executor.spin_once(timeout_sec=0.1)

    def wait_until_ready(self, timeout_s: float) -> None:
        deadline = time.perf_counter() + timeout_s
        while time.perf_counter() < deadline:
            if self.is_ready:
                return
            time.sleep(0.05)

        missing = [key for key in self.config.ordered_output_keys if key not in self._latest_values]
        raise TimeoutError(
            "Timed out waiting for ROS environment-state topics. "
            f"Missing values for keys: {missing}."
        )

    def get_latest_values(self) -> dict[str, np.float32]:
        with self._lock:
            missing = [key for key in self.config.ordered_output_keys if key not in self._latest_values]
            if missing:
                raise RuntimeError(
                    "ROS environment-state reader is missing required values "
                    f"for keys: {missing}."
                )
            return {key: self._latest_values[key] for key in self.config.ordered_output_keys}

    def try_get_latest_values(self) -> dict[str, np.float32] | None:
        with self._lock:
            if not all(key in self._latest_values for key in self.config.ordered_output_keys):
                return None
            return {key: self._latest_values[key] for key in self.config.ordered_output_keys}

    def disconnect(self) -> None:
        self._stop_event.set()
        if self._spin_thread is not None and self._spin_thread.is_alive():
            self._spin_thread.join(timeout=2.0)
        if self._node is not None:
            self._node.destroy_node()
            self._node = None
        if self._executor is not None:
            try:
                self._executor.shutdown()
            except Exception:
                pass
            self._executor = None
        self._subscriptions.clear()
class RemotePolicyClient:
    """Async remote policy client for custom manipulator recording."""

    def __init__(
        self,
        *,
        server_address: str,
        policy_type: str,
        pretrained_name_or_path: str,
        policy_device: str,
        client_device: str,
        lerobot_features: dict[str, dict],
        rename_map: dict[str, str],
        actions_per_chunk: int,
        chunk_size_threshold: float,
        aggregate_fn_name: str,
        fps: int,
    ):
        self.server_address = server_address
        self.policy_config = RemotePolicyConfig(
            policy_type=policy_type,
            pretrained_name_or_path=pretrained_name_or_path,
            lerobot_features=lerobot_features,
            actions_per_chunk=actions_per_chunk,
            device=policy_device,
            rename_map=rename_map,
        )
        self.client_device = client_device
        self.environment_dt = 1 / fps
        self.chunk_size_threshold = chunk_size_threshold
        self.aggregate_fn = get_aggregate_function(aggregate_fn_name)

        self.channel = grpc.insecure_channel(
            self.server_address, grpc_channel_options(initial_backoff=f"{self.environment_dt:.4f}s")
        )
        self.stub = services_pb2_grpc.AsyncInferenceStub(self.channel)

        self.shutdown_event = threading.Event()
        self.action_queue: Queue[TimedAction] = Queue()
        self.action_queue_lock = threading.Lock()
        self.latest_action_lock = threading.Lock()
        self.latest_action = -1
        self.action_chunk_size = -1
        self.must_go = threading.Event()
        self.must_go.set()
        self.action_queue_size: list[int] = []
        self.receiver_thread: threading.Thread | None = None

    def start(self) -> None:
        self._ready()
        self._configure_policy()
        self.shutdown_event.clear()
        self.receiver_thread = threading.Thread(target=self._receive_actions, daemon=True)
        self.receiver_thread.start()

    def stop(self) -> None:
        self.shutdown_event.set()
        self.channel.close()
        if self.receiver_thread is not None:
            self.receiver_thread.join(timeout=2)

    def reset(self) -> None:
        self._clear_queue()
        with self.latest_action_lock:
            self.latest_action = -1
        self.action_chunk_size = -1
        self.must_go.set()
        self._ready()

    def _ready(self) -> None:
        self.stub.Ready(services_pb2.Empty())

    def _configure_policy(self) -> None:
        policy_config_bytes = pickle.dumps(self.policy_config)
        self.stub.SendPolicyInstructions(services_pb2.PolicySetup(data=policy_config_bytes))

    def _clear_queue(self) -> None:
        with self.action_queue_lock:
            self.action_queue = Queue()

    def actions_available(self) -> bool:
        with self.action_queue_lock:
            return not self.action_queue.empty()

    def should_request_action(self) -> bool:
        with self.action_queue_lock:
            if self.action_chunk_size <= 0:
                return True
            queue_fraction = self.action_queue.qsize() / self.action_chunk_size
            return queue_fraction <= self.chunk_size_threshold

    def pop_action(self) -> torch.Tensor:
        with self.action_queue_lock:
            self.action_queue_size.append(self.action_queue.qsize())
            timed_action = self.action_queue.get_nowait()
        with self.latest_action_lock:
            self.latest_action = timed_action.get_timestep()
        return timed_action.get_action()

    def send_observation(self, observation: dict[str, Any], task: str | None) -> None:
        with self.latest_action_lock:
            latest_action = self.latest_action

        timed_observation = TimedObservation(
            timestamp=time.time(),
            observation={**observation, "task": task or ""},
            timestep=max(latest_action, 0),
        )

        with self.action_queue_lock:
            timed_observation.must_go = self.must_go.is_set() and self.action_queue.empty()

        payload = pickle.dumps(timed_observation)
        obs_iterator = send_bytes_in_chunks(
            payload,
            services_pb2.Observation,
            log_prefix="[CUSTOM_RECORD] Observation",
            silent=True,
        )
        self.stub.SendObservations(obs_iterator)

        if timed_observation.must_go:
            self.must_go.clear()

    def _aggregate_action_queues(self, incoming_actions: list[TimedAction]) -> None:
        future_action_queue: Queue[TimedAction] = Queue()
        with self.action_queue_lock:
            current_items = list(self.action_queue.queue)

        current_action_queue = {action.get_timestep(): action.get_action() for action in current_items}

        for new_action in incoming_actions:
            with self.latest_action_lock:
                latest_action = self.latest_action

            if new_action.get_timestep() <= latest_action:
                continue
            if new_action.get_timestep() not in current_action_queue:
                future_action_queue.put(new_action)
                continue

            future_action_queue.put(
                TimedAction(
                    timestamp=new_action.get_timestamp(),
                    timestep=new_action.get_timestep(),
                    action=self.aggregate_fn(
                        current_action_queue[new_action.get_timestep()], new_action.get_action()
                    ),
                )
            )

        with self.action_queue_lock:
            self.action_queue = future_action_queue

    def _receive_actions(self) -> None:
        while not self.shutdown_event.is_set():
            try:
                actions_chunk = self.stub.GetActions(services_pb2.Empty())
                if len(actions_chunk.data) == 0:
                    continue

                timed_actions: list[TimedAction] = pickle.loads(actions_chunk.data)  # nosec B301
                if self.client_device != "cpu":
                    for timed_action in timed_actions:
                        if timed_action.get_action().device.type != self.client_device:
                            timed_action.action = timed_action.get_action().to(self.client_device)

                if timed_actions:
                    self.action_chunk_size = max(self.action_chunk_size, len(timed_actions))
                    self._aggregate_action_queues(timed_actions)
                    self.must_go.set()
            except grpc.RpcError as exc:
                if not self.shutdown_event.is_set():
                    logging.error("Remote policy action receiver error: %s", exc)
                time.sleep(self.environment_dt)
            except Exception as exc:  # noqa: BLE001
                if not self.shutdown_event.is_set():
                    logging.error("Unexpected remote policy receiver error: %s", exc)
                time.sleep(self.environment_dt)

#  +---------------------------------------------------------------------------------------+
#  |                                          record_loop                                  |
#  +---------------------------------------------------------------------------------------+
#  | Legend: [variable] (function)                                                         |
#  |                                                                                       |
#  |      [Robot]                                                                          |
#  |         |                                                                             |
#  |         v                                                                             |
#  |       [obs] ---------------------------------------+                                  |
#  |         |                                          |                                  |
#  |         v                                          |                                  |
#  | (robot_observation_processor)                      |                                  |
#  |         |                                          |                                  |
#  |         v                                          |                                  |
#  |   [obs_processed]                                  |                                  |
#  |         |                                          |                                  |
#  |         v                                          |                                  |
#  | (build_dataset_frame)                              |                                  |
#  |         |                                          |                                  |
#  |         v                                          |                                  |
#  | [observation_frame] -------------------------------|---------------------------+      |
#  |         |                                          |                           |      |
#  |         | (if Policy)                              |                           |      |
#  |         v                                          |                           |      |
#  |  (predict_action)       [Teleop]                   |                           |      |
#  |         |                  |                       |                           |      |
#  |         v                  v                       |                           |      |
#  |  [action_values]         [act]                     |                           |      |
#  |         |                  |                       |                           |      |
#  |         v                  v                       |                           |      |
#  | (make_robot_action) (teleop_action_processor) <----+                           |      |
#  |         |                  |                       |                           |      |
#  |         v                  v                       |                           |      |
#  | [act_processed_policy] [act_processed_teleop]      |                           |      |
#  |         |                  |                       |                           |      |
#  |         +--------+---------+                       |                           |      |
#  |                  |                                 |                           |      |
#  |                  v                                 |                           |      |
#  |           [action_values] -->(build_dataset_frame)-|-->[action_frame]------+   |      |
#  |                  |                                 |                       |   |      |
#  |                  v                                 |                       v   v      |
#  |        (robot_action_processor) <------------------+                     [Dataset]    |
#  |                  |                                                                    |
#  |                  v                                                                    |
#  |        [robot_action_to_send]                                                         |
#  |                  |                                                                    |
#  |                  v                                                                    |
#  |               [Robot]                                                                 |
#  |                                                                                       |
#  +---------------------------------------------------------------------------------------+

@safe_stop_image_writer
def record_loop(
    robot: CustomManipulator,
    events: dict,
    fps: int,
    teleop_action_processor: RobotProcessorPipeline[
        tuple[RobotAction, RobotObservation], RobotAction
    ],  # runs after teleop
    robot_action_processor: RobotProcessorPipeline[
        tuple[RobotAction, RobotObservation], RobotAction
    ],  # runs before robot
    robot_observation_processor: RobotProcessorPipeline[
        RobotObservation, RobotObservation
    ],  # runs after robot
    dataset: LeRobotDataset | None = None,
    teleop: Teleoperator | list[Teleoperator] | None = None,
    policy: PreTrainedPolicy | None = None,
    preprocessor: PolicyProcessorPipeline[dict[str, Any], dict[str, Any]] | None = None,
    postprocessor: PolicyProcessorPipeline[PolicyAction, PolicyAction] | None = None,
    remote_policy_client: RemotePolicyClient | None = None,
    control_time_s: int | None = None,
    single_task: str | None = None,
    display_data: bool = False,
    overlay_viewer = None,
    ros_environment_state_reader: _RosEnvironmentStateReader | None = None,
    teleop_recording_mode: str = "corrections_only",
):
    """
    Custom record_loop forked from lerobot.scripts.lerobot_record.record_loop.
    
    Modifications:
    - Supports 'pause' behavior: frames are only added to dataset when 'is_engaged' is True.
    - Supports 'early exit' via 'exit_episode' (A button).
    - Supports 'discard episode' via 'discard_episode' (B button).
    
    Note: This function will not automatically receive updates from the upstream lerobot_record.py.
    """
    if dataset is not None and dataset.fps != fps:
        raise ValueError(f"The dataset fps should be equal to requested fps ({dataset.fps} != {fps}).")

    # Reset policy and processor if they are provided
    if policy is not None and preprocessor is not None and postprocessor is not None:
        policy.reset()
        preprocessor.reset()
        postprocessor.reset()
    elif remote_policy_client is not None:
        remote_policy_client.reset()

    timestamp = 0
    start_episode_t = time.perf_counter()
    teleop_was_engaged = False
    waiting_for_ros_env_state = False
    while timestamp < control_time_s:
        start_loop_t = time.perf_counter()

        if events["exit_early"]:
            events["exit_early"] = False
            break

        # Get robot observation
        obs = robot.get_observation()
        if overlay_viewer is not None:
            overlay_viewer.show(obs)

        # Applies a pipeline to the raw robot observation, default is IdentityProcessor
        obs_processed = robot_observation_processor(obs)
        ros_env_state_values = {}
        if ros_environment_state_reader is not None:
            latest_values = ros_environment_state_reader.try_get_latest_values()
            if latest_values is None:
                if not waiting_for_ros_env_state:
                    logging.info(
                        "Waiting for ROS environment-state outputs. Cameras remain active and keep streaming "
                        "until the first values arrive."
                    )
                    waiting_for_ros_env_state = True
                precise_sleep(max(1 / fps - (time.perf_counter() - start_loop_t), 0.0))
                start_episode_t = time.perf_counter()
                timestamp = 0
                continue

            ros_env_state_values = latest_values
            if waiting_for_ros_env_state:
                logging.info("ROS environment-state outputs received. Starting episode timing now.")
                waiting_for_ros_env_state = False
                start_episode_t = time.perf_counter()
                timestamp = 0
        if ros_env_state_values:
            obs_processed = {**obs_processed, **ros_env_state_values}

        if policy is not None or dataset is not None:
            observation_frame = build_dataset_frame(dataset.features, obs_processed, prefix=OBS_STR)

        teleop_engaged = False
        selected_action = None

        if isinstance(teleop, Teleoperator):
            act = teleop.get_action()

            rr.log('oculus_frame', rr.Transform3D(translation=[act["position.x"], act["position.y"], act["position.z"]],
                                                  mat3x3=R.from_rotvec([act["orientation.x"], act["orientation.y"], act["orientation.z"]]).as_matrix(),
                                                  )
            )

            # Check for exit signal from teleop (A button)
            if act.pop("exit_episode"):
                break

            # Check for discard signal from teleop (B button)
            if act.pop("discard_episode"):
                events["rerecord_episode"] = True
                break

            teleop_engaged = bool(act.pop("is_engaged"))

        # Get action from either policy or teleop
        if teleop_engaged:
            selected_action = teleop_action_processor((act, obs))
            action_values = selected_action
        else:
            if isinstance(teleop, Teleoperator):
                teleop_action_processor.reset()

                if teleop_was_engaged and policy is not None and preprocessor is not None and postprocessor is not None:
                    policy.reset()
                    preprocessor.reset()
                    postprocessor.reset()
                elif teleop_was_engaged and remote_policy_client is not None:
                    remote_policy_client.reset()

                if policy is None and remote_policy_client is None:
                    teleop_was_engaged = teleop_engaged
                    continue

            if policy is not None and preprocessor is not None and postprocessor is not None:
                action_values = predict_action(
                    observation=observation_frame,
                    policy=policy,
                    device=get_safe_torch_device(policy.config.device),
                    preprocessor=preprocessor,
                    postprocessor=postprocessor,
                    use_amp=policy.config.use_amp,
                    task=single_task,
                    robot_type=robot.robot_type,
                )

                if display_data:
                    queued_actions = getattr(policy, "_action_queue", getattr(policy, "_queues", {}).get(ACTION, []))
                    log_policy_rollout(action_values, list(queued_actions), dataset.features, postprocessor)

                selected_action = make_robot_action(action_values, dataset.features)
                action_values = selected_action
            elif remote_policy_client is not None:
                if remote_policy_client.should_request_action():
                    remote_policy_client.send_observation(obs_processed, single_task)

                if not remote_policy_client.actions_available():
                    teleop_was_engaged = teleop_engaged
                    dt_s = time.perf_counter() - start_loop_t
                    target_dt_s = 1 / fps
                    if dt_s < target_dt_s:
                        precise_sleep(target_dt_s - dt_s)
                    timestamp = time.perf_counter() - start_episode_t
                    continue

                action_tensor = remote_policy_client.pop_action()
                selected_action = make_robot_action(action_tensor, dataset.features)
                action_values = selected_action
            else:
                logging.info(
                    "No policy or teleoperator provided, skipping action generation."
                    "This is likely to happen when resetting the environment without a teleop device."
                    "The robot won't be at its rest position at the start of the next episode."
                )
                teleop_was_engaged = teleop_engaged
                continue

        # Applies a pipeline to the action, default is IdentityProcessor
        robot_action_to_send = robot_action_processor((selected_action, obs))

        _sent_action = robot.send_action(robot_action_to_send)

        should_save_frame = (
            dataset is not None
            and (
                policy is None
                or teleop is None
                or teleop_recording_mode == "all"
                or teleop_engaged
            )
        )
        if should_save_frame:
            action_frame = build_dataset_frame(dataset.features, _sent_action, prefix=ACTION)
            frame = {
                **observation_frame,
                **action_frame,
                "task": single_task,
            }
            dataset.add_frame(frame)

        if display_data:
            log_rerun_data(observation=obs_processed, action=action_values)

        dt_s = time.perf_counter() - start_loop_t
        target_dt_s = 1 / fps
        
        # Warn if control frequency drops below target fps
        if dt_s > target_dt_s:
            actual_fps = 1 / dt_s
            logging.warning(
                f"Control frequency dropped below target: {actual_fps:.1f} Hz (actual) vs {fps} Hz (target). "
                f"Loop took {dt_s*1000:.1f}ms vs target {target_dt_s*1000:.1f}ms."
            )

        teleop_was_engaged = teleop_engaged
        
        precise_sleep(target_dt_s - dt_s)

        timestamp = time.perf_counter() - start_episode_t


def _instantiate_processor_step(step_spec: Any):
    if isinstance(step_spec, str):
        step_class = ProcessorStepRegistry.get(step_spec)
        return step_class()

    if isinstance(step_spec, dict):
        if "registry_name" in step_spec:
            step_class = ProcessorStepRegistry.get(step_spec["registry_name"])
        elif "class" in step_spec:
            module_path, class_name = step_spec["class"].rsplit(".", 1)
            module = importlib.import_module(module_path)
            step_class = getattr(module, class_name)
        else:
            raise ValueError(
                f"Invalid processor step config {step_spec!r}. Expected a string, or a dict with "
                f"'registry_name' or 'class'."
            )
        return step_class(**step_spec.get("config", {}))

    raise TypeError(f"Unsupported processor step spec: {step_spec!r}")


def _build_robot_processor_pipeline(
    processor_cfg: dict[str, Any],
    *,
    to_transition,
    to_output,
) -> RobotProcessorPipeline:
    steps = [_instantiate_processor_step(step_spec) for step_spec in processor_cfg.get("steps", [])]
    return RobotProcessorPipeline(
        steps=steps,
        to_transition=to_transition,
        to_output=to_output,
    )


def _resolve_resume_root(cfg: RecordConfig) -> Path:
    if cfg.dataset.root is not None:
        return Path(cfg.dataset.root)

    root = HF_LEROBOT_HOME / cfg.dataset.repo_id
    logging.info(
        "Resuming recording without `dataset.root`; using the default local dataset path: %s",
        root,
    )
    return root
@parser.wrap(config_path='cfgs/record.yaml')
def record(cfg: RecordConfig):
    init_logging()
    logging.info(pformat(asdict(cfg)))
    
    if cfg.display_data:
        init_rerun(session_name="recording_custom_manipulator")

    # Initialize robot and teleop from config
    robot = CustomManipulator(cfg.robot)
    teleop = make_teleoperator_from_config(cfg.teleop) if cfg.teleop is not None else None

    teleop_action_processor = _build_robot_processor_pipeline(
        cfg.teleop_action_processor,
        to_transition=robot_action_observation_to_transition,
        to_output=transition_to_robot_action,
    )
    robot_action_processor = _build_robot_processor_pipeline(
        cfg.robot_action_processor,
        to_transition=robot_action_observation_to_transition,
        to_output=transition_to_robot_action,
    )
    robot_observation_processor = _build_robot_processor_pipeline(
        cfg.robot_observation_processor,
        to_transition=observation_to_transition,
        to_output=transition_to_observation,
    )

    processed_observation_features = aggregate_pipeline_dataset_features(
        pipeline=robot_observation_processor,
        initial_features=create_initial_features(observation=robot.observation_features),
        use_videos=cfg.dataset.video,
    )

    dataset_features = combine_feature_dicts(
        aggregate_pipeline_dataset_features(
            pipeline=teleop_action_processor,
            initial_features=create_initial_features(
                action=robot.action_features
            ),
            use_videos=cfg.dataset.video,
        ),
        aggregate_pipeline_dataset_features(
            pipeline=robot_observation_processor,
            initial_features=create_initial_features(observation=robot.observation_features),
            use_videos=cfg.dataset.video,
        ),
        _build_ros_env_state_dataset_features(cfg.ros_environment_state),
        processed_observation_features,
    )

    if cfg.resume:
        resume_root = _resolve_resume_root(cfg)
        if cfg.dataset.force_cache_sync:
            logging.info("Force-syncing dataset '%s' from the Hub before resuming.", cfg.dataset.repo_id)
        LeRobotDataset(cfg.dataset.repo_id, root=resume_root, force_cache_sync=cfg.dataset.force_cache_sync)
        num_cameras = len(robot.cameras) if hasattr(robot, "cameras") else 0
        dataset = LeRobotDataset.resume(
            cfg.dataset.repo_id,
            root=resume_root,
            force_cache_sync=cfg.dataset.force_cache_sync,
            batch_encoding_size=cfg.dataset.video_encoding_batch_size,
            image_writer_processes=cfg.dataset.num_image_writer_processes if num_cameras > 0 else 0,
            image_writer_threads=cfg.dataset.num_image_writer_threads_per_camera * num_cameras
            if num_cameras > 0
            else 0,
        )
        sanity_check_dataset_robot_compatibility(dataset, robot, cfg.dataset.fps, dataset_features)
    else:
        sanity_check_dataset_name(cfg.dataset.repo_id, cfg.policy, cfg.teleop)
        dataset = LeRobotDataset.create(
            cfg.dataset.repo_id,
            cfg.dataset.fps,
            root=cfg.dataset.root,
            robot_type=robot.name,
            features=dataset_features,
            use_videos=cfg.dataset.video,
            image_writer_processes=cfg.dataset.num_image_writer_processes,
            image_writer_threads=cfg.dataset.num_image_writer_threads_per_camera * len(robot.cameras),
            batch_encoding_size=cfg.dataset.video_encoding_batch_size,
        )

    use_remote_policy = cfg.policy is not None and cfg.policy_server.enabled

    # Load pretrained policy
    if cfg.policy is not None and not use_remote_policy:
        policy_source = get_policy_loading_source(cfg.policy)
        if policy_source is None:
            raise ValueError(get_missing_policy_source_message(cfg.policy))
        logging.info("Loading pretrained policy '%s' from '%s'.", cfg.policy.type, policy_source)
    elif use_remote_policy:
        remote_policy_source = get_remote_policy_loading_source(cfg.policy)
        if remote_policy_source is None:
            raise ValueError(get_missing_remote_policy_source_message(cfg.policy))
        logging.info(
            "Using remote async policy '%s' from '%s' via '%s'.",
            cfg.policy.type,
            remote_policy_source,
            cfg.policy_server.server_address,
        )

    policy = None if (cfg.policy is None or use_remote_policy) else make_policy(cfg.policy, ds_meta=dataset.meta)

    preprocessor = None
    postprocessor = None
    if cfg.policy is not None and not use_remote_policy:
        preprocessor, postprocessor = make_pre_post_processors(
            policy_cfg=cfg.policy,
            pretrained_path=cfg.policy.pretrained_path,
            dataset_stats=rename_stats(dataset.meta.stats, cfg.dataset.rename_map),
            preprocessor_overrides={
                "device_processor": {"device": cfg.policy.device},
                "rename_observations_processor": {"rename_map": cfg.dataset.rename_map},
            },
        )

    ros_environment_state_reader = None
    if cfg.ros_environment_state.enabled:
        ros_environment_state_reader = _RosEnvironmentStateReader(cfg.ros_environment_state)
    remote_policy_client = None
    if use_remote_policy:
        remote_policy_source = get_remote_policy_loading_source(cfg.policy)
        assert remote_policy_source is not None
        remote_policy_client = RemotePolicyClient(
            server_address=cfg.policy_server.server_address,
            policy_type=cfg.policy.type,
            pretrained_name_or_path=remote_policy_source,
            policy_device=cfg.policy.device,
            client_device=cfg.policy_server.client_device,
            lerobot_features=processed_observation_features,
            rename_map=cfg.dataset.rename_map,
            actions_per_chunk=cfg.policy_server.actions_per_chunk,
            chunk_size_threshold=cfg.policy_server.chunk_size_threshold,
            aggregate_fn_name=cfg.policy_server.aggregate_fn_name,
            fps=cfg.dataset.fps,
        )

    overlay_viewer = None
    if cfg.display_data and not is_headless():
        overlay_viewer = make_episode_start_overlay(dataset)

    robot.connect()
    if ros_environment_state_reader is not None:
        ros_environment_state_reader.connect()
    if cfg.teleop is not None:
        teleop.connect()
    if remote_policy_client is not None:
        remote_policy_client.start()

    listener, events = init_keyboard_listener()
    
    robot.reset()

    with VideoEncodingManager(dataset):
        recorded_episodes = 0
        while recorded_episodes < cfg.dataset.num_episodes and not events["stop_recording"]:
            log_say(f"Recording episode {dataset.num_episodes}", cfg.play_sounds)
            record_loop(
                robot=robot,
                events=events,
                fps=cfg.dataset.fps,
                teleop_action_processor=teleop_action_processor,
                robot_action_processor=robot_action_processor,
                robot_observation_processor=robot_observation_processor,
                teleop=teleop,
                policy=policy,
                preprocessor=preprocessor,
                postprocessor=postprocessor,
                remote_policy_client=remote_policy_client,
                dataset=dataset,
                control_time_s=cfg.dataset.episode_time_s,
                single_task=cfg.dataset.single_task,
                display_data=cfg.display_data,
                overlay_viewer=overlay_viewer,
                ros_environment_state_reader=ros_environment_state_reader,
                teleop_recording_mode=cfg.teleop_recording_mode,
            )

            if not events["stop_recording"] and (
                (recorded_episodes < cfg.dataset.num_episodes - 1) or events["rerecord_episode"]
                or (cfg.policy is not None and cfg.teleop is not None and not dataset.has_pending_frames())
            ):
                log_say("Reset the environment", cfg.play_sounds)
                robot.reset()
                teleop_action_processor.reset()

            if events["rerecord_episode"]:
                log_say("Re-record episode", cfg.play_sounds)
                events["rerecord_episode"] = False
                events["exit_early"] = False
                dataset.clear_episode_buffer()
                continue

            if cfg.policy is not None and cfg.teleop is not None and not dataset.has_pending_frames():
                if events["stop_recording"]:
                    break
                log_say("No corrections recorded. Retry episode", cfg.play_sounds)
                continue

            dataset.save_episode()
            if overlay_viewer is not None:
                overlay_viewer.on_episode_saved(dataset)
            recorded_episodes += 1

    log_say("Stop recording", cfg.play_sounds, blocking=True)

    if overlay_viewer is not None:
        overlay_viewer.close()

    robot.disconnect()
    if ros_environment_state_reader is not None:
        ros_environment_state_reader.disconnect()
    if cfg.teleop is not None:
        teleop.disconnect()
    if remote_policy_client is not None:
        remote_policy_client.stop()
        if cfg.policy_server.debug_visualize_queue_size and remote_policy_client.action_queue_size:
            from lerobot.async_inference.helpers import visualize_action_queue_size

            visualize_action_queue_size(remote_policy_client.action_queue_size)

    if not is_headless() and listener is not None:
        listener.stop()

    if cfg.dataset.push_to_hub:
        dataset.push_to_hub(tags=cfg.dataset.tags, private=cfg.dataset.private)

    log_say("Exiting", cfg.play_sounds)
    return dataset

if __name__ == "__main__":
    record()
    import os, sys; sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
