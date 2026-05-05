"""@file __init__.py
@brief Public package surface for the collaborative sandwich supervisor.

@details The imports below collect the supervisor's main data models, clients,
mock backends, and orchestration classes at package level. This lets callers use
`sandwich_bt_supervisor.SupervisorConfig` and related symbols without knowing the
internal module layout.
"""

# Behavior-tree XML execution helpers used by robot-assigned supervisor steps.
from .bt_executor import BtXmlRobotExecutor, ExecutedBtCommand, default_subtree_path
# Runner/client utilities that coordinate robot and human work.
from .collaborative_runner import CollaborativeRunner, SupervisorRos2Client, build_mock_collaborative_runner
# Human-step executor abstraction.
from .human_interface import HumanCommandExecutor
# Backends that invoke named robot commands either in process or through ROS2.
from .named_command_backends import (
    InProcessMockNamedCommandBackend,
    NamedCommandBackend,
    NamedCommandRequest,
    NamedCommandResult,
    NamedCommandServiceUnavailableError,
    Ros2NamedCommandBackend,
)
# Dataclasses that describe planner decisions, execution, and results.
from .planner_schema import (
    ExecutedSupervisorStep,
    PlanStepDecision,
    SceneEstimate,
    StepExecutionResult,
    StepVerification,
    SupervisorConfig,
    SupervisorRunResult,
    TaskPrimitive,
)
# Scene observation and estimation primitives.
from .scene_state import SandwichSceneEstimator, SandwichSceneObservation
# ROS2 supervisor service backend and node wrapper.
from .server import SandwichSupervisorServer, SupervisorServiceBackend
# Demo-stack construction helpers.
from .simulation import build_demo_supervisor_stack, make_demo_supervisor_config
# Closed-set task allocator.
from .task_allocator import SandwichTaskAllocator
# High-level collaborative supervisor orchestration.
from .vlm_supervisor import CollaborativeSandwichSupervisor

# Explicit package exports; keep this list synchronized with the imports above.
__all__ = [
    "BtXmlRobotExecutor",
    "CollaborativeRunner",
    "CollaborativeSandwichSupervisor",
    "ExecutedBtCommand",
    "ExecutedSupervisorStep",
    "HumanCommandExecutor",
    "InProcessMockNamedCommandBackend",
    "NamedCommandBackend",
    "NamedCommandRequest",
    "NamedCommandResult",
    "NamedCommandServiceUnavailableError",
    "PlanStepDecision",
    "Ros2NamedCommandBackend",
    "SandwichSceneEstimator",
    "SandwichSceneObservation",
    "SandwichSupervisorServer",
    "SandwichTaskAllocator",
    "SceneEstimate",
    "StepExecutionResult",
    "StepVerification",
    "SupervisorServiceBackend",
    "SupervisorConfig",
    "SupervisorRunResult",
    "TaskPrimitive",
    "SupervisorRos2Client",
    "build_demo_supervisor_stack",
    "build_mock_collaborative_runner",
    "default_subtree_path",
    "make_demo_supervisor_config",
]
