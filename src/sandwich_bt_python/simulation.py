"""Simulation helpers for sandwich BT command execution."""

"""Hardware-free simulation harness for the sandwich BT stack.

This module keeps the BT command contract intact without importing ROS2 or any
robot drivers. It is intended for local smoke tests of the named-command flow.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

_ACTION_KEYS = (
    "position.x",
    "position.y",
    "position.z",
    "orientation.x",
    "orientation.y",
    "orientation.z",
)


@dataclass
class MockSkillTransition:
    mode: str = "timeout"
    min_duration_s: float = 0.0
    max_duration_s: float = 0.5

    def __post_init__(self) -> None:
        allowed_modes = {"timeout", "all_conditions", "all_conditions_or_timeout"}
        if self.mode not in allowed_modes:
            raise ValueError(f"Unsupported mode '{self.mode}'. Expected one of {sorted(allowed_modes)}.")
        if self.min_duration_s < 0:
            raise ValueError("min_duration_s must be >= 0.")
        if self.max_duration_s <= 0:
            raise ValueError("max_duration_s must be > 0.")


@dataclass
class MockSkillConfig:
    name: str
    transition: MockSkillTransition = field(default_factory=MockSkillTransition)
    settle_time_s: float = 0.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Skill name must not be empty.")
        if self.settle_time_s < 0:
            raise ValueError("settle_time_s must be >= 0.")


@dataclass
class MockRecoveryStep:
    kind: str
    duration_s: float = 0.0
    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0
    droll: float = 0.0
    dpitch: float = 0.0
    dyaw: float = 0.0
    gripper_value: float | None = None

    def __post_init__(self) -> None:
        allowed_kinds = {"pause", "robot_reset", "cartesian_delta", "set_gripper"}
        if self.kind not in allowed_kinds:
            raise ValueError(
                f"Unsupported recovery step '{self.kind}'. Expected one of {sorted(allowed_kinds)}."
            )
        if self.kind != "robot_reset" and self.duration_s < 0:
            raise ValueError("duration_s must be >= 0.")
        if self.kind == "set_gripper" and self.gripper_value is None:
            raise ValueError("set_gripper steps require gripper_value.")


@dataclass
class MockRecoveryConfig:
    name: str
    steps: list[MockRecoveryStep] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Recovery name must not be empty.")
        if not self.steps:
            raise ValueError(f"Recovery '{self.name}' must define at least one step.")


@dataclass
class MockServerConfig:
    fps: int = 10
    service_name: str = "/sandwich_bt/run_command"
    display_data: bool = False
    play_sounds: bool = False
    rename_map: dict[str, str] = field(default_factory=dict)
    skills: list[MockSkillConfig] = field(default_factory=list)
    recoveries: list[MockRecoveryConfig] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.fps <= 0:
            raise ValueError("fps must be > 0.")
        if not self.skills:
            raise ValueError("At least one skill must be configured.")


@dataclass
class MockRobotArmConfig:
    use_delta_actions: bool = False
    step_size: float = 0.01
    initial_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    initial_orientation: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        if self.step_size <= 0:
            raise ValueError("step_size must be > 0.")


@dataclass
class MockRobotConfig:
    arm: MockRobotArmConfig = field(default_factory=MockRobotArmConfig)
    initial_gripper: float = 0.0


class MockGripperInterface:
    def __init__(self, robot: MockCustomManipulator):
        self.robot = robot

    def apply_commands(self, commands: dict[str, Any] | float) -> None:
        if isinstance(commands, dict):
            if "gripper" in commands:
                self.robot._state["gripper"] = float(commands["gripper"])
            return
        self.robot._state["gripper"] = float(commands)


class MockCustomManipulator:
    """Small in-memory stand-in for the real custom manipulator."""

    robot_type = "mock_custom_manipulator"

    def __init__(self, config: MockRobotConfig | None = None):
        self.config = config if config is not None else MockRobotConfig()
        self._is_connected = False
        self._state = self._make_initial_state()
        self.reset_count = 0
        self.sent_actions: list[dict[str, float]] = []
        self.gripper_interface = MockGripperInterface(self)

    def _make_initial_state(self) -> dict[str, float]:
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
        return dict.fromkeys(self._state, float)

    @property
    def action_features(self) -> dict[str, type]:
        return dict.fromkeys(self._state, float)

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def is_calibrated(self) -> bool:
        return True

    def connect(self, calibrate: bool = True) -> None:
        self._is_connected = True

    def calibrate(self) -> None:
        return None

    def configure(self) -> None:
        return None

    def disconnect(self) -> None:
        self._is_connected = False

    def reset(self) -> None:
        self._state = self._make_initial_state()
        self.reset_count += 1

    def get_observation(self) -> dict[str, float]:
        if not self._is_connected:
            raise RuntimeError("MockCustomManipulator is not connected.")
        return dict(self._state)

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
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
    success: bool
    status: str
    elapsed_s: float
    message: str


@dataclass
class MockRunNamedCommandRequest:
    kind: str
    name: str
    timeout_s: float = 0.0


@dataclass
class MockRunNamedCommandResponse:
    success: bool
    status: str
    elapsed_s: float
    message: str


@dataclass
class MockSkillRuntime:
    cfg: MockSkillConfig
    step_count: int = 0

    def reset(self) -> None:
        self.step_count = 0


class MockSkillCommandExecutor:
    """In-process command executor used by the simulation harness."""

    def __init__(self, cfg: MockServerConfig, robot: MockCustomManipulator):
        self.cfg = cfg
        self.robot = robot
        self.skill_configs = {skill.name: skill for skill in cfg.skills}
        self.recoveries = {recovery.name: recovery for recovery in cfg.recoveries}
        self._skills: dict[str, MockSkillRuntime] = {}
        self._command_lock = Lock()

    def _get_skill_runtime(self, skill_name: str) -> MockSkillRuntime:
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
        del robot_action_processor, robot_observation_processor

        if skill_name not in self.skill_configs:
            return CommandResult(False, "ERROR", 0.0, f"Unknown skill '{skill_name}'.")

        with self._command_lock:
            skill = self._get_skill_runtime(skill_name)
            skill.reset()

            target_dt_s = 1.0 / self.cfg.fps
            timeout_s = timeout_override_s if timeout_override_s > 0 else skill.cfg.transition.max_duration_s
            elapsed_s = skill.cfg.settle_time_s

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

    def execute_named_recovery(self, recovery_name: str, timeout_override_s: float = 0.0) -> CommandResult:
        if recovery_name not in self.recoveries:
            return CommandResult(False, "ERROR", 0.0, f"Unknown recovery '{recovery_name}'.")

        with self._command_lock:
            elapsed_s = 0.0
            recovery_cfg = self.recoveries[recovery_name]

            for step in recovery_cfg.steps:
                step_duration = timeout_override_s if timeout_override_s > 0 else step.duration_s
                elapsed_s += step_duration

                if step.kind == "pause":
                    continue

                if step.kind == "robot_reset":
                    self.robot.reset()
                    continue

                if step.kind == "set_gripper":
                    self.robot.gripper_interface.apply_commands({"gripper": float(step.gripper_value)})
                    continue

                if step.kind == "cartesian_delta":
                    current = self.robot.get_observation()
                    if self.robot.config.arm.use_delta_actions:
                        action = {
                            "position.x": float(step.dx),
                            "position.y": float(step.dy),
                            "position.z": float(step.dz),
                            "orientation.x": float(step.droll),
                            "orientation.y": float(step.dpitch),
                            "orientation.z": float(step.dyaw),
                            "gripper": float(
                                current["gripper"] if step.gripper_value is None else step.gripper_value
                            ),
                        }
                    else:
                        action = {
                            "position.x": float(current["position.x"] + step.dx),
                            "position.y": float(current["position.y"] + step.dy),
                            "position.z": float(current["position.z"] + step.dz),
                            "orientation.x": float(current["orientation.x"] + step.droll),
                            "orientation.y": float(current["orientation.y"] + step.dpitch),
                            "orientation.z": float(current["orientation.z"] + step.dyaw),
                            "gripper": float(
                                current["gripper"] if step.gripper_value is None else step.gripper_value
                            ),
                        }

                    self.robot.send_action(action)
                    continue

                return CommandResult(
                    False,
                    "ERROR",
                    elapsed_s,
                    f"Unsupported recovery step '{step.kind}'.",
                )

            message = f"Recovery '{recovery_name}' completed in {elapsed_s:.2f}s."
            return CommandResult(True, "SUCCESS", elapsed_s, message)

    def _run_skill_step(self, skill: MockSkillRuntime, obs: dict[str, float]) -> None:
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
    """Tiny stand-in for the ROS2 `RunNamedCommand` service."""

    def __init__(
        self,
        executor: MockSkillCommandExecutor,
        *,
        scripted_responses: dict[tuple[str, str], list[MockRunNamedCommandResponse]] | None = None,
    ):
        self.executor = executor
        self.service_name = executor.cfg.service_name
        self.scripted_responses = scripted_responses if scripted_responses is not None else {}
        self.request_log: list[MockRunNamedCommandRequest] = []

    def handle_request(self, request: MockRunNamedCommandRequest) -> MockRunNamedCommandResponse:
        self.request_log.append(request)
        scripted_queue = self.scripted_responses.get((request.kind, request.name))
        if scripted_queue:
            return scripted_queue.pop(0)

        if request.kind == "skill":
            result = self.executor.execute_skill(request.name, timeout_override_s=request.timeout_s)
        elif request.kind == "recovery":
            result = self.executor.execute_named_recovery(request.name, timeout_override_s=request.timeout_s)
        else:
            result = CommandResult(
                False,
                "ERROR",
                0.0,
                f"Unsupported command kind '{request.kind}'.",
            )

        return MockRunNamedCommandResponse(
            success=result.success,
            status=result.status,
            elapsed_s=result.elapsed_s,
            message=result.message,
        )


def build_demo_stack(
    use_delta_actions: bool = False,
    fps: int = 10,
    service_name: str = "/sandwich_bt/run_command",
    scripted_responses: dict[tuple[str, str], list[MockRunNamedCommandResponse]] | None = None,
) -> MockRunNamedCommandService:
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
        service_name=service_name,
        skills=[
            MockSkillConfig(
                name="place_first_toast",
                transition=MockSkillTransition(mode="timeout", max_duration_s=0.4),
                settle_time_s=0.0,
            ),
            MockSkillConfig(
                name="pour",
                transition=MockSkillTransition(mode="timeout", max_duration_s=0.3),
                settle_time_s=0.0,
            ),
            MockSkillConfig(
                name="place_second_toast",
                transition=MockSkillTransition(mode="timeout", max_duration_s=0.4),
                settle_time_s=0.0,
            ),
        ],
        recoveries=[
            MockRecoveryConfig(
                name="recover_place_first_toast",
                steps=[
                    MockRecoveryStep(kind="set_gripper", gripper_value=1.0, duration_s=0.1),
                    MockRecoveryStep(kind="cartesian_delta", dz=0.05, duration_s=0.2),
                    MockRecoveryStep(kind="pause", duration_s=0.1),
                ],
            ),
            MockRecoveryConfig(
                name="recover_pour",
                steps=[
                    MockRecoveryStep(kind="cartesian_delta", dz=0.03, duration_s=0.1),
                    MockRecoveryStep(kind="pause", duration_s=0.1),
                ],
            ),
            MockRecoveryConfig(
                name="recover_place_second_toast",
                steps=[
                    MockRecoveryStep(kind="set_gripper", gripper_value=1.0, duration_s=0.1),
                    MockRecoveryStep(kind="cartesian_delta", dz=0.05, duration_s=0.2),
                    MockRecoveryStep(kind="pause", duration_s=0.1),
                ],
            ),
        ],
    )
    executor = MockSkillCommandExecutor(cfg=cfg, robot=robot)
    return MockRunNamedCommandService(executor, scripted_responses=scripted_responses)


def build_ros2_demo_stack(
    use_delta_actions: bool = False,
    fps: int = 10,
    service_name: str = "/sandwich_bt/run_command",
) -> MockRunNamedCommandService:
    return build_demo_stack(use_delta_actions=use_delta_actions, fps=fps, service_name=service_name)


def default_command_sequence() -> list[MockRunNamedCommandRequest]:
    return [
        MockRunNamedCommandRequest(kind="recovery", name="recover_place_first_toast"),
        MockRunNamedCommandRequest(kind="skill", name="place_first_toast"),
        MockRunNamedCommandRequest(kind="recovery", name="recover_pour"),
        MockRunNamedCommandRequest(kind="skill", name="pour"),
        MockRunNamedCommandRequest(kind="recovery", name="recover_place_second_toast"),
        MockRunNamedCommandRequest(kind="skill", name="place_second_toast"),
    ]


def parse_command_spec(spec: str) -> MockRunNamedCommandRequest:
    parts = spec.split(":")
    if len(parts) not in {2, 3}:
        raise argparse.ArgumentTypeError("Commands must use the form kind:name or kind:name:timeout_s.")

    kind, name = parts[0].strip(), parts[1].strip()
    timeout_s = float(parts[2]) if len(parts) == 3 and parts[2].strip() else 0.0

    if kind not in {"skill", "recovery"}:
        raise argparse.ArgumentTypeError("kind must be either 'skill' or 'recovery'.")
    if not name:
        raise argparse.ArgumentTypeError("name must not be empty.")
    if timeout_s < 0:
        raise argparse.ArgumentTypeError("timeout_s must be >= 0.")

    return MockRunNamedCommandRequest(kind=kind, name=name, timeout_s=timeout_s)


def run_requests(
    service: MockRunNamedCommandService,
    requests: Sequence[MockRunNamedCommandRequest],
) -> list[MockRunNamedCommandResponse]:
    responses: list[MockRunNamedCommandResponse] = []
    for request in requests:
        responses.append(service.handle_request(request))
    return responses


def _format_response(request: MockRunNamedCommandRequest, response: MockRunNamedCommandResponse) -> str:
    return (
        f"{request.kind}:{request.name} -> {response.status} ({response.elapsed_s:.2f}s) {response.message}"
    )


def run_ros2_service(
    service: MockRunNamedCommandService,
) -> int:
    try:
        import rclpy
        from rclpy.node import Node

        from sandwich_bt_interfaces.srv import RunNamedCommand
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on ROS2 install
        raise RuntimeError(
            "ROS2 simulation mode requires rclpy and sandwich_bt_interfaces. "
            "Source the ROS workspace before running --ros2-service."
        ) from exc

    class MockRunNamedCommandNode(Node):
        def __init__(self) -> None:
            super().__init__("sandwich_bt_skill_server_sim")
            self._service_impl = service
            self._service = self.create_service(RunNamedCommand, service.service_name, self._handle_request)
            self.get_logger().info(f"Serving mock BT commands on '{service.service_name}'.")

        def _handle_request(self, request, response):
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
            return response

    if not rclpy.ok():
        rclpy.init()

    node = MockRunNamedCommandNode()
    try:
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            node.get_logger().info("Mock BT command service interrupted, shutting down.")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
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
        help="Interpret cartesian recovery steps as delta actions.",
    )
    parser.add_argument(
        "--ros2-service",
        action="store_true",
        help="Expose the mock command handler as a ROS2 service so the C++ BT runner can connect to it.",
    )
    parser.add_argument(
        "--service-name",
        default="/sandwich_bt/run_command",
        help="ROS2 service name used in --ros2-service mode.",
    )
    args = parser.parse_args(argv)

    if args.ros2_service and args.commands:
        parser.error("--command is only supported without --ros2-service")

    service = (
        build_ros2_demo_stack(
            use_delta_actions=args.delta_actions,
            fps=args.fps,
            service_name=args.service_name,
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
