"""@file processor_factory.py
@brief Build LeRobot processor pipelines from declarative YAML entries.

The server YAML lists processor steps as either a registry name or a dict that
either points to a registered processor or names a class by dotted Python
path. Keeping this construction logic out of `server.py` lets the server file
focus on the ROS2 boundary.
"""

from __future__ import annotations

import importlib
from typing import Any

from lerobot.processor import ProcessorStepRegistry, RobotProcessorPipeline
from lerobot.robots.custom_manipulator.processor import safety_processor as _safety_processor  # noqa: F401


def instantiate_processor_step(step_spec: Any):
    """@brief Build one configured robot/policy processor step.

    @param step_spec Either a registry name, or a mapping containing
        `registry_name`/`class` and an optional `config` dictionary.
    @return A configured processor step instance.
    """
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


def build_robot_processor_pipeline(
    processor_cfg: dict[str, Any],
    *,
    to_transition,
    to_output,
) -> RobotProcessorPipeline:
    """@brief Convert a YAML processor list into a LeRobot pipeline.

    @param processor_cfg Mapping with a `steps` list.
    @param to_transition Converter from robot-native objects to transition data.
    @param to_output Converter from transition data back to robot-native output.
    @return A `RobotProcessorPipeline` that wraps every configured step.
    """
    steps = [instantiate_processor_step(step_spec) for step_spec in processor_cfg.get("steps", [])]
    return RobotProcessorPipeline(
        steps=steps,
        to_transition=to_transition,
        to_output=to_output,
    )
