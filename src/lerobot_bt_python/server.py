#!/usr/bin/env python

# Comment: executes this BT logic statement.
"""@file server.py
@brief ROS2 service server for the Python execution layer.

@details
This module is the runtime boundary between the C++ BehaviorTree.CPP process,
the Python robot execution process, and external scene verifiers. The C++ side
never imports policy or robot code directly: it sends a `RunNamedCommand`
request, waits for this server to finish the command, and then polls the
VLM check state managed here. VLM/manual verifiers use topics only.

Flow role:
1. Wait for the C++ BT to send a named command.
2. Dispatch that command to a learned policy skill or a VLM/manual gate.
3. Return the result to the BT so the tree can continue or retry.
"""

# Comment: imports dependencies or symbols required by the module.
import importlib
# Comment: imports dependencies or symbols required by the module.
import json
# Comment: imports dependencies or symbols required by the module.
import logging
# Comment: imports dependencies or symbols required by the module.
import os
# Comment: imports dependencies or symbols required by the module.
import sys
# Comment: imports dependencies or symbols required by the module.
import time
# Comment: imports dependencies or symbols required by the module.
from dataclasses import asdict
# Comment: imports dependencies or symbols required by the module.
from pathlib import Path
# Comment: imports dependencies or symbols required by the module.
from pprint import pformat
# Comment: imports dependencies or symbols required by the module.
from typing import TYPE_CHECKING, Any, Callable

# Comment: imports dependencies or symbols required by the module.
import rclpy
# Comment: imports dependencies or symbols required by the module.
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup
# Comment: imports dependencies or symbols required by the module.
from rclpy.executors import MultiThreadedExecutor
# Comment: imports dependencies or symbols required by the module.
from rclpy.node import Node

# Comment: imports dependencies or symbols required by the module.
from lerobot.common.control_utils import is_headless
# Comment: imports dependencies or symbols required by the module.
from lerobot.configs import parser
# Comment: imports dependencies or symbols required by the module.
from lerobot.processor import ProcessorStepRegistry, RobotProcessorPipeline
# Comment: imports dependencies or symbols required by the module.
from lerobot.processor.converters import (
    # Comment: executes this BT logic statement.
    observation_to_transition,
    # Comment: executes this BT logic statement.
    robot_action_observation_to_transition,
    # Comment: executes this BT logic statement.
    transition_to_observation,
    # Comment: executes this BT logic statement.
    transition_to_robot_action,
# Comment: closes a call, data structure, or multiline block.
)
# Comment: imports dependencies or symbols required by the module.
from lerobot.utils.utils import init_logging, log_say
# Comment: imports dependencies or symbols required by the module.
from lerobot.utils.visualization_utils import init_rerun as init_rerun_viz

# Comment: imports dependencies or symbols required by the module.
from .config import SkillCommandServerConfig
# Comment: imports dependencies or symbols required by the module.
from .executor import CommandResult, SkillCommandExecutor
# Comment: imports dependencies or symbols required by the module.
from .verification import (
    # Comment: executes this BT logic statement.
    VLM_FAILURE,
    # Comment: executes this BT logic statement.
    VLM_NEEDS_MANUAL_HELP,
    # Comment: executes this BT logic statement.
    VLM_PENDING,
    # Comment: executes this BT logic statement.
    VLM_RUNNING,
    # Comment: executes this BT logic statement.
    VLM_SUCCESS,
    # Comment: executes this BT logic statement.
    VLM_UNKNOWN,
    # Comment: executes this BT logic statement.
    VLM_WAIT_HUMAN,
    # Comment: executes this BT logic statement.
    VLM_WAITING_STATUSES,
    # Comment: executes this BT logic statement.
    VlmCheckRegistry,
# Comment: closes a call, data structure, or multiline block.
)

# Comment: assigns or prepares a value used by later statements.
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "make_sandwich_executor.yaml"
# Comment: executes this BT logic statement.
"""Default draccus YAML loaded when the entry point is started without flags."""

# Comment: evaluates a condition and chooses the branch to run.
if TYPE_CHECKING:
    # Comment: imports dependencies or symbols required by the module.
    from lerobot.robots.custom_manipulator.custom_manipulator import CustomManipulator

# Comment: assigns or prepares a value used by later statements.
VLM_GATE_PENDING_KIND = "vlm_gate_pending"
# Comment: executes this BT logic statement.
"""Command kind that acknowledges a gate but leaves the VLM check pending."""

# Comment: assigns or prepares a value used by later statements.
_NEXT_ACTION_TO_STATUS = {
    # Comment: executes this BT logic statement.
    "CONTINUE": VLM_SUCCESS,
    # Comment: executes this BT logic statement.
    "PROCEED": VLM_SUCCESS,
    # Comment: executes this BT logic statement.
    "RETRY": VLM_FAILURE,
    # Comment: executes this BT logic statement.
    "RETRY_SKILL": VLM_FAILURE,
    # Comment: executes this BT logic statement.
    "WAIT": VLM_RUNNING,
    # Comment: executes this BT logic statement.
    "WAIT_HUMAN": VLM_WAIT_HUMAN,
    # Comment: executes this BT logic statement.
    "REQUEST_MANUAL_INTERVENTION": VLM_NEEDS_MANUAL_HELP,
    # Comment: executes this BT logic statement.
    "MANUAL_INTERVENTION": VLM_NEEDS_MANUAL_HELP,
# Comment: closes a call, data structure, or multiline block.
}


# Comment: defines the function or method _truthy_payload_value.
def _truthy_payload_value(value: Any) -> bool:
    # Comment: executes this BT logic statement.
    """@brief Return true for boolean-like values coming from simple VLM topics."""
    # Comment: evaluates a condition and chooses the branch to run.
    if isinstance(value, bool):
        # Comment: returns the computed value to the caller.
        return value
    # Comment: evaluates a condition and chooses the branch to run.
    if isinstance(value, str):
        # Comment: returns the computed value to the caller.
        return value.strip().lower() in {"1", "true", "yes", "y"}
    # Comment: returns the computed value to the caller.
    return False


# Comment: defines the function or method _normalize_vlm_status_token.
def _normalize_vlm_status_token(token: str) -> str:
    # Comment: executes this BT logic statement.
    """@brief Map scene-gate tokens onto the registry status vocabulary."""
    # Comment: assigns or prepares a value used by later statements.
    normalized = token.upper()
    # Comment: evaluates a condition and chooses the branch to run.
    if not normalized:
        # Comment: returns the computed value to the caller.
        return ""
    # Comment: evaluates a condition and chooses the branch to run.
    if normalized.startswith("SCENE_") and normalized.endswith("_READY"):
        # Comment: returns the computed value to the caller.
        return VLM_SUCCESS
    # Comment: evaluates a condition and chooses the branch to run.
    if normalized == "TASK_COMPLETE":
        # Comment: returns the computed value to the caller.
        return VLM_SUCCESS
    # Comment: evaluates a condition and chooses the branch to run.
    if normalized == "ANOMALY_DETECTED":
        # Comment: returns the computed value to the caller.
        return VLM_FAILURE
    # Comment: evaluates a condition and chooses the branch to run.
    if normalized == "HUMAN_HELP_REQUIRED":
        # Comment: returns the computed value to the caller.
        return VLM_NEEDS_MANUAL_HELP
    # Comment: returns the computed value to the caller.
    return normalized


