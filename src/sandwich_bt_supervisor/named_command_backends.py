"""@file named_command_backends.py
@brief Named-command backends for BT subtree execution."""

from __future__ import annotations

from dataclasses import dataclass

from rclpy.node import Node

from lerobot.robots.custom_manipulator.ros_spin import spin_until_future_complete
from sandwich_bt_python.simulation import (
    MockRunNamedCommandRequest,
    MockRunNamedCommandService,
)

from .ros_services import load_run_named_command_service


@dataclass(frozen=True)
class NamedCommandRequest:
    """@brief Value object for one command generated from BT XML."""

    kind: str
    name: str
    timeout_s: float = 0.0


@dataclass(frozen=True)
class NamedCommandResult:
    """@brief Backend-independent result of one named command."""

    success: bool
    status: str
    elapsed_s: float
    message: str


class NamedCommandBackend:
    """@brief Interface implemented by in-process and ROS2 command backends."""

    def run_named_command(
        self,
        *,
        kind: str,
        name: str,
        timeout_s: float,
    ) -> NamedCommandResult:
        """@brief Execute one named command and return its result."""
        raise NotImplementedError


class NamedCommandServiceUnavailableError(RuntimeError):
    """Raised when the live RunNamedCommand service cannot be reached."""


class InProcessMockNamedCommandBackend(NamedCommandBackend):
    """@brief Backend that calls the mock Python service directly."""

    def __init__(self, service: MockRunNamedCommandService) -> None:
        """@brief Store the in-process mock service implementation."""
        self.service = service

    def run_named_command(
        self,
        *,
        kind: str,
        name: str,
        timeout_s: float,
    ) -> NamedCommandResult:
        """@brief Convert a backend call into an in-process mock request."""
        response = self.service.handle_request(
            MockRunNamedCommandRequest(kind=kind, name=name, timeout_s=timeout_s)
        )
        return NamedCommandResult(
            success=response.success,
            status=response.status,
            elapsed_s=float(response.elapsed_s),
            message=response.message,
        )


class Ros2NamedCommandBackend(Node, NamedCommandBackend):
    """@brief Backend that calls the live `/sandwich_bt/run_command` service."""

    def __init__(
        self,
        *,
        service_name: str = "/sandwich_bt/run_command",
    ) -> None:
        """@brief Create a ROS2 client for `RunNamedCommand`."""
        super().__init__(
            "sandwich_bt_named_command_client",
            start_parameter_services=False,
            enable_logger_service=False,
        )
        self.service_name = service_name
        service_type = load_run_named_command_service()
        self._client = self.create_client(service_type, service_name)
        self._service_type = service_type

    def wait_for_service(self, timeout_s: float = 5.0) -> None:
        """@brief Wait until the live named-command service is available."""
        if not self._client.wait_for_service(timeout_sec=timeout_s):
            raise NamedCommandServiceUnavailableError(
                f"RunNamedCommand service '{self.service_name}' is not available."
            )

    def run_named_command(
        self,
        *,
        kind: str,
        name: str,
        timeout_s: float,
    ) -> NamedCommandResult:
        """@brief Send one live ROS2 `RunNamedCommand` request."""
        request = self._service_type.Request()
        request.kind = kind
        request.name = name
        request.timeout_s = float(timeout_s)

        future = self._client.call_async(request)
        spin_until_future_complete(self, future)
        response = future.result()
        if response is None:
            raise NamedCommandServiceUnavailableError(
                f"RunNamedCommand service '{self.service_name}' returned no response."
            )

        return NamedCommandResult(
            success=bool(response.success),
            status=response.status,
            elapsed_s=float(response.elapsed_s),
            message=response.message,
        )
