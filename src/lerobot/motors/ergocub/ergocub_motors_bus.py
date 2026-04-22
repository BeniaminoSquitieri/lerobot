#!/usr/bin/env python

# Copyright 2024 Istituto Italiano di Tecnologia. All rights reserved.
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

import logging
import time

import yarp
from lerobot.robots.ergocub.profiles import CubRobotProfile
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from .head_controller import ErgoCubHeadController
from .finger_controller import ErgoCubFingerController
from .bimanual_controller import ErgoCubBimanualController
from .xela_controller import ErgoCubXelaController

logger = logging.getLogger(__name__)


class ErgoCubMotorsBus:
    """
    YARP-based motors bus for ErgoCub that manages bimanual and head controllers.
    """
    
    def __init__(
        self,
        remote_prefix: str,
        local_prefix: str,
        urdf_path: str,
        profile: CubRobotProfile,
        control_boards: list[str],
        state_boards: list[str],
        left_hand: bool = True,
        right_hand: bool = True,
        finger_scale: float = 1.0,
    ):
        """
        Initialize ErgoCub YARP motors bus.
        
        Args:
            remote_prefix: Remote YARP prefix (e.g., "/ergocubSim")
            local_prefix: Local YARP prefix (e.g., "/lerobot/session_id")
            control_boards: List of control boards to send commands to
            state_boards: List of state boards to read from
        """
        self.remote_prefix = remote_prefix
        self.local_prefix = local_prefix
        self.profile = profile
        self.state_boards = self._normalize_boards(state_boards)
        self.control_boards = self._normalize_boards(control_boards)
        
        # Initialize controllers
        parts_needed = set(self.control_boards) | set(self.state_boards)
        self.controllers = {}
        
        if "bimanual" in parts_needed:
            self.controllers["bimanual"] = ErgoCubBimanualController(
                remote_prefix, local_prefix, urdf_path, profile, left_hand, right_hand
            )
            
        if 'head' in parts_needed:
            self.controllers["head"] = ErgoCubHeadController(remote_prefix, local_prefix, urdf_path, profile)
        
        # Optionally add finger controller
        if 'fingers' in parts_needed:
            self.controllers["fingers"] = ErgoCubFingerController(remote_prefix, local_prefix, finger_scale=finger_scale)

        if "left_xela" in parts_needed:
            self.controllers["left_xela"] = ErgoCubXelaController(local_prefix, side="left")
        if "right_xela" in parts_needed:
            self.controllers["right_xela"] = ErgoCubXelaController(local_prefix, side="right")

    @staticmethod
    def _normalize_boards(boards: list[str]) -> list[str]:
        normalized: list[str] = []
        for board in boards:
            if board == "xela":
                normalized_board = "left_xela"
            elif board == "xela_left":
                normalized_board = "left_xela"
            elif board == "xela_right":
                normalized_board = "right_xela"
            else:
                normalized_board = board
            if normalized_board not in normalized:
                normalized.append(normalized_board)
        return normalized

    @property
    def is_connected(self) -> bool:
        """Check if all controllers are connected."""
        return all(controller.is_connected for controller in self.controllers.values())
    
    def connect(self) -> None:
        """Connect all controllers."""
        if self.is_connected:
            raise DeviceAlreadyConnectedError("ErgoCubMotorsBus already connected")
        
        for name, controller in self.controllers.items():
            logger.info(f"Connecting {name} controller...")
            controller.connect()
        
        logger.info("ErgoCubMotorsBus connected")
    
    def disconnect(self) -> None:
        """Disconnect all controllers."""
        if not self.is_connected:
            raise DeviceNotConnectedError("ErgoCubMotorsBus not connected")
        
        for name, controller in self.controllers.items():
            logger.info(f"Disconnecting {name} controller...")
            controller.disconnect()

        # YARP is initialized by multiple wrappers in this process (robot, cameras,
        # teleoperator). Calling fini() here can tear down global state while other
        # YARP-backed objects are still being destroyed, which has caused shutdown
        # segfaults after a successful recording.
        logger.info("ErgoCubMotorsBus disconnected")
    
    def read_state(self) -> dict[str, float]:
        """Read current state from all controllers."""
        if not self.is_connected:
            raise DeviceNotConnectedError("ErgoCubMotorsBus not connected")
        
        state = {}
        for board in self.state_boards:
            controller_state = self.controllers[board].read_current_state()
            state.update(controller_state)
        
        return state
    
    def send_commands(self, commands: dict[str, float]) -> None:
        """Send commands to controllers."""
        if not self.is_connected:
            raise DeviceNotConnectedError("ErgoCubMotorsBus not connected")
        
        for board in self.control_boards:
            self.controllers[board].send_commands(commands)

    def get_latest_joint_states(self) -> dict[str, float]:
        """Return the latest joint values exposed by subcontrollers."""
        joints: dict[str, float] = {}
        for controller in self.controllers.values():
            if hasattr(controller, "get_latest_joint_states"):
                joints.update(controller.get_latest_joint_states())
        return joints


    @property
    def state_features(self) -> dict[str, type]:
        """Get state features by aggregating from all controllers."""
        features = {}
        for name, controller in self.controllers.items():
            if name not in self.state_boards:
                continue 
            features.update(controller.motor_features)
        return features
    
    @property
    def action_features(self) -> dict[str, type]:
        """Get action features by aggregating from all controllers."""
        features = {}
        for name, controller in self.controllers.items():
            if name not in self.control_boards:
                continue 
            features.update(controller.motor_features)
        return features

    @property
    def motor_features(self) -> dict[str, type]:
        """Expose a unified feature map for robots whose action/state schema matches."""
        return self.state_features
    # ---------------------------------------------------------------------
    # Reset handling
    # ---------------------------------------------------------------------
    def reset(self) -> None:
        if "bimanual" in self.controllers:
            self.controllers["bimanual"].reset()
        if "head" in self.controllers:
            self.controllers["head"].reset()
        if "fingers" in self.controllers:
            self.controllers["fingers"].reset()
        time.sleep(5)  # Allow some time for reset to take effect