# Comment: defines the function or method _vlm_status_from_payload.
def _vlm_status_from_payload(payload: dict[str, Any]) -> str:
    # Comment: executes this BT logic statement.
    """@brief Resolve VLM status/next_action fields into the BT-facing status."""
    # Comment: evaluates a condition and chooses the branch to run.
    if _truthy_payload_value(payload.get("human_help_required", False)):
        # Comment: returns the computed value to the caller.
        return VLM_NEEDS_MANUAL_HELP
    # Comment: evaluates a condition and chooses the branch to run.
    if _truthy_payload_value(payload.get("anomaly_detected", False)):
        # Comment: returns the computed value to the caller.
        return VLM_FAILURE
    # Comment: evaluates a condition and chooses the branch to run.
    if _truthy_payload_value(payload.get("scene_ready", False)):
        # Comment: returns the computed value to the caller.
        return VLM_SUCCESS

    # Comment: assigns or prepares a value used by later statements.
    status = _normalize_vlm_status_token(str(payload.get("status", "")))
    # Comment: evaluates a condition and chooses the branch to run.
    if status:
        # Comment: returns the computed value to the caller.
        return status
    # Comment: assigns or prepares a value used by later statements.
    scene_id = _normalize_vlm_status_token(str(payload.get("scene_id", "")))
    # Comment: evaluates a condition and chooses the branch to run.
    if scene_id:
        # Comment: returns the computed value to the caller.
        return scene_id
    # Comment: assigns or prepares a value used by later statements.
    next_action = str(payload.get("next_action", "")).upper()
    # Comment: evaluates a condition and chooses the branch to run.
    if next_action in _NEXT_ACTION_TO_STATUS:
        # Comment: returns the computed value to the caller.
        return _NEXT_ACTION_TO_STATUS[next_action]
    # Comment: returns the computed value to the caller.
    return ""


# Comment: defines the function or method _vlm_message_from_payload.
def _vlm_message_from_payload(payload: dict[str, Any], *, status: str) -> str:
    # Comment: executes this BT logic statement.
    """@brief Build a compact operator message from richer VLM topic fields."""
    # Comment: assigns or prepares a value used by later statements.
    message_parts = []
    # Comment: assigns or prepares a value used by later statements.
    message = str(payload.get("message", ""))
    # Comment: evaluates a condition and chooses the branch to run.
    if message:
        # Comment: closes a call, data structure, or multiline block.
        message_parts.append(message)
    # Comment: iterates over the elements of the selected sequence.
    for key in (
        # Comment: executes this BT logic statement.
        "scene_id",
        # Comment: executes this BT logic statement.
        "scene_ready",
        # Comment: executes this BT logic statement.
        "anomaly_detected",
        # Comment: executes this BT logic statement.
        "human_help_required",
        # Comment: executes this BT logic statement.
        "failure_reason",
        # Comment: executes this BT logic statement.
        "scene_state",
        # Comment: executes this BT logic statement.
        "required_human_action",
        # Comment: executes this BT logic statement.
        "next_action",
    # Comment: executes this BT logic statement.
    ):
        # Comment: assigns or prepares a value used by later statements.
        value = payload.get(key)
        # Comment: evaluates a condition and chooses the branch to run.
        if value not in (None, ""):
            # Comment: assigns or prepares a value used by later statements.
            message_parts.append(f"{key}={value}")
    # Comment: evaluates a condition and chooses the branch to run.
    if not message_parts:
        # Comment: closes a call, data structure, or multiline block.
        message_parts.append(f"External verifier reported {status}.")
    # Comment: returns the computed value to the caller.
    return " | ".join(message_parts)


