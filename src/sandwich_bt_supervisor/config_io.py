"""YAML configuration loader for the supervisor runtime."""

"""YAML loader for the closed-set sandwich supervisor config."""

from __future__ import annotations

from pathlib import Path

import yaml

from .planner_schema import SupervisorConfig, SupervisorServiceConfig, TaskPrimitive


def load_supervisor_config(config_path: str | Path) -> SupervisorConfig:
    path = Path(config_path)
    try:
        with path.open() as config_file:
            raw_cfg = yaml.safe_load(config_file) or {}
    except FileNotFoundError as exc:
        raise ValueError(f"Supervisor config file was not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Supervisor config YAML is invalid: {path}") from exc

    if not isinstance(raw_cfg, dict):
        raise ValueError(f"Supervisor config must decode to a mapping: {path}")

    raw_service_cfg = raw_cfg.pop("service", {}) or {}
    raw_primitives = raw_cfg.pop("task_primitives", []) or []
    if not isinstance(raw_service_cfg, dict):
        raise ValueError(f"Supervisor config field 'service' must be a mapping: {path}")
    if not isinstance(raw_primitives, list):
        raise ValueError(f"Supervisor config field 'task_primitives' must be a list: {path}")

    try:
        return SupervisorConfig(
            service=SupervisorServiceConfig(**raw_service_cfg),
            task_primitives=[TaskPrimitive(**primitive_cfg) for primitive_cfg in raw_primitives],
            **raw_cfg,
        )
    except TypeError as exc:
        raise ValueError(f"Supervisor config fields are invalid in {path}: {exc}") from exc
