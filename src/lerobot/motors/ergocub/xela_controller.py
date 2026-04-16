#!/usr/bin/env python

# Copyright 2026 The HuggingFace Inc. team. All rights reserved.
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

from __future__ import annotations

import logging
import os
import time
from collections.abc import Iterable
from typing import Any

import numpy as np
try:
    import yarp
except ImportError:
    yarp = None

from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

logger = logging.getLogger(__name__)

XELA_FINGERS = ("thumb", "index", "middle", "ring", "pinky")
XELA_AXES = ("x", "y", "z")
XELA_NUM_TAXELS = 7
XELA_NEUTRAL_VALUE = float(os.getenv("LEROBOT_ERGOCUB_XELA_NEUTRAL_VALUE", "32768"))
XELA_NEUTRAL_VECTOR = np.array([XELA_NEUTRAL_VALUE, XELA_NEUTRAL_VALUE, XELA_NEUTRAL_VALUE], dtype=float)
XELA_OFFSET_SAMPLE_COUNT = int(os.getenv("LEROBOT_ERGOCUB_XELA_OFFSET_SAMPLE_COUNT", "10"))


def _tokenize_yarp_text(text: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch in "()":
            tokens.append(ch)
            i += 1
            continue
        if ch == "[":
            end = text.find("]", i)
            if end == -1:
                raise ValueError(f"Unclosed bracket token in Xela payload: {text[i:]}")
            tokens.append(text[i : end + 1])
            i = end + 1
            continue

        end = i
        while end < len(text) and not text[end].isspace() and text[end] not in "()[]":
            end += 1
        tokens.append(text[i:end])
        i = end
    return tokens


def _parse_yarp_text_value(token: str) -> Any:
    if token.startswith("[") and token.endswith("]"):
        return token[1:-1]
    try:
        if any(ch in token for ch in ".eE"):
            return float(token)
        return int(token)
    except ValueError:
        return token


def _parse_yarp_text_tokens(tokens: list[str], start_idx: int = 0) -> tuple[list[Any], int]:
    values: list[Any] = []
    idx = start_idx
    while idx < len(tokens):
        token = tokens[idx]
        if token == ")":
            return values, idx + 1
        if token == "(":
            nested, idx = _parse_yarp_text_tokens(tokens, idx + 1)
            values.append(nested)
            continue
        values.append(_parse_yarp_text_value(token))
        idx += 1
    return values, idx


def parse_xela_payload(payload: Any) -> list[Any]:
    """Convert a YARP bottle payload into plain Python values."""

    if isinstance(payload, str):
        values, _ = _parse_yarp_text_tokens(_tokenize_yarp_text(payload))
        return values

    if hasattr(payload, "size") and hasattr(payload, "get"):
        return [parse_xela_payload(payload.get(i)) for i in range(payload.size())]

    if hasattr(payload, "isList") and payload.isList():
        return parse_xela_payload(payload.asList())

    for check_name, convert_name in (
        ("isFloat64", "asFloat64"),
        ("isFloat32", "asFloat32"),
        ("isInt64", "asInt64"),
        ("isInt32", "asInt32"),
        ("isInt16", "asInt16"),
        ("isInt8", "asInt8"),
        ("isBool", "asBool"),
    ):
        if hasattr(payload, check_name) and getattr(payload, check_name)():
            return getattr(payload, convert_name)()

    if hasattr(payload, "isString") and payload.isString():
        return payload.asString()

    if hasattr(payload, "asString"):
        return payload.asString()

    return payload


def _normalize_status(status_value: Any) -> str:
    if isinstance(status_value, str):
        return status_value.strip("[]").lower()
    if isinstance(status_value, Iterable) and not isinstance(status_value, (str, bytes)):
        return " ".join(_normalize_status(item) for item in status_value).strip()
    return str(status_value).strip("[]").lower()


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def extract_xela_state(
    payload: Any,
    side: str,
    baselines: dict[tuple[str, int], np.ndarray] | None = None,
    finger_offsets: dict[str, np.ndarray] | None = None,
    offset_samples: dict[str, list[np.ndarray]] | None = None,
    offset_sample_count: int = XELA_OFFSET_SAMPLE_COUNT,
) -> dict[str, float]:
    """Extract Xela states, calibrating each finger with a fixed rest offset estimated from the first samples."""

    parsed_payload = parse_xela_payload(payload)
    if len(parsed_payload) < 2:
        raise ValueError(f"Unexpected Xela payload structure for {side}: {parsed_payload!r}")

    finger_entries = next((item for item in parsed_payload[1:] if isinstance(item, list)), [])
    if not isinstance(finger_entries, list):
        raise ValueError(f"Missing finger entries in Xela payload for {side}: {parsed_payload!r}")

    if baselines is None:
        baselines = {}
    if finger_offsets is None:
        finger_offsets = {}
    if offset_samples is None:
        offset_samples = {}

    state: dict[str, float] = {f"{side}_xela.timestamp": _as_float(parsed_payload[0])}
    hand_force = np.zeros(3, dtype=float)
    hand_raw_force = np.zeros(3, dtype=float)
    hand_delta = np.zeros(3, dtype=float)

    for finger_idx, finger_name in enumerate(XELA_FINGERS):
        finger_force = np.zeros(3, dtype=float)
        finger_raw_force = np.zeros(3, dtype=float)
        finger_delta = np.zeros(3, dtype=float)
        valid_taxel_count = 0
        taxel_entries: list[Any] = []

        if finger_idx < len(finger_entries) and isinstance(finger_entries[finger_idx], list):
            taxel_entries = next(
                (item for item in finger_entries[finger_idx] if isinstance(item, list)),
                [],
            )

        for taxel_idx in range(XELA_NUM_TAXELS):
            raw = np.zeros(3, dtype=float)
            force = np.zeros(3, dtype=float)
            delta = np.zeros(3, dtype=float)
            valid = 0.0

            if taxel_idx < len(taxel_entries) and isinstance(taxel_entries[taxel_idx], list):
                taxel_entry = taxel_entries[taxel_idx]
                raw_xyz = np.array(
                    [
                        _as_float(taxel_entry[1]),
                        _as_float(taxel_entry[2]),
                        _as_float(taxel_entry[3]),
                    ],
                    dtype=float,
                )
                raw = raw_xyz.copy()
                status = _normalize_status(taxel_entry[-1]) if taxel_entry else "fail"
                if "ok" in status:
                    force = raw_xyz - XELA_NEUTRAL_VECTOR
                    baseline_key = (finger_name, taxel_idx)
                    baseline = baselines.setdefault(baseline_key, raw_xyz.copy())
                    delta = raw_xyz - baseline
                    valid = 1.0
                    finger_raw_force += force
                    finger_delta += delta
                    valid_taxel_count += 1

            taxel_prefix = f"{side}_xela.{finger_name}.taxel_{taxel_idx}"
            for axis, value in zip(XELA_AXES, raw):
                state[f"{taxel_prefix}.raw.{axis}"] = float(value)
                state[f"{taxel_prefix}.{axis}"] = float(value)
            for axis, value in zip(XELA_AXES, force):
                state[f"{taxel_prefix}.force.{axis}"] = float(value)
            for axis, value in zip(XELA_AXES, delta):
                state[f"{taxel_prefix}.delta.{axis}"] = float(value)
            state[f"{taxel_prefix}.valid"] = valid

        if valid_taxel_count > 0:
            finger_raw_force = finger_raw_force / valid_taxel_count
            finger_delta = finger_delta / valid_taxel_count

            if finger_name not in finger_offsets and offset_sample_count > 0:
                samples = offset_samples.setdefault(finger_name, [])
                if len(samples) < offset_sample_count:
                    samples.append(finger_raw_force.copy())
                if len(samples) == offset_sample_count:
                    finger_offsets[finger_name] = np.mean(np.stack(samples, axis=0), axis=0)

        finger_offset = finger_offsets.get(finger_name, np.zeros(3, dtype=float))
        if valid_taxel_count > 0 and finger_name in finger_offsets:
            finger_force = finger_raw_force - finger_offset
        else:
            # Hide uncalibrated readings until we have collected the requested rest samples.
            finger_force = np.zeros(3, dtype=float)

        for axis, value in zip(XELA_AXES, finger_force):
            state[f"{side}_xela.{finger_name}.force.{axis}"] = float(value)
        for axis, value in zip(XELA_AXES, finger_raw_force):
            state[f"{side}_xela.{finger_name}.raw_force.{axis}"] = float(value)
        for axis, value in zip(XELA_AXES, finger_offset):
            state[f"{side}_xela.{finger_name}.offset.{axis}"] = float(value)
        for axis, value in zip(XELA_AXES, finger_delta):
            state[f"{side}_xela.{finger_name}.delta.{axis}"] = float(value)
        state[f"{side}_xela.{finger_name}.valid_taxels"] = float(valid_taxel_count)
        state[f"{side}_xela.{finger_name}.offset_samples"] = float(len(offset_samples.get(finger_name, [])))
        state[f"{side}_xela.{finger_name}.offset_ready"] = float(finger_name in finger_offsets)
        hand_force += finger_force
        hand_raw_force += finger_raw_force
        hand_delta += finger_delta

    for axis, value in zip(XELA_AXES, hand_force):
        state[f"{side}_xela.force.{axis}"] = float(value)
    for axis, value in zip(XELA_AXES, hand_raw_force):
        state[f"{side}_xela.raw_force.{axis}"] = float(value)
    for axis, value in zip(XELA_AXES, hand_delta):
        state[f"{side}_xela.delta.{axis}"] = float(value)

    return state


class ErgoCubXelaController:
    """Read fake Xela tactile data from a YARP bottle port and expose it as state features."""

    def __init__(self, local_prefix: str, side: str, remote_port: str | None = None):
        if side not in {"left", "right"}:
            raise ValueError(f"Unsupported Xela side: {side!r}")
        if yarp is None:
            raise ModuleNotFoundError("yarp")

        self.side = side
        self.local_prefix = local_prefix
        self.remote_port = remote_port or f"/{side}Xela:o"
        self.xela_port = yarp.BufferedPortBottle()
        self._is_connected = False
        self._baselines: dict[tuple[str, int], np.ndarray] = {}
        self._finger_offsets: dict[str, np.ndarray] = {}
        self._offset_samples: dict[str, list[np.ndarray]] = {}
        self._latest_state: dict[str, float] = {}

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def connect(self) -> None:
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"ErgoCubXelaController({self.side}) already connected")

        local_port = f"{self.local_prefix}/{self.side}_xela:i"
        if not self.xela_port.open(local_port):
            raise ConnectionError(f"Failed to open Xela port {local_port}")

        while not yarp.Network.connect(self.remote_port, local_port):
            logger.warning("Failed to connect %s -> %s, retrying...", self.remote_port, local_port)
            time.sleep(1)

        self._baselines.clear()
        self._finger_offsets.clear()
        self._offset_samples.clear()
        self._is_connected = True
        logger.info("ErgoCubXelaController(%s) connected", self.side)

    def disconnect(self) -> None:
        if not self.is_connected:
            raise DeviceNotConnectedError(f"ErgoCubXelaController({self.side}) not connected")

        self.xela_port.close()
        self._is_connected = False
        logger.info("ErgoCubXelaController(%s) disconnected", self.side)

    def read_current_state(self) -> dict[str, float]:
        if not self.is_connected:
            raise DeviceNotConnectedError(f"ErgoCubXelaController({self.side}) not connected")

        read_attempts = 0
        while (bottle := self.xela_port.read(False)) is None:
            read_attempts += 1
            if read_attempts % 1000 == 0:
                logger.warning("Still waiting for %s Xela data (attempt %d)", self.side, read_attempts)
            time.sleep(0.001)

        previous_ready = set(self._finger_offsets)
        self._latest_state = extract_xela_state(
            bottle,
            side=self.side,
            baselines=self._baselines,
            finger_offsets=self._finger_offsets,
            offset_samples=self._offset_samples,
        )
        for finger_name in sorted(set(self._finger_offsets) - previous_ready):
            logger.info(
                "Xela %s %s offset calibrated from %d rest samples: %s",
                self.side,
                finger_name,
                XELA_OFFSET_SAMPLE_COUNT,
                np.array2string(self._finger_offsets[finger_name], precision=2),
            )
        return dict(self._latest_state)

    @property
    def motor_features(self) -> dict[str, type]:
        prefix = f"{self.side}_xela"
        features: dict[str, type] = {}
        for finger_name in XELA_FINGERS:
            for taxel_idx in range(XELA_NUM_TAXELS):
                for axis in XELA_AXES:
                    features[f"{prefix}.{finger_name}.taxel_{taxel_idx}.{axis}"] = float

        return features