# Comment: defines the function or method _instantiate_processor_step.
def _instantiate_processor_step(step_spec: Any):
    # Comment: executes this BT logic statement.
    """@brief Build one configured robot/policy processor step.

    @param step_spec Either a registry name, or a mapping containing
        `registry_name`/`class` and an optional `config` dictionary.
    @return A configured processor step instance.

    The server allows processor steps to be configured without importing every
    possible class at module import time. A string uses LeRobot's processor
    registry; a mapping can either name a registry entry or import a class by
    dotted Python path.
    """
    # Comment: evaluates a condition and chooses the branch to run.
    if isinstance(step_spec, str):
        # Registry form: the YAML only stores a stable processor name.
        # Comment: assigns or prepares a value used by later statements.
        step_class = ProcessorStepRegistry.get(step_spec)
        # Comment: returns the computed value to the caller.
        return step_class()

    # Comment: evaluates a condition and chooses the branch to run.
    if isinstance(step_spec, dict):
        # Comment: evaluates a condition and chooses the branch to run.
        if "registry_name" in step_spec:
            # Explicit registry mapping, useful when a config block is needed.
            # Comment: assigns or prepares a value used by later statements.
            step_class = ProcessorStepRegistry.get(step_spec["registry_name"])
        # Comment: evaluates an alternative condition from the previous branch.
        elif "class" in step_spec:
            # Dynamic class path for processors that are not registered globally.
            # Comment: assigns or prepares a value used by later statements.
            module_path, class_name = step_spec["class"].rsplit(".", 1)
            # Comment: assigns or prepares a value used by later statements.
            module = importlib.import_module(module_path)
            # Comment: assigns or prepares a value used by later statements.
            step_class = getattr(module, class_name)
        # Comment: handles the fallback branch when previous conditions do not match.
        else:
            # Comment: raises an explicit error for the caller.
            raise ValueError(
                # Comment: executes this BT logic statement.
                f"Invalid processor step config {step_spec!r}. Expected a string, or a dict with "
                # Comment: executes this BT logic statement.
                f"'registry_name' or 'class'."
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: returns the computed value to the caller.
        return step_class(**step_spec.get("config", {}))

    # Comment: raises an explicit error for the caller.
    raise TypeError(f"Unsupported processor step spec: {step_spec!r}")


# Comment: defines the function or method _start_camera_publisher.
def _start_camera_publisher(
    *,
    robot: "CustomManipulator",
    topic_map: dict[str, str],
    fps: float,
    jpeg_quality: int,
    node: Node,
) -> Callable[[], None]:
    """Start a background thread that publishes camera frames as ROS2 CompressedImage.

    This lets the external VLM verifier subscribe to live camera feeds without
    opening the RealSense devices directly (which would conflict with the BT
    server's own usage).

    @param robot Connected CustomManipulator with cameras already open.
    @param topic_map Mapping from BT camera name to ROS topic name.
    @param fps Publishing rate in Hz.
    @param jpeg_quality JPEG quality 0-100.
    @param node ROS2 node used to create publishers.
    @return A stop function that signals the thread to exit.
    """
    import cv2
    import threading
    from sensor_msgs.msg import CompressedImage

    stop_event = threading.Event()
    publishers: dict[str, Any] = {}

    # Create one publisher per mapped camera
    for bt_cam_name, ros_topic in topic_map.items():
        if bt_cam_name not in robot.cameras:
            logging.warning(
                "Camera publish map references '%s' but robot has no such camera. Available: %s",
                bt_cam_name,
                sorted(robot.cameras),
            )
            continue
        pub = node.create_publisher(CompressedImage, ros_topic, 10)
        publishers[bt_cam_name] = pub
        logging.info("Publishing camera '%s' → %s", bt_cam_name, ros_topic)

    if not publishers:
        logging.warning("No valid camera→topic mappings; camera publisher idle.")
        return stop_event.set  # Return a no-op stop function

    period_s = 1.0 / max(fps, 0.1)
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)]

    def _publish_loop() -> None:
        while not stop_event.is_set():
            for bt_cam_name, pub in publishers.items():
                try:
                    camera = robot.cameras[bt_cam_name]
                    # Use a short timeout so the publisher never blocks the
                    # policy control loop that also reads from the same camera.
                    frame = camera.async_read(timeout_ms=50)
                    if frame is None:
                        continue
                    # frame is a numpy array (H, W, 3) in RGB; cv2 needs BGR
                    _, jpeg_bytes = cv2.imencode(".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), encode_params)
                    msg = CompressedImage()
                    msg.header.stamp = node.get_clock().now().to_msg()
                    msg.header.frame_id = bt_cam_name
                    msg.format = "jpeg"
                    msg.data = jpeg_bytes.tobytes()
                    pub.publish(msg)
                except Exception:
                    pass  # Silently skip if camera is busy or no frame available
            stop_event.wait(timeout=period_s)

    thread = threading.Thread(target=_publish_loop, daemon=True, name="camera-publisher")
    thread.start()
    return stop_event.set
def _build_robot_processor_pipeline(
    # Comment: executes this BT logic statement.
    processor_cfg: dict[str, Any],
    # Comment: executes this BT logic statement.
    *,
    # Comment: executes this BT logic statement.
    to_transition,
    # Comment: executes this BT logic statement.
    to_output,
# Comment: executes this BT logic statement.
) -> RobotProcessorPipeline:
    # Comment: executes this BT logic statement.
    """@brief Convert a YAML processor list into a LeRobot pipeline.

    @param processor_cfg Mapping with a `steps` list.
    @param to_transition Converter from robot-native objects to transition data.
    @param to_output Converter from transition data back to robot-native output.
    @return A `RobotProcessorPipeline` that wraps every configured step.
    """
    # Comment: assigns or prepares a value used by later statements.
    steps = [_instantiate_processor_step(step_spec) for step_spec in processor_cfg.get("steps", [])]
    # Comment: returns the computed value to the caller.
    return RobotProcessorPipeline(
        # Comment: assigns or prepares a value used by later statements.
        steps=steps,
        # Comment: assigns or prepares a value used by later statements.
        to_transition=to_transition,
        # Comment: assigns or prepares a value used by later statements.
        to_output=to_output,
    # Comment: closes a call, data structure, or multiline block.
    )


# Comment: defines the function or method _prepend_generated_interface_paths.
def _prepend_generated_interface_paths() -> None:
    # Comment: executes this BT logic statement.
    """@brief Put generated ROS2 interface packages before source packages.

    The repository contains `src/lerobot_bt_interfaces`, while ROS2 generation
    creates importable Python bindings under `install/.../site-packages`. When
    the editable repo has already placed `src/` on `sys.path`, Python may see the
    source package first and miss the generated `.srv` modules. This helper adds
    the generated package directories at the front of `sys.path`.
    """
    # Comment: assigns or prepares a value used by later statements.
    python_dir = f"python{sys.version_info.major}.{sys.version_info.minor}"
    # Comment: assigns or prepares a value used by later statements.
    repo_root = Path(__file__).resolve().parents[2]
    # Comment: assigns or prepares a value used by later statements.
    prefixes = [Path(path) for path in os.environ.get("COLCON_PREFIX_PATH", "").split(os.pathsep) if path]
    # Comment: executes this BT logic statement.
    prefixes.extend(
        # Comment: executes this BT logic statement.
        [
            # Comment: executes this BT logic statement.
            repo_root / "install" / "lerobot_bt_interfaces",
            # Comment: executes this BT logic statement.
            repo_root / "install",
        # Comment: closes a call, data structure, or multiline block.
        ]
    # Comment: closes a call, data structure, or multiline block.
    )

    # Comment: iterates over the elements of the selected sequence.
    for prefix in prefixes:
        # Comment: assigns or prepares a value used by later statements.
        site_packages = prefix / "lib" / python_dir / "site-packages"
        # Comment: evaluates a condition and chooses the branch to run.
        if (site_packages / "lerobot_bt_interfaces" / "srv").exists():
            # Comment: assigns or prepares a value used by later statements.
            site_packages_str = str(site_packages)
            # Comment: evaluates a condition and chooses the branch to run.
            if site_packages_str not in sys.path:
                # Comment: closes a call, data structure, or multiline block.
                sys.path.insert(0, site_packages_str)


# Comment: defines the function or method _load_bt_services.
def _load_bt_services():
    # Comment: executes this BT logic statement.
    """@brief Import generated LeRobot BT ROS2 service classes.

    @return `(RunNamedCommand, GetSkillVerification, ReportSkillVerification)`.
    @throws ImportError if the workspace has not been built or sourced.

    The editable repo adds `src/` to `sys.path`, which makes Python see the
    source-only ROS package as a namespace package before the generated
    interface package under `install/.../site-packages`.
    """
    # Comment: closes a call, data structure, or multiline block.
    _prepend_generated_interface_paths()
    # Comment: iterates over the elements of the selected sequence.
    for module_name in list(sys.modules):
        # Comment: evaluates a condition and chooses the branch to run.
        if module_name == "lerobot_bt_interfaces" or module_name.startswith("lerobot_bt_interfaces."):
            # Comment: closes a call, data structure, or multiline block.
            del sys.modules[module_name]

    # Comment: opens a protected block to catch possible errors.
    try:
        # Comment: imports dependencies or symbols required by the module.
        from lerobot_bt_interfaces.srv import GetSkillVerification, ReportSkillVerification, RunNamedCommand

        # Comment: returns the computed value to the caller.
        return RunNamedCommand, GetSkillVerification, ReportSkillVerification
    # Comment: handles a specific exception raised by the protected block.
    except ImportError as import_error:
        # Comment: raises an explicit error for the caller.
        raise ImportError(
            # Comment: executes this BT logic statement.
            "Could not import the lerobot_bt_interfaces service bindings. "
            # Comment: executes this BT logic statement.
            "Source install/local_setup.bash or rebuild lerobot_bt_interfaces."
        # Comment: executes this BT logic statement.
        ) from import_error


# Comment: declares the class SkillCommandServer.
class SkillCommandServer(Node):
    # Comment: executes this BT logic statement.
    """@brief ROS2 node that executes BT commands and stores VLM check state.

    The node owns three services and two verifier-facing topics:
    - `RunNamedCommand`: command execution requested by BT XML leaf nodes.
    - `VLM state service`: polling endpoint used by `WaitForVLMVerdict`.
    - `legacy VLM result service`: legacy endpoint kept for compatibility.
    - `vlm_request_topic`: published when a scene verdict is needed.
    - `vlm_result_topic`: consumed from manual/VLM results.
    """

    # Comment: defines the function or method __init__.
    def __init__(
        # Comment: executes this BT logic statement.
        self,
        # Comment: executes this BT logic statement.
        cfg: SkillCommandServerConfig,
        # Comment: executes this BT logic statement.
        robot: "CustomManipulator",
        # Comment: executes this BT logic statement.
        executor_backend: SkillCommandExecutor,
        # Comment: executes this BT logic statement.
        robot_action_processor: RobotProcessorPipeline,
        # Comment: executes this BT logic statement.
        robot_observation_processor: RobotProcessorPipeline,
        # Comment: executes this BT logic statement.
        vlm_check_registry: VlmCheckRegistry,
    # Comment: executes this BT logic statement.
    ) -> None:
        # Comment: executes this BT logic statement.
        """@brief Construct the service node and register every ROS2 service.

        @param cfg Runtime configuration loaded from YAML.
        @param robot Connected robot object used by the executor backend.
        @param executor_backend Object that actually runs learned skills.
        @param robot_action_processor Pipeline that converts policy actions.
        @param robot_observation_processor Pipeline that converts observations.
        @param vlm_check_registry In-memory state machine for skill attempts.
        """
        # Comment: closes a call, data structure, or multiline block.
        super().__init__("lerobot_bt_skill_server")
        # Comment: updates state or a field on the current object.
        self.cfg = cfg
        # Comment: updates state or a field on the current object.
        self.robot = robot
        # Comment: updates state or a field on the current object.
        self.executor_backend = executor_backend
        # Comment: updates state or a field on the current object.
        self.robot_action_processor = robot_action_processor
        # Comment: updates state or a field on the current object.
        self.robot_observation_processor = robot_observation_processor
        # Comment: updates state or a field on the current object.
        self.vlm_check_registry = vlm_check_registry
        # Comment: updates state or a field on the current object.
        self._command_callback_group = MutuallyExclusiveCallbackGroup()
        # Comment: updates state or a field on the current object.
        self._vlm_callback_group = ReentrantCallbackGroup()

        # ROS2 entrypoints used by the BT runtime and verifier-facing topics.
        # Comment: assigns or prepares a value used by later statements.
        bt_command_service_type, vlm_state_service_type, legacy_vlm_result_service_type = _load_bt_services()
        # Comment: imports dependencies or symbols required by the module.
        from std_msgs.msg import String  # type: ignore

        # Comment: creates a ROS2 service exposed to other nodes.
        self._bt_command_server = self.create_service(
            # Comment: executes this BT logic statement.
            bt_command_service_type,
            # Comment: executes this BT logic statement.
            cfg.bt_command_service,
            # Comment: executes this BT logic statement.
            self._handle_request,
            # Comment: assigns or prepares a value used by later statements.
            callback_group=self._command_callback_group,
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: creates a ROS2 service exposed to other nodes.
        self._vlm_state_server = self.create_service(
            # Comment: executes this BT logic statement.
            vlm_state_service_type,
            # Comment: executes this BT logic statement.
            cfg.vlm_state_service,
            # Comment: executes this BT logic statement.
            self._handle_get_vlm_state,
            # Comment: assigns or prepares a value used by later statements.
            callback_group=self._vlm_callback_group,
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: creates a ROS2 service exposed to other nodes.
        self._legacy_vlm_result_server = self.create_service(
            # Comment: executes this BT logic statement.
            legacy_vlm_result_service_type,
            # Comment: executes this BT logic statement.
            cfg.legacy_vlm_result_service,
            # Comment: executes this BT logic statement.
            self._handle_legacy_vlm_result,
            # Comment: assigns or prepares a value used by later statements.
            callback_group=self._vlm_callback_group,
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: creates a ROS2 publisher to send messages on a topic.
        self._vlm_request_publisher = self.create_publisher(
            # Comment: executes this BT logic statement.
            String,
            # Comment: executes this BT logic statement.
            cfg.vlm_request_topic,
            # Comment: executes this BT logic statement.
            10,
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: creates a ROS2 subscription to receive messages from a topic.
        self._vlm_result_subscription = self.create_subscription(
            # Comment: executes this BT logic statement.
            String,
            # Comment: executes this BT logic statement.
            cfg.vlm_result_topic,
            # Comment: executes this BT logic statement.
            self._handle_vlm_result_topic,
            # Comment: executes this BT logic statement.
            10,
            # Comment: assigns or prepares a value used by later statements.
            callback_group=self._vlm_callback_group,
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: executes this BT logic statement.
        self.get_logger().info(
            # Comment: executes this BT logic statement.
            "Serving BT commands on "
            # Comment: executes this BT logic statement.
            f"'{cfg.bt_command_service}', VLM state service on "
            # Comment: executes this BT logic statement.
            f"'{cfg.vlm_state_service}', legacy VLM result service on "
            # Comment: executes this BT logic statement.
            f"'{cfg.legacy_vlm_result_service}', VLM requests on "
            # Comment: executes this BT logic statement.
            f"'{cfg.vlm_request_topic}', and VLM results from "
            # Comment: executes this BT logic statement.
            f"'{cfg.vlm_result_topic}'."
        # Comment: closes a call, data structure, or multiline block.
        )

    # Comment: defines the function or method _handle_request.
    def _handle_request(self, request, response):
        # Comment: executes this BT logic statement.
        """@brief Handle one `RunNamedCommand` service request.

        @param request ROS2 request with `kind`, `name`, and `timeout_s`.
        @param response Mutable ROS2 response filled before returning.
        @return The filled ROS2 response object.

        This method deliberately separates command execution from post-skill
        scene check. A successful skill opens a VLM check attempt; the
        BT can only advance after `WaitForVLMVerdict` sees that attempt resolve.
        """
        # This is the handoff point between C++ BT orchestration and Python execution.
        # Comment: closes a call, data structure, or multiline block.
        log_say(f"Executing {request.kind} {request.name}", self.cfg.play_sounds)

        # Comment: opens a protected block to catch possible errors.
        try:
            # Comment: evaluates a condition and chooses the branch to run.
            if request.kind == "skill":
                # Open a VLM check BEFORE executing the skill so the VLM can
                # monitor the scene in real-time and return SUCCESS as soon as
                # the goal is achieved, cutting the skill execution short.
                self.vlm_check_registry.register_skill_name(request.name)
                vlm_pre_attempt = self.vlm_check_registry.begin_attempt(request.name)
                self._publish_vlm_request(vlm_pre_attempt)
                self.get_logger().info(
                    f"Pre-skill VLM check opened for '{request.name}' attempt {vlm_pre_attempt.attempt_id}."
                )
                # Real learned primitive: delegate to the robot/policy executor.
                # The executor checks _active_vlm_result and stops early if the
                # VLM reports a terminal status during execution.
                # Comment: assigns or prepares a value used by later statements.
                result = self.executor_backend.execute_skill(
                    # Comment: assigns or prepares a value used by later statements.
                    skill_name=request.name,
                    # Comment: assigns or prepares a value used by later statements.
                    robot_action_processor=self.robot_action_processor,
                    # Comment: assigns or prepares a value used by later statements.
                    robot_observation_processor=self.robot_observation_processor,
                    # Comment: assigns or prepares a value used by later statements.
                    timeout_override_s=request.timeout_s,
                # Comment: closes a call, data structure, or multiline block.
                )
            # Comment: evaluates an alternative condition from the previous branch.
            elif request.kind == VLM_GATE_PENDING_KIND:
                # Human/VLM gate: open an attempt but do not resolve it.
                # Comment: assigns or prepares a value used by later statements.
                result = CommandResult(
                    # Comment: executes this BT logic statement.
                    True,
                    # Comment: executes this BT logic statement.
                    "SUCCESS",
                    # Comment: executes this BT logic statement.
                    0.0,
                    # Comment: executes this BT logic statement.
                    f"VLM gate '{request.name}' opened and is awaiting a VLM result.",
                # Comment: closes a call, data structure, or multiline block.
                )
            # Comment: handles the fallback branch when previous conditions do not match.
            else:
                # Comment: assigns or prepares a value used by later statements.
                result = None
        # Comment: handles a specific exception raised by the protected block.
        except Exception as exc:  # noqa: BLE001
            # Comment: updates state or a field on the current object.
            response.success = False
            # Comment: updates state or a field on the current object.
            response.status = "ERROR"
            # Comment: updates state or a field on the current object.
            response.elapsed_s = 0.0
            # Comment: updates state or a field on the current object.
            response.message = f"Server exception while executing command: {exc}"
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().exception(response.message)
            # Comment: returns the computed value to the caller.
            return response

        # Comment: evaluates a condition and chooses the branch to run.
        if result is None:
            # Comment: updates state or a field on the current object.
            response.success = False
            # Comment: updates state or a field on the current object.
            response.status = "ERROR"
            # Comment: updates state or a field on the current object.
            response.elapsed_s = 0.0
            # Comment: updates state or a field on the current object.
            response.message = f"Unsupported command kind '{request.kind}'."
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().error(response.message)
            # Comment: returns the computed value to the caller.
            return response

        # Comment: evaluates a condition and chooses the branch to run.
        if request.kind in {"skill", VLM_GATE_PENDING_KIND} and result.success:
            # Comment: opens a protected block to catch possible errors.
            try:
                # For skills, the VLM check was already opened before execution
                # (see pre-skill block above). Only open a new attempt for gates.
                if request.kind == VLM_GATE_PENDING_KIND:
                    # Gate names do not need to exist in the real skill config.
                    # Comment: closes a call, data structure, or multiline block.
                    self.vlm_check_registry.register_skill_name(request.name)
                    # Comment: assigns or prepares a value used by later statements.
                    vlm_check_attempt = self.vlm_check_registry.begin_attempt(request.name)
                    # Give the human operator time to place/adjust objects
                    # before the VLM starts checking the scene. The BT polls
                    # and sees PENDING during this wait.
                    gate_wait_s = float(getattr(self.cfg, "vlm_gate_min_wait_s", 5.0))
                    if gate_wait_s > 0:
                        self.get_logger().info(
                            f"Gate '{request.name}': waiting {gate_wait_s:.1f}s for human operator..."
                        )
                        time.sleep(gate_wait_s)
                    self._publish_vlm_request(vlm_check_attempt)
                # For skills, the pre-skill VLM check was a warm-up. After the
                # skill finishes, open a fresh attempt so the VLM sees the
                # final scene, not stale pre-skill frames.
                elif request.kind == "skill":
                    vlm_check_attempt = self.vlm_check_registry.begin_attempt(request.name)
                    self._publish_vlm_request(vlm_check_attempt)
                # Comment: assigns or prepares a value used by later statements.
                live_vlm_status = getattr(result, "vlm_status", None)
                # Comment: evaluates a condition and chooses the branch to run.
                if live_vlm_status:
                    # Comment: executes this BT logic statement.
                    self.vlm_check_registry.report(
                        # Comment: assigns or prepares a value used by later statements.
                        skill_name=request.name,
                        # Comment: assigns or prepares a value used by later statements.
                        attempt_id=vlm_check_attempt.attempt_id,
                        # Comment: assigns or prepares a value used by later statements.
                        status=live_vlm_status,
                        # Comment: assigns or prepares a value used by later statements.
                        message=getattr(result, "vlm_message", "") or result.message,
                    # Comment: closes a call, data structure, or multiline block.
                    )
                    # Comment: assigns or prepares a value used by later statements.
                    result.message = (
                        # Comment: executes this BT logic statement.
                        f"{result.message} "
                        # Comment: executes this BT logic statement.
                        f"VLM check attempt {vlm_check_attempt.attempt_id} was resolved as "
                        # Comment: executes this BT logic statement.
                        f"{live_vlm_status} from the live verifier result."
                    # Comment: closes a call, data structure, or multiline block.
                    )
                # Comment: handles the fallback branch when previous conditions do not match.
                else:
                    # Comment: assigns or prepares a value used by later statements.
                    publish_vlm_request = getattr(self, "_publish_vlm_request", None)
                    # Comment: evaluates a condition and chooses the branch to run.
                    if publish_vlm_request is not None:
                        # Comment: closes a call, data structure, or multiline block.
                        publish_vlm_request(vlm_check_attempt)
                    # Comment: assigns or prepares a value used by later statements.
                    vlm_request_topic = getattr(
                        # Comment: executes this BT logic statement.
                        self.cfg,
                        # Comment: executes this BT logic statement.
                        "vlm_request_topic",
                        # Comment: executes this BT logic statement.
                        self.cfg.vlm_state_service,
                    # Comment: closes a call, data structure, or multiline block.
                    )
                    # Comment: assigns or prepares a value used by later statements.
                    result.message = (
                        # Comment: executes this BT logic statement.
                        f"{result.message} "
                        # Comment: executes this BT logic statement.
                        f"VLM check attempt {vlm_check_attempt.attempt_id} is now pending on "
                        # Comment: executes this BT logic statement.
                        f"'{vlm_request_topic}'."
                    # Comment: closes a call, data structure, or multiline block.
                    )
            # Comment: handles a specific exception raised by the protected block.
            except Exception as exc:  # noqa: BLE001
                # Comment: updates state or a field on the current object.
                response.success = False
                # Comment: updates state or a field on the current object.
                response.status = "ERROR"
                # Comment: updates state or a field on the current object.
                response.elapsed_s = float(result.elapsed_s)
                # Comment: updates state or a field on the current object.
                response.message = f"Could not open VLM check for command '{request.name}': {exc}"
                # Comment: closes a call, data structure, or multiline block.
                self.get_logger().error(response.message)
                # Comment: returns the computed value to the caller.
                return response

        # Comment: updates state or a field on the current object.
        response.success = bool(result.success)
        # Comment: updates state or a field on the current object.
        response.status = result.status
        # Comment: updates state or a field on the current object.
        response.elapsed_s = float(result.elapsed_s)
        # Comment: updates state or a field on the current object.
        response.message = result.message
        # Comment: evaluates a condition and chooses the branch to run.
        if result.success:
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().info(result.message)
        # Comment: handles the fallback branch when previous conditions do not match.
        else:
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().error(result.message)
        # Comment: returns the computed value to the caller.
        return response

    # Comment: defines the function or method _handle_get_vlm_state.
    def _handle_get_vlm_state(self, request, response):
        # Comment: executes this BT logic statement.
        """@brief Return the latest VLM check attempt for one skill.

        @param request ROS2 request containing `skill_name`.
        @param response Mutable ROS2 response with attempt metadata.
        @return The filled ROS2 response object.
        """
        # Comment: opens a protected block to catch possible errors.
        try:
            # Comment: assigns or prepares a value used by later statements.
            snapshot = self.vlm_check_registry.get_latest(request.skill_name)
        # Comment: handles a specific exception raised by the protected block.
        except ValueError as exc:
            # Comment: updates state or a field on the current object.
            response.has_attempt = False
            # Comment: updates state or a field on the current object.
            response.attempt_id = 0
            # Comment: updates state or a field on the current object.
            response.status = VLM_UNKNOWN
            # Comment: updates state or a field on the current object.
            response.message = str(exc)
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().error(response.message)
            # Comment: returns the computed value to the caller.
            return response

        # Comment: evaluates a condition and chooses the branch to run.
        if snapshot is None:
            # Comment: updates state or a field on the current object.
            response.has_attempt = False
            # Comment: updates state or a field on the current object.
            response.attempt_id = 0
            # Comment: updates state or a field on the current object.
            response.status = VLM_UNKNOWN
            # Comment: updates state or a field on the current object.
            response.message = f"No completed attempt has been recorded yet for skill '{request.skill_name}'."
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().warning(response.message)
            # Comment: returns the computed value to the caller.
            return response

        # Comment: updates state or a field on the current object.
        response.has_attempt = True
        # Comment: updates state or a field on the current object.
        response.attempt_id = int(snapshot.attempt_id)
        # Comment: updates state or a field on the current object.
        response.status = snapshot.status
        # Comment: updates state or a field on the current object.
        response.message = snapshot.message
        # Comment: evaluates a condition and chooses the branch to run.
        if snapshot.status in VLM_WAITING_STATUSES:
            # Comment: executes this BT logic statement.
            self.get_logger().debug(
                # Comment: executes this BT logic statement.
                f"VLM check for skill '{snapshot.skill_name}' attempt {snapshot.attempt_id} "
                # Comment: executes this BT logic statement.
                f"is {snapshot.status}."
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: returns the computed value to the caller.
        return response

    # Comment: defines the function or method _handle_legacy_vlm_result.
    def _handle_legacy_vlm_result(self, request, response):
        # Comment: executes this BT logic statement.
        """@brief Accept a verifier verdict for a pending skill attempt.

        @param request ROS2 request containing skill name, attempt id, status,
            and message.
        @param response Mutable ROS2 response that reports whether the verdict
            was applied.
        @return The filled ROS2 response object.
        """
        # Comment: evaluates a condition and chooses the branch to run.
        if self._try_report_active_skill_vlm_result(
            # Comment: assigns or prepares a value used by later statements.
            skill_name=request.skill_name,
            # Comment: assigns or prepares a value used by later statements.
            attempt_id=int(request.attempt_id),
            # Comment: assigns or prepares a value used by later statements.
            status=request.status,
            # Comment: assigns or prepares a value used by later statements.
            message=request.message,
        # Comment: executes this BT logic statement.
        ):
            # Comment: updates state or a field on the current object.
            response.accepted = True
            # Comment: updates state or a field on the current object.
            response.applied_attempt_id = 0
            # Comment: updates state or a field on the current object.
            response.message = (
                # Comment: executes this BT logic statement.
                f"Accepted VLM status {request.status} as live stop for active skill "
                # Comment: executes this BT logic statement.
                f"'{request.skill_name}'."
            # Comment: closes a call, data structure, or multiline block.
            )
            # Comment: returns the computed value to the caller.
            return response

        # Comment: opens a protected block to catch possible errors.
        try:
            # Comment: assigns or prepares a value used by later statements.
            update = self.vlm_check_registry.report(
                # Comment: assigns or prepares a value used by later statements.
                skill_name=request.skill_name,
                # Comment: assigns or prepares a value used by later statements.
                attempt_id=int(request.attempt_id),
                # Comment: assigns or prepares a value used by later statements.
                status=request.status,
                # Comment: assigns or prepares a value used by later statements.
                message=request.message,
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: handles a specific exception raised by the protected block.
        except ValueError as exc:
            # Comment: updates state or a field on the current object.
            response.accepted = False
            # Comment: updates state or a field on the current object.
            response.applied_attempt_id = 0
            # Comment: updates state or a field on the current object.
            response.message = str(exc)
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().error(response.message)
            # Comment: returns the computed value to the caller.
            return response

        # Comment: updates state or a field on the current object.
        response.accepted = bool(update.accepted)
        # Comment: updates state or a field on the current object.
        response.applied_attempt_id = 0 if update.snapshot is None else int(update.snapshot.attempt_id)
        # Comment: updates state or a field on the current object.
        response.message = update.message
        # Comment: assigns or prepares a value used by later statements.
        log_fn = self.get_logger().info if update.accepted else self.get_logger().warning
        # Comment: closes a call, data structure, or multiline block.
        log_fn(response.message)
        # Comment: returns the computed value to the caller.
        return response

    # Comment: defines the function or method _try_report_active_skill_vlm_result.
    def _try_report_active_skill_vlm_result(
        # Comment: executes this BT logic statement.
        self,
        # Comment: executes this BT logic statement.
        *,
        # Comment: executes this BT logic statement.
        skill_name: str,
        # Comment: executes this BT logic statement.
        attempt_id: int,
        # Comment: executes this BT logic statement.
        status: str,
        # Comment: executes this BT logic statement.
        message: str,
    # Comment: executes this BT logic statement.
    ) -> bool:
        # Comment: executes this BT logic statement.
        """@brief Offer a verifier result to the currently running skill first."""
        # Comment: assigns or prepares a value used by later statements.
        report_active = getattr(self.executor_backend, "report_active_vlm_result", None)
        # Comment: evaluates a condition and chooses the branch to run.
        if report_active is None:
            # Comment: returns the computed value to the caller.
            return False

        # Comment: assigns or prepares a value used by later statements.
        accepted = bool(
            # Comment: executes this BT logic statement.
            report_active(
                # Comment: assigns or prepares a value used by later statements.
                skill_name=skill_name,
                # Comment: assigns or prepares a value used by later statements.
                attempt_id=attempt_id,
                # Comment: assigns or prepares a value used by later statements.
                status=status,
                # Comment: assigns or prepares a value used by later statements.
                message=message,
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: closes a call, data structure, or multiline block.
        )
        # Comment: evaluates a condition and chooses the branch to run.
        if accepted:
            # Comment: executes this BT logic statement.
            self.get_logger().info(
                # Comment: executes this BT logic statement.
                f"Accepted VLM status {status} as live stop for active skill '{skill_name}'."
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: returns the computed value to the caller.
        return accepted

    # Comment: defines the function or method _publish_vlm_request.
    def _publish_vlm_request(self, snapshot) -> None:
        # Comment: executes this BT logic statement.
        """@brief Publish a topic event asking a VLM/manual verifier for a verdict."""
        # Comment: imports dependencies or symbols required by the module.
        from std_msgs.msg import String  # type: ignore

        # Resolve the optional human-readable task description for this skill so
        # the VLM prompt can include semantic context about what to verify.
        # Check two sources: PrimitiveSkillConfig.task for BC skills, and
        # vlm_gate_tasks for VLM-only gates (AwaitScene nodes).
        skill_cfg = self.executor_backend.skill_configs.get(snapshot.skill_name)
        task_desc = ""
        if skill_cfg is not None and getattr(skill_cfg, "task", None):
            task_desc = skill_cfg.task.strip()
        if not task_desc:
            task_desc = self.cfg.vlm_gate_tasks.get(snapshot.skill_name, "")

        # Comment: assigns or prepares a value used by later statements.
        payload = {
            # Comment: executes this BT logic statement.
            "event": "vlm_check_requested",
            # Comment: executes this BT logic statement.
            "skill_name": snapshot.skill_name,
            # Comment: executes this BT logic statement.
            "attempt_id": int(snapshot.attempt_id),
            # Comment: executes this BT logic statement.
            "status": VLM_PENDING,
            # Comment: executes this BT logic statement.
            "message": snapshot.message,
            # Comment: executes this BT logic statement.
            "task": task_desc,
            # Comment: executes this BT logic statement.
            "allowed_statuses": [
                # Comment: executes this BT logic statement.
                "PENDING",
                # Comment: executes this BT logic statement.
                "RUNNING",
                # Comment: executes this BT logic statement.
                "WAIT_HUMAN",
                # Comment: executes this BT logic statement.
                "MANUAL_INTERVENTION_REQUIRED",
                # Comment: executes this BT logic statement.
                "SUCCESS",
                # Comment: executes this BT logic statement.
                "FAILURE",
            # Comment: executes this BT logic statement.
            ],
            # Comment: executes this BT logic statement.
            "allowed_next_actions": [
                # Comment: executes this BT logic statement.
                "CONTINUE",
                # Comment: executes this BT logic statement.
                "RETRY_SKILL",
                # Comment: executes this BT logic statement.
                "WAIT_HUMAN",
                # Comment: executes this BT logic statement.
                "REQUEST_MANUAL_INTERVENTION",
            # Comment: executes this BT logic statement.
            ],
        # Comment: closes a call, data structure, or multiline block.
        }
        # Comment: assigns or prepares a value used by later statements.
        msg = String()
        # Comment: serializes the Python payload into a JSON string.
        msg.data = json.dumps(payload, sort_keys=True)
        # Comment: publishes the prepared message on the ROS2 topic.
        self._vlm_request_publisher.publish(msg)
        # Comment: executes this BT logic statement.
        self.get_logger().info(
            # Comment: executes this BT logic statement.
            f"VLM REQUEST → skill='{snapshot.skill_name}' attempt={snapshot.attempt_id} "
            f"task='{task_desc}'"
        # Comment: closes a call, data structure, or multiline block.
        )
        # Visible terminal output for the operator.
        print(f"\n{'═'*60}")
        print(f"🔍 VLM CHECK → {snapshot.skill_name} (attempt {snapshot.attempt_id})")
        if task_desc:
            print(f"   Task: {task_desc}")
        print(f"{'═'*60}\n")

    # Comment: defines the function or method _handle_vlm_result_topic.
    def _handle_vlm_result_topic(self, msg) -> None:
        # Comment: executes this BT logic statement.
        """@brief Apply one JSON verifier verdict received from a ROS2 topic."""
        # Comment: opens a protected block to catch possible errors.
        try:
            # Comment: deserializes a JSON string into a Python object.
            payload = json.loads(msg.data)
        # Comment: handles a specific exception raised by the protected block.
        except Exception as exc:  # noqa: BLE001
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().error(f"Invalid VLM result JSON: {exc}: '{msg.data}'")
            # Comment: returns the computed value to the caller.
            return
        # Comment: evaluates a condition and chooses the branch to run.
        if not isinstance(payload, dict):
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().error("Rejected VLM result topic message: payload must be a JSON object.")
            # Comment: returns the computed value to the caller.
            return

        # Comment: opens a protected block to catch possible errors.
        try:
            # Comment: assigns or prepares a value used by later statements.
            skill_name = str(payload.get("skill_name", ""))
            # Comment: assigns or prepares a value used by later statements.
            status = _vlm_status_from_payload(payload)
            # Comment: assigns or prepares a value used by later statements.
            attempt_id = int(payload.get("attempt_id", 0))
            # Comment: assigns or prepares a value used by later statements.
            message = _vlm_message_from_payload(payload, status=status)
            # Comment: evaluates a condition and chooses the branch to run.
            if self._try_report_active_skill_vlm_result(
                # Comment: assigns or prepares a value used by later statements.
                skill_name=skill_name,
                # Comment: assigns or prepares a value used by later statements.
                attempt_id=attempt_id,
                # Comment: assigns or prepares a value used by later statements.
                status=status,
                # Comment: assigns or prepares a value used by later statements.
                message=message,
            # Comment: executes this BT logic statement.
            ):
                # Comment: returns the computed value to the caller.
                return
            # Comment: assigns or prepares a value used by later statements.
            update = self.vlm_check_registry.report(
                # Comment: assigns or prepares a value used by later statements.
                skill_name=skill_name,
                # Comment: assigns or prepares a value used by later statements.
                attempt_id=attempt_id,
                # Comment: assigns or prepares a value used by later statements.
                status=status,
                # Comment: assigns or prepares a value used by later statements.
                message=message,
            # Comment: closes a call, data structure, or multiline block.
            )
        # Comment: handles a specific exception raised by the protected block.
        except (TypeError, ValueError) as exc:
            # Comment: closes a call, data structure, or multiline block.
            self.get_logger().error(f"Rejected VLM result topic message: {exc}")
            # Comment: returns the computed value to the caller.
            return

        # Comment: assigns or prepares a value used by later statements.
        log_fn = self.get_logger().info if update.accepted else self.get_logger().warning
        # Comment: closes a call, data structure, or multiline block.
        log_fn(update.message)

        # Visible terminal output for the operator.
        emoji = {"SUCCESS": "✅", "FAILURE": "❌", "RUNNING": "🔄", "PENDING": "⏳"}.get(status, "📢")
        print(f"\n{'═'*60}")
        print(f"{emoji} VLM RESULT → {skill_name}: {status}")
        print(f"   Message: {message}")
        print(f"{'═'*60}\n")


# Comment: applies a decorator to the following definition.
@parser.wrap(config_path=DEFAULT_CONFIG_PATH)
def run(cfg: SkillCommandServerConfig) -> None:
    # Comment: executes this BT logic statement.
    """@brief Start the real ROS2 skill command server.

    @param cfg Parsed draccus config. When invoked from the entry point this is
        loaded from `make_sandwich_executor.yaml` unless another config is passed.

    Startup order matters: the robot and processors are created before the node
    spins so the BT never reaches a half-initialized command server.
    """
    # Comment: closes a call, data structure, or multiline block.
    init_logging()
    # Comment: closes a call, data structure, or multiline block.
    logging.info(pformat(asdict(cfg)))

    # Comment: closes a call, data structure, or multiline block.
    logging.info("Initializing ROS2 client library.")
    # Comment: evaluates a condition and chooses the branch to run.
    if not rclpy.ok():
        # Comment: closes a call, data structure, or multiline block.
        rclpy.init()
    # Comment: closes a call, data structure, or multiline block.
    logging.info("ROS2 client library is ready.")

    # Comment: evaluates a condition and chooses the branch to run.
    if cfg.display_data and not is_headless():
        # Comment: closes a call, data structure, or multiline block.
        logging.info("Initializing Rerun visualization.")
        # Comment: assigns or prepares a value used by later statements.
        init_rerun_viz(session_name="lerobot_bt_skill_server")
        # Comment: closes a call, data structure, or multiline block.
        logging.info("Rerun visualization is ready.")

    # Comment: closes a call, data structure, or multiline block.
    logging.info("Constructing CustomManipulator.")
    # Comment: imports dependencies or symbols required by the module.
    from lerobot.robots.custom_manipulator.custom_manipulator import CustomManipulator
    # Comment: assigns or prepares a value used by later statements.
    robot = CustomManipulator(cfg.robot)
    # Comment: closes a call, data structure, or multiline block.
    logging.info("CustomManipulator constructed.")

    # Comment: closes a call, data structure, or multiline block.
    logging.info("Building robot action processor.")
    # Comment: assigns or prepares a value used by later statements.
    robot_action_processor = _build_robot_processor_pipeline(
        # Comment: executes this BT logic statement.
        cfg.robot_action_processor,
        # Comment: assigns or prepares a value used by later statements.
        to_transition=robot_action_observation_to_transition,
        # Comment: assigns or prepares a value used by later statements.
        to_output=transition_to_robot_action,
    # Comment: closes a call, data structure, or multiline block.
    )
    # Comment: closes a call, data structure, or multiline block.
    logging.info("Robot action processor ready.")

    # Comment: closes a call, data structure, or multiline block.
    logging.info("Building robot observation processor.")
    # Comment: assigns or prepares a value used by later statements.
    robot_observation_processor = _build_robot_processor_pipeline(
        # Comment: executes this BT logic statement.
        cfg.robot_observation_processor,
        # Comment: assigns or prepares a value used by later statements.
        to_transition=observation_to_transition,
        # Comment: assigns or prepares a value used by later statements.
        to_output=transition_to_observation,
    # Comment: closes a call, data structure, or multiline block.
    )
    # Comment: closes a call, data structure, or multiline block.
    logging.info("Robot observation processor ready.")

    # Comment: closes a call, data structure, or multiline block.
    logging.info("Constructing skill command executor.")
    # Comment: assigns or prepares a value used by later statements.
    executor_backend = SkillCommandExecutor(cfg=cfg, robot=robot)
    # Comment: closes a call, data structure, or multiline block.
    logging.info("Skill command executor ready.")
    # Comment: assigns or prepares a value used by later statements.
    vlm_check_registry = VlmCheckRegistry(
        # Comment: assigns or prepares a value used by later statements.
        known_skill_names=set(executor_backend.skill_configs),
        # Comment: assigns or prepares a value used by later statements.
        vlm_timeout_s=cfg.vlm_timeout_s,
    # Comment: closes a call, data structure, or multiline block.
    )
    # Comment: closes a call, data structure, or multiline block.
    logging.info("VLM check registry ready.")

    # Comment: closes a call, data structure, or multiline block.
    logging.info("Creating ROS2 skill command service node.")
    # Comment: assigns or prepares a value used by later statements.
    server_node = SkillCommandServer(
        # Comment: assigns or prepares a value used by later statements.
        cfg=cfg,
        # Comment: assigns or prepares a value used by later statements.
        robot=robot,
        # Comment: assigns or prepares a value used by later statements.
        executor_backend=executor_backend,
        # Comment: assigns or prepares a value used by later statements.
        robot_action_processor=robot_action_processor,
        # Comment: assigns or prepares a value used by later statements.
        robot_observation_processor=robot_observation_processor,
        # Comment: assigns or prepares a value used by later statements.
        vlm_check_registry=vlm_check_registry,
    # Comment: closes a call, data structure, or multiline block.
    )
    # Comment: closes a call, data structure, or multiline block.
    logging.info("ROS2 skill command service node is ready.")

    # Comment: assigns or prepares a value used by later statements.
    ros_executor = MultiThreadedExecutor(num_threads=4)
    # Comment: closes a call, data structure, or multiline block.
    ros_executor.add_node(server_node)
    # Comment: opens a protected block to catch possible errors.
    try:
        # Robot-facing startup happens before we start accepting BT commands.
        # Comment: closes a call, data structure, or multiline block.
        logging.info("Connecting robot.")
        # Comment: closes a call, data structure, or multiline block.
        robot.connect()
        # Comment: closes a call, data structure, or multiline block.
        logging.info("Robot connected.")
        # Comment: evaluates a condition and chooses the branch to run.
        if cfg.reset_robot_on_startup:
            # Comment: closes a call, data structure, or multiline block.
            logging.info("Resetting robot on startup.")
            # Comment: closes a call, data structure, or multiline block.
            robot.reset()
            # Comment: closes a call, data structure, or multiline block.
            logging.info("Robot startup reset complete.")
        # Comment: closes a call, data structure, or multiline block.
        logging.info("Spinning skill command server.")
        # Comment: closes a call, data structure, or multiline block.

        # Start background camera publisher so the VLM can subscribe to live
        # frames without opening the RealSense devices a second time.
        _camera_pub_stop = None
        if cfg.camera_publish_map and cfg.camera_publish_fps > 0:
            _camera_pub_stop = _start_camera_publisher(
                robot=robot,
                topic_map=cfg.camera_publish_map,
                fps=cfg.camera_publish_fps,
                jpeg_quality=cfg.camera_publish_jpeg_quality,
                node=server_node,
            )
            logging.info(
                "Camera publisher started: %s at %.1f FPS.",
                sorted(cfg.camera_publish_map.values()),
                cfg.camera_publish_fps,
            )

        try:
            ros_executor.spin()
        finally:
            if _camera_pub_stop is not None:
                _camera_pub_stop()
    # Comment: always runs the final cleanup for the protected block.
    finally:
        # Comment: opens a protected block to catch possible errors.
        try:
            # Comment: closes a call, data structure, or multiline block.
            ros_executor.shutdown()
        # Comment: handles a specific exception raised by the protected block.
        except Exception:  # noqa: BLE001
            # Comment: closes a call, data structure, or multiline block.
            logging.exception("Best-effort ROS2 executor shutdown failed.")
        # Comment: opens a protected block to catch possible errors.
        try:
            # Comment: closes a call, data structure, or multiline block.
            robot.disconnect()
        # Comment: handles a specific exception raised by the protected block.
        except Exception:  # noqa: BLE001
            # Comment: closes a call, data structure, or multiline block.
            logging.exception("Best-effort robot disconnect failed during server shutdown.")
        # Comment: opens a protected block to catch possible errors.
        try:
            # Comment: closes a call, data structure, or multiline block.
            server_node.destroy_node()
        # Comment: handles a specific exception raised by the protected block.
        except Exception:  # noqa: BLE001
            # Comment: closes a call, data structure, or multiline block.
            logging.exception("Best-effort ROS2 node destruction failed during server shutdown.")
        # Comment: evaluates a condition and chooses the branch to run.
        if rclpy.ok():
            # Comment: closes a call, data structure, or multiline block.
            rclpy.shutdown()


# Comment: defines the function or method main.
def main() -> None:
    # Comment: executes this BT logic statement.
    """@brief Console entry point used by `lerobot-bt-skill-server`."""
    # Comment: closes a call, data structure, or multiline block.
    run()


# Comment: evaluates a condition and chooses the branch to run.
if __name__ == "__main__":
    # Comment: closes a call, data structure, or multiline block.
    main()
