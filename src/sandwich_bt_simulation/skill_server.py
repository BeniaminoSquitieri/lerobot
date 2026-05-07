"""@file skill_server.py
@brief Hardware-free simulation harness for the sandwich BT stack.

This module keeps the BT command contract intact without importing ROS2 or any
robot drivers. It is intended for local smoke tests of the named-command flow.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from sandwich_bt_python.verification import (  # type: ignore
        VLM_FAILURE,
        VLM_NEEDS_MANUAL_HELP,
        VLM_UNKNOWN,
        VLM_WAIT_HUMAN,
        VLM_WAITING_STATUSES,
        VlmCheckRegistry,
    )
else:
    from sandwich_bt_python.verification import (
        VLM_FAILURE,
        VLM_NEEDS_MANUAL_HELP,
        VLM_UNKNOWN,
        VLM_WAIT_HUMAN,
        VLM_WAITING_STATUSES,
        VlmCheckRegistry,
    )

_ACTION_KEYS = (
    "position.x",
    "position.y",
    "position.z",
    "orientation.x",
    "orientation.y",
    "orientation.z",
)

SIMULATED_SKILL_KIND = "simulated_skill"
SIMULATED_SKILL_PENDING_KIND = "simulated_skill_pending"

_NEXT_ACTION_TO_STATUS = {
    "CONTINUE": "SUCCESS",
    "PROCEED": "SUCCESS",
    "RETRY": VLM_FAILURE,
    "RETRY_SKILL": VLM_FAILURE,
    "WAIT_HUMAN": VLM_WAIT_HUMAN,
    "REQUEST_MANUAL_INTERVENTION": VLM_NEEDS_MANUAL_HELP,
}

_COMMAND_KINDS_THAT_OPEN_VLM_CHECK = {
    "skill",
    SIMULATED_SKILL_KIND,
    SIMULATED_SKILL_PENDING_KIND,
}


def _vlm_status_from_payload(payload: dict[str, Any]) -> str:
    """@brief Resolve topic status/next_action fields into registry status."""
    status = str(payload.get("status", "")).upper()
    if status:
        return status
    next_action = str(payload.get("next_action", "")).upper()
    return _NEXT_ACTION_TO_STATUS.get(next_action, "")


def _vlm_message_from_payload(payload: dict[str, Any], *, status: str) -> str:
    """@brief Keep richer VLM reasons visible through the legacy message field."""
    message_parts = []
    message = str(payload.get("message", ""))
    if message:
        message_parts.append(message)
    for key in ("failure_reason", "scene_state", "required_human_action", "next_action"):
        value = payload.get(key)
        if value not in (None, ""):
            message_parts.append(f"{key}={value}")
    return " | ".join(message_parts) if message_parts else f"External verifier reported {status}."


@dataclass
class MockSkillTransition:
    """@brief Minimal transition config used by the mock skill executor."""

    mode: str = "timeout"
    """Termination mode mirrored from the real `SkillTransitionConfig`."""

    min_duration_s: float = 0.0
    """Minimum simulated rollout duration before predicate-based success."""

    max_duration_s: float = 0.5
    """Maximum simulated rollout duration for timeout-based modes."""

    def __post_init__(self) -> None:
        """@brief Validate the transition shape at construction time."""
        allowed_modes = {"timeout", "all_conditions", "all_conditions_or_timeout", "until_success"}
        if self.mode not in allowed_modes:
            raise ValueError(f"Unsupported mode '{self.mode}'. Expected one of {sorted(allowed_modes)}.")
        if self.min_duration_s < 0:
            raise ValueError("min_duration_s must be >= 0.")
        if self.max_duration_s <= 0:
            raise ValueError("max_duration_s must be > 0.")


@dataclass
class MockSkillConfig:
    """@brief Named mock skill entry accepted by the simulation service."""

    name: str
    """Runtime name matched against `RunNamedCommand.name`."""

    transition: MockSkillTransition = field(default_factory=MockSkillTransition)
    """Termination behavior used by the mock executor."""

    settle_time_s: float = 0.0
    """Simulated pre-rollout settle time in seconds."""

    def __post_init__(self) -> None:
        """@brief Reject empty names and negative settle times."""
        if not self.name:
            raise ValueError("Skill name must not be empty.")
        if self.settle_time_s < 0:
            raise ValueError("settle_time_s must be >= 0.")


@dataclass
class MockServerConfig:
    """@brief Top-level config for the in-process mock command service."""

    fps: int = 10
    """Virtual control frequency used to accumulate elapsed time."""

    bt_command_service: str = "/sandwich_bt/run"
    """ROS2 service name used when exposing the mock as a live node."""

    vlm_state_service: str = "/sandwich_bt/vlm_state"
    """Mock VLM state service name."""

    legacy_vlm_result_service: str = "/sandwich_bt/vlm_result_legacy"
    """Mock legacy VLM result service name."""

    vlm_request_topic: str = "/sandwich_bt/vlm_request"
    """Mock topic published when a VLM/manual verifier should inspect a scene."""

    vlm_result_topic: str = "/sandwich_bt/vlm_result"
    """Mock topic consumed from a VLM/manual verifier."""

    vlm_timeout_s: float = 30.0
    """Seconds before a waiting VLM check is treated as FAILURE."""

    display_data: bool = False
    play_sounds: bool = False
    rename_map: dict[str, str] = field(default_factory=dict)
    skills: list[MockSkillConfig] = field(default_factory=list)
    """Configured skill names accepted by the mock executor."""

    def __post_init__(self) -> None:
        """@brief Validate basic service/runtime invariants."""
        if self.fps <= 0:
            raise ValueError("fps must be > 0.")
        if self.vlm_timeout_s < 0:
            raise ValueError("vlm_timeout_s must be >= 0.")
        if not self.skills:
            raise ValueError("At least one skill must be configured.")


@dataclass
class MockRobotArmConfig:
    """@brief Arm-specific behavior for the in-memory robot."""

    use_delta_actions: bool = False
    """When true, actions are interpreted as deltas instead of absolute targets."""

    step_size: float = 0.01
    """Per-step mock policy displacement."""

    initial_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    initial_orientation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    """Initial Cartesian pose used by `reset()`."""

    def __post_init__(self) -> None:
        """@brief Reject non-positive motion increments."""
        if self.step_size <= 0:
            raise ValueError("step_size must be > 0.")


@dataclass
class MockRobotConfig:
    """@brief Full mock robot config used by `MockCustomManipulator`."""

    arm: MockRobotArmConfig = field(default_factory=MockRobotArmConfig)
    initial_gripper: float = 0.0
    """Initial gripper value restored by `reset()`."""


class MockGripperInterface:
    """@brief Tiny adapter with the same call shape as the real gripper driver."""

    def __init__(self, robot: MockCustomManipulator):
        """@brief Store the parent mock robot whose state will be mutated."""
        self.robot = robot

    def apply_commands(self, commands: dict[str, Any] | float) -> None:
        """@brief Apply either dict-based or scalar gripper commands."""
        if isinstance(commands, dict):
            if "gripper" in commands:
                self.robot._state["gripper"] = float(commands["gripper"])
            return
        self.robot._state["gripper"] = float(commands)


class MockCustomManipulator:
    """@brief Small in-memory stand-in for the real custom manipulator."""

    robot_type = "mock_custom_manipulator"

    def __init__(self, config: MockRobotConfig | None = None):
        """@brief Initialize connection flag, state dict, and gripper adapter."""
        self.config = config if config is not None else MockRobotConfig()
        self._is_connected = False
        self._state = self._make_initial_state()
        self.reset_count = 0
        self.sent_actions: list[dict[str, float]] = []
        self.gripper_interface = MockGripperInterface(self)

    def _make_initial_state(self) -> dict[str, float]:
        """@brief Build the reset state from the mock robot config."""
        return {
            "position.x": float(self.config.arm.initial_position[0]),
            "position.y": float(self.config.arm.initial_position[1]),
            "position.z": float(self.config.arm.initial_position[2]),
            "orientation.x": float(self.config.arm.initial_orientation[0]),
            "orientation.y": float(self.config.arm.initial_orientation[1]),
            "orientation.z": float(self.config.arm.initial_orientation[2]),
            "gripper": float(self.config.initial_gripper),
        }

    @property
    def observation_features(self) -> dict[str, type]:
        """@brief Return observation feature names with scalar float types."""
        return dict.fromkeys(self._state, float)

    @property
    def action_features(self) -> dict[str, type]:
        """@brief Return action feature names with scalar float types."""
        return dict.fromkeys(self._state, float)

    @property
    def is_connected(self) -> bool:
        """@brief Report whether `connect()` has been called."""
        return self._is_connected

    @property
    def is_calibrated(self) -> bool:
        """@brief The mock is always considered calibrated."""
        return True

    def connect(self, calibrate: bool = True) -> None:
        """@brief Mark the mock robot as connected."""
        self._is_connected = True

    def calibrate(self) -> None:
        """@brief No-op calibration hook matching the real robot API."""
        return None

    def configure(self) -> None:
        """@brief No-op configuration hook matching the real robot API."""
        return None

    def disconnect(self) -> None:
        """@brief Mark the mock robot as disconnected."""
        self._is_connected = False

    def reset(self) -> None:
        """@brief Restore the initial state and count the reset."""
        self._state = self._make_initial_state()
        self.reset_count += 1

    def get_observation(self) -> dict[str, float]:
        """@brief Return a copy of the current mock state."""
        if not self._is_connected:
            raise RuntimeError("MockCustomManipulator is not connected.")
        return dict(self._state)

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """@brief Apply an action to the mock state and record it."""
        if not self._is_connected:
            raise RuntimeError("MockCustomManipulator is not connected.")

        action_copy = dict(action)
        self.sent_actions.append(action_copy)

        if self.config.arm.use_delta_actions:
            for key in _ACTION_KEYS:
                self._state[key] += float(action_copy.get(key, 0.0))
        else:
            for key in _ACTION_KEYS:
                if key in action_copy:
                    self._state[key] = float(action_copy[key])

        if "gripper" in action_copy:
            self._state["gripper"] = float(action_copy["gripper"])

        return action_copy


@dataclass
class CommandResult:
    """@brief Mock executor result with the same shape as the real executor."""

    success: bool
    status: str
    elapsed_s: float
    message: str


@dataclass
class MockRunNamedCommandRequest:
    """@brief In-process representation of a `RunNamedCommand` request."""

    kind: str
    name: str
    timeout_s: float = 0.0


@dataclass
class MockRunNamedCommandResponse:
    """@brief In-process representation of a `RunNamedCommand` response."""

    success: bool
    status: str
    elapsed_s: float
    message: str


@dataclass
class MockVlmStateRequest:
    """@brief In-process representation of a VLM state request."""

    skill_name: str


@dataclass
class MockVlmStateResponse:
    """@brief In-process representation of a VLM state response."""

    has_attempt: bool
    attempt_id: int
    status: str
    message: str


@dataclass
class MockLegacyVlmResultRequest:
    """@brief In-process representation of a legacy VLM result request."""

    skill_name: str
    status: str
    attempt_id: int = 0
    message: str = ""


@dataclass
class MockLegacyVlmResultResponse:
    """@brief In-process representation of a legacy VLM result response."""

    accepted: bool
    applied_attempt_id: int
    message: str


@dataclass
class MockSkillRuntime:
    """@brief Cached runtime state for one mock skill."""

    cfg: MockSkillConfig
    step_count: int = 0

    def reset(self) -> None:
        """@brief Clear per-attempt mock step count."""
        self.step_count = 0


class MockSkillCommandExecutor:
    """@brief In-process command executor used by the simulation harness."""

    def __init__(self, cfg: MockServerConfig, robot: MockCustomManipulator):
        """@brief Index skill configs and keep the mock robot."""
        self.cfg = cfg
        self.robot = robot
        self.skill_configs = {skill.name: skill for skill in cfg.skills}
        self._skills: dict[str, MockSkillRuntime] = {}
        self._command_lock = Lock()

    def _get_skill_runtime(self, skill_name: str) -> MockSkillRuntime:
        """@brief Return cached mock runtime state for a skill."""
        if skill_name not in self._skills:
            self._skills[skill_name] = MockSkillRuntime(cfg=self.skill_configs[skill_name])
        return self._skills[skill_name]

    def execute_skill(
        self,
        skill_name: str,
        robot_action_processor: Any | None = None,
        robot_observation_processor: Any | None = None,
        timeout_override_s: float = 0.0,
    ) -> CommandResult:
        """@brief Simulate executing one learned skill."""
        del robot_action_processor, robot_observation_processor

        if skill_name not in self.skill_configs:
            return CommandResult(False, "ERROR", 0.0, f"Unknown skill '{skill_name}'.")

        with self._command_lock:
            skill = self._get_skill_runtime(skill_name)
            skill.reset()

            target_dt_s = 1.0 / self.cfg.fps
            elapsed_s = skill.cfg.settle_time_s

            if skill.cfg.transition.mode == "until_success":
                obs = self.robot.get_observation()
                self._run_skill_step(skill, obs)
                skill.step_count += 1
                elapsed_s += target_dt_s
                message = f"Skill '{skill_name}' completed in {elapsed_s:.2f}s."
                return CommandResult(True, "SUCCESS", elapsed_s, message)

            timeout_s = timeout_override_s if timeout_override_s > 0 else skill.cfg.transition.max_duration_s

            while elapsed_s < timeout_s:
                obs = self.robot.get_observation()
                self._run_skill_step(skill, obs)
                skill.step_count += 1
                elapsed_s += target_dt_s

            if skill.cfg.transition.mode == "all_conditions":
                message = f"Skill '{skill_name}' failed after {elapsed_s:.2f}s."
                return CommandResult(False, "FAILURE", elapsed_s, message)

            message = f"Skill '{skill_name}' completed in {elapsed_s:.2f}s."
            return CommandResult(True, "SUCCESS", elapsed_s, message)

    def _run_skill_step(self, skill: MockSkillRuntime, obs: dict[str, float]) -> None:
        """@brief Mutate the mock robot as though one policy step ran."""
        step_size = self.robot.config.arm.step_size
        if self.robot.config.arm.use_delta_actions:
            action = {
                "position.x": step_size,
                "position.y": step_size / 2,
                "position.z": step_size / 4,
                "orientation.x": step_size / 10,
                "orientation.y": step_size / 10,
                "orientation.z": step_size / 10,
                "gripper": obs["gripper"],
            }
        else:
            action = {
                "position.x": float(obs["position.x"] + step_size),
                "position.y": float(obs["position.y"] + step_size / 2),
                "position.z": float(obs["position.z"] + step_size / 4),
                "orientation.x": float(obs["orientation.x"] + step_size / 10),
                "orientation.y": float(obs["orientation.y"] + step_size / 10),
                "orientation.z": float(obs["orientation.z"] + step_size / 10),
                "gripper": obs["gripper"],
            }

        self.robot.send_action(action)


class MockRunNamedCommandService:
    """@brief Tiny stand-in for the ROS2 `RunNamedCommand` service."""

    def __init__(
        self,
        executor: MockSkillCommandExecutor,
        *,
        auto_vlm_result_status: str | None = None,
        scripted_responses: dict[tuple[str, str], list[MockRunNamedCommandResponse]] | None = None,
    ):
        """@brief Store executor, service/topic names, scripts, and VLM check registry."""
        self.executor = executor
        self.bt_command_service = executor.cfg.bt_command_service
        self.vlm_state_service = executor.cfg.vlm_state_service
        self.legacy_vlm_result_service = executor.cfg.legacy_vlm_result_service
        self.vlm_request_topic = executor.cfg.vlm_request_topic
        self.vlm_result_topic = executor.cfg.vlm_result_topic
        self.auto_vlm_result_status = auto_vlm_result_status
        self.scripted_responses = scripted_responses if scripted_responses is not None else {}
        self.request_log: list[MockRunNamedCommandRequest] = []
        self.vlm_check_registry = VlmCheckRegistry(
            known_skill_names=set(executor.skill_configs),
            vlm_timeout_s=executor.cfg.vlm_timeout_s,
        )

    def handle_request(self, request: MockRunNamedCommandRequest) -> MockRunNamedCommandResponse:
        """@brief Execute or script one mock named-command request."""
        self.request_log.append(request)
        scripted_queue = self.scripted_responses.get((request.kind, request.name))
        if scripted_queue:
            return scripted_queue.pop(0)

        if request.kind == "skill":
            result = self.executor.execute_skill(request.name, timeout_override_s=request.timeout_s)
        elif request.kind == SIMULATED_SKILL_KIND:
            self.vlm_check_registry.register_skill_name(request.name)
            result = CommandResult(
                True,
                "SUCCESS",
                0.0,
                f"Simulated skill '{request.name}' completed without mock robot execution.",
            )
        elif request.kind == SIMULATED_SKILL_PENDING_KIND:
            self.vlm_check_registry.register_skill_name(request.name)
            result = CommandResult(
                True,
                "SUCCESS",
                0.0,
                f"Simulated skill '{request.name}' completed and is awaiting a VLM result.",
            )
        else:
            result = CommandResult(
                False,
                "ERROR",
                0.0,
                f"Unsupported command kind '{request.kind}'.",
            )

        if request.kind in _COMMAND_KINDS_THAT_OPEN_VLM_CHECK and result.success:
            snapshot = self.vlm_check_registry.begin_attempt(request.name)
            result.message = (
                f"{result.message} VLM check attempt {snapshot.attempt_id} is now pending on "
                f"'{self.vlm_request_topic}'."
            )
            if self.auto_vlm_result_status is not None:
                auto_update = self.vlm_check_registry.report(
                    skill_name=request.name,
                    attempt_id=snapshot.attempt_id,
                    status=self.auto_vlm_result_status,
                    message=f"Mock VLM auto-reported {self.auto_vlm_result_status} for skill '{request.name}'.",
                )
                result.message = f"{result.message} {auto_update.message}"

        return MockRunNamedCommandResponse(
            success=result.success,
            status=result.status,
            elapsed_s=result.elapsed_s,
            message=result.message,
        )

    def handle_get_vlm_state(
        self,
        request: MockVlmStateRequest,
    ) -> MockVlmStateResponse:
        """@brief Return mock VLM check state for a skill."""
        try:
            snapshot = self.vlm_check_registry.get_latest(request.skill_name)
        except ValueError as exc:
            return MockVlmStateResponse(
                has_attempt=False,
                attempt_id=0,
                status=VLM_UNKNOWN,
                message=str(exc),
            )
        if snapshot is None:
            return MockVlmStateResponse(
                has_attempt=False,
                attempt_id=0,
                status=VLM_UNKNOWN,
                message=f"No completed attempt has been recorded yet for skill '{request.skill_name}'.",
            )

        return MockVlmStateResponse(
            has_attempt=True,
            attempt_id=snapshot.attempt_id,
            status=snapshot.status,
            message=snapshot.message,
        )

    def handle_legacy_vlm_result(
        self,
        request: MockLegacyVlmResultRequest,
    ) -> MockLegacyVlmResultResponse:
        """@brief Apply a mock external verifier verdict."""
        try:
            update = self.vlm_check_registry.report(
                skill_name=request.skill_name,
                attempt_id=request.attempt_id,
                status=request.status,
                message=request.message,
            )
        except ValueError as exc:
            return MockLegacyVlmResultResponse(
                accepted=False,
                applied_attempt_id=0,
                message=str(exc),
            )
        return MockLegacyVlmResultResponse(
            accepted=update.accepted,
            applied_attempt_id=0 if update.snapshot is None else update.snapshot.attempt_id,
            message=update.message,
        )


def build_demo_stack(
    use_delta_actions: bool = False,
    fps: int = 10,
    bt_command_service: str = "/sandwich_bt/run",
    auto_vlm_result_status: str | None = None,
    scripted_responses: dict[tuple[str, str], list[MockRunNamedCommandResponse]] | None = None,
) -> MockRunNamedCommandService:
    """@brief Build the default in-process mock sandwich command stack."""
    robot = MockCustomManipulator(
        MockRobotConfig(
            arm=MockRobotArmConfig(use_delta_actions=use_delta_actions, step_size=0.01),
            initial_gripper=0.0,
        )
    )
    robot.connect()
    robot.reset()

    cfg = MockServerConfig(
        fps=fps,
        bt_command_service=bt_command_service,
        skills=[
            MockSkillConfig(
                name="place_first_toast",
                transition=MockSkillTransition(mode="timeout", max_duration_s=0.4),
                settle_time_s=0.0,
            ),
            MockSkillConfig(
                name="place_second_toast",
                transition=MockSkillTransition(mode="timeout", max_duration_s=0.4),
                settle_time_s=0.0,
            ),
        ],
    )
    executor = MockSkillCommandExecutor(cfg=cfg, robot=robot)
    return MockRunNamedCommandService(
        executor,
        auto_vlm_result_status=auto_vlm_result_status,
        scripted_responses=scripted_responses,
    )


def build_ros2_demo_stack(
    use_delta_actions: bool = False,
    fps: int = 10,
    bt_command_service: str = "/sandwich_bt/run",
) -> MockRunNamedCommandService:
    """@brief Build a mock stack configured for ROS2 service smoke tests."""
    return build_demo_stack(
        use_delta_actions=use_delta_actions,
        fps=fps,
        bt_command_service=bt_command_service,
        auto_vlm_result_status="SUCCESS",
    )


def default_command_sequence() -> list[MockRunNamedCommandRequest]:
    """@brief Return the default VLM-gated sequence for a full sandwich."""
    return [
        MockRunNamedCommandRequest(kind=SIMULATED_SKILL_PENDING_KIND, name="initial_scene_ready"),
        MockRunNamedCommandRequest(kind="skill", name="place_first_toast"),
        MockRunNamedCommandRequest(kind=SIMULATED_SKILL_PENDING_KIND, name="pour_ingredient"),
        MockRunNamedCommandRequest(kind="skill", name="place_second_toast"),
    ]


def parse_command_spec(spec: str) -> MockRunNamedCommandRequest:
    """@brief Parse CLI text of the form `kind:name[:timeout_s]`."""
    parts = spec.split(":")
    if len(parts) not in {2, 3}:
        raise argparse.ArgumentTypeError("Commands must use the form kind:name or kind:name:timeout_s.")

    kind, name = parts[0].strip(), parts[1].strip()
    timeout_s = float(parts[2]) if len(parts) == 3 and parts[2].strip() else 0.0

    valid_kinds = {"skill", SIMULATED_SKILL_KIND, SIMULATED_SKILL_PENDING_KIND}
    if kind not in valid_kinds:
        raise argparse.ArgumentTypeError(f"kind must be one of {sorted(valid_kinds)}.")
    if not name:
        raise argparse.ArgumentTypeError("name must not be empty.")
    if timeout_s < 0:
        raise argparse.ArgumentTypeError("timeout_s must be >= 0.")

    return MockRunNamedCommandRequest(kind=kind, name=name, timeout_s=timeout_s)


def run_requests(
    service: MockRunNamedCommandService,
    requests: Sequence[MockRunNamedCommandRequest],
) -> list[MockRunNamedCommandResponse]:
    """@brief Run a list of in-process requests against the mock service."""
    responses: list[MockRunNamedCommandResponse] = []
    for request in requests:
        responses.append(service.handle_request(request))
    return responses


def _format_response(request: MockRunNamedCommandRequest, response: MockRunNamedCommandResponse) -> str:
    """@brief Format one request/response pair for the CLI."""
    return (
        f"{request.kind}:{request.name} -> {response.status} ({response.elapsed_s:.2f}s) {response.message}"
    )


def run_ros2_service(
    service: MockRunNamedCommandService,
) -> int:
    """@brief Expose the mock command service as live ROS2 services."""
    try:
        import rclpy
        from rclpy.executors import ExternalShutdownException
        from rclpy.node import Node
        from std_msgs.msg import String

        from sandwich_bt_python.server import _load_bt_services

        bt_command_service_type, vlm_state_service_type, legacy_vlm_result_service_type = _load_bt_services()
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on ROS2 install
        raise RuntimeError(
            "ROS2 simulation mode requires rclpy and sandwich_bt_interfaces. "
            "Source the ROS workspace and build sandwich_bt_interfaces before running --ros2-service."
        ) from exc
    except ImportError as exc:  # pragma: no cover - depends on ROS2/generated interfaces
        raise RuntimeError(
            "ROS2 simulation mode could not load the generated sandwich_bt_interfaces bindings. "
            "Run a ROS2 build for sandwich_bt_interfaces, then source install/local_setup.bash."
        ) from exc

    class MockRunNamedCommandNode(Node):
        """@brief ROS2 adapter that forwards generated service calls to the mock."""

        def __init__(self) -> None:
            """@brief Register command, VLM state, legacy VLM result services, and VLM topics."""
            super().__init__("sandwich_bt_skill_server_sim")
            self._service_impl = service
            self._bt_command_server = self.create_service(
                bt_command_service_type,
                service.bt_command_service,
                self._handle_request,
            )
            self._vlm_state_server = self.create_service(
                vlm_state_service_type,
                service.vlm_state_service,
                self._handle_get_vlm_state,
            )
            self._legacy_vlm_result_server = self.create_service(
                legacy_vlm_result_service_type,
                service.legacy_vlm_result_service,
                self._handle_legacy_vlm_result,
            )
            self._vlm_request_publisher = self.create_publisher(
                String,
                service.vlm_request_topic,
                10,
            )
            self._vlm_result_subscription = self.create_subscription(
                String,
                service.vlm_result_topic,
                self._handle_vlm_result_topic,
                10,
            )
            self.get_logger().info(
                f"Serving mock BT commands on '{service.bt_command_service}', "
                f"VLM requests on '{service.vlm_request_topic}', "
                f"and VLM results from '{service.vlm_result_topic}'."
            )

        def _handle_request(self, request, response):
            """@brief Convert generated ROS request/response objects to mock objects."""
            result = self._service_impl.handle_request(
                MockRunNamedCommandRequest(
                    kind=request.kind,
                    name=request.name,
                    timeout_s=float(request.timeout_s),
                )
            )
            response.success = result.success
            response.status = result.status
            response.elapsed_s = float(result.elapsed_s)
            response.message = result.message
            self._publish_vlm_request_if_waiting(request)
            return response

        def _handle_get_vlm_state(self, request, response):
            """@brief Convert a generated VLM state request into a mock request."""
            result = self._service_impl.handle_get_vlm_state(
                MockVlmStateRequest(skill_name=request.skill_name)
            )
            response.has_attempt = bool(result.has_attempt)
            response.attempt_id = int(result.attempt_id)
            response.status = result.status
            response.message = result.message
            return response

        def _handle_legacy_vlm_result(self, request, response):
            """@brief Convert a generated verifier report into a mock report."""
            result = self._service_impl.handle_legacy_vlm_result(
                MockLegacyVlmResultRequest(
                    skill_name=request.skill_name,
                    status=request.status,
                    attempt_id=int(request.attempt_id),
                    message=request.message,
                )
            )
            response.accepted = bool(result.accepted)
            response.applied_attempt_id = int(result.applied_attempt_id)
            response.message = result.message
            return response

        def _publish_vlm_request_if_waiting(self, request) -> None:
            """@brief Emit the same topic request as the real server after opening a gate."""
            if request.kind not in _COMMAND_KINDS_THAT_OPEN_VLM_CHECK:
                return
            try:
                snapshot = self._service_impl.vlm_check_registry.get_latest(request.name)
            except ValueError:
                return
            if snapshot is None or snapshot.status not in VLM_WAITING_STATUSES:
                return
            payload = {
                "event": "vlm_check_requested",
                "skill_name": snapshot.skill_name,
                "attempt_id": int(snapshot.attempt_id),
                "status": snapshot.status,
                "message": snapshot.message,
                "allowed_statuses": [
                    "PENDING",
                    "RUNNING",
                    "WAIT_HUMAN",
                    "MANUAL_INTERVENTION_REQUIRED",
                    "SUCCESS",
                    "FAILURE",
                ],
                "allowed_next_actions": [
                    "CONTINUE",
                    "RETRY_SKILL",
                    "WAIT_HUMAN",
                    "REQUEST_MANUAL_INTERVENTION",
                ],
            }
            msg = String()
            msg.data = json.dumps(payload, sort_keys=True)
            self._vlm_request_publisher.publish(msg)

        def _handle_vlm_result_topic(self, msg) -> None:
            """@brief Apply a verifier report published on the same topic as real mode."""
            try:
                payload = json.loads(msg.data)
            except Exception as exc:  # noqa: BLE001
                self.get_logger().error(f"Invalid VLM result JSON: {exc}: '{msg.data}'")
                return
            if not isinstance(payload, dict):
                self.get_logger().error("Rejected VLM result topic message: payload must be a JSON object.")
                return

            try:
                result = self._service_impl.handle_legacy_vlm_result(
                    MockLegacyVlmResultRequest(
                        skill_name=str(payload.get("skill_name", "")),
                        status=_vlm_status_from_payload(payload),
                        attempt_id=int(payload.get("attempt_id", 0)),
                        message=_vlm_message_from_payload(
                            payload,
                            status=_vlm_status_from_payload(payload),
                        ),
                    )
                )
            except (TypeError, ValueError) as exc:
                self.get_logger().error(f"Rejected VLM result topic message: {exc}")
                return
            log_fn = self.get_logger().info if result.accepted else self.get_logger().warning
            log_fn(result.message)

    if not rclpy.ok():
        rclpy.init()

    node = MockRunNamedCommandNode()
    try:
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            node.get_logger().info("Mock BT command service interrupted, shutting down.")
        except ExternalShutdownException:
            print("Mock BT command service stopped, shutting down.")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """@brief CLI entry point for in-process or ROS2 mock execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--command",
        action="append",
        dest="commands",
        help="Command in the form kind:name or kind:name:timeout_s.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=10,
        help="Virtual control frequency used by the mock executor.",
    )
    parser.add_argument(
        "--delta-actions",
        action="store_true",
        help="Interpret mock skill actions as delta commands.",
    )
    parser.add_argument(
        "--ros2-service",
        action="store_true",
        help="Expose the mock command handler as a ROS2 service so the C++ BT runner can connect to it.",
    )
    parser.add_argument(
        "--bt-command-service",
        "--service-name",
        dest="bt_command_service",
        default="/sandwich_bt/run",
        help="ROS2 service where the C++ BT sends skill/gate commands in --ros2-service mode.",
    )
    args = parser.parse_args(argv)

    if args.ros2_service and args.commands:
        parser.error("--command is only supported without --ros2-service")

    service = (
        build_ros2_demo_stack(
            use_delta_actions=args.delta_actions,
            fps=args.fps,
            bt_command_service=args.bt_command_service,
        )
        if args.ros2_service
        else build_demo_stack(use_delta_actions=args.delta_actions, fps=args.fps)
    )

    if args.ros2_service:
        return run_ros2_service(service)

    requests = (
        [parse_command_spec(command) for command in args.commands]
        if args.commands
        else default_command_sequence()
    )
    responses = run_requests(service, requests)

    for request, response in zip(requests, responses, strict=True):
        print(_format_response(request, response))

    robot = service.executor.robot
    observation = robot.get_observation()
    print(
        "robot_state="
        f"{{'position.x': {observation['position.x']:.3f}, "
        f"'position.y': {observation['position.y']:.3f}, "
        f"'position.z': {observation['position.z']:.3f}, "
        f"'gripper': {observation['gripper']:.3f}}}"
    )
    print(f"actions_sent={len(robot.sent_actions)} resets={robot.reset_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
