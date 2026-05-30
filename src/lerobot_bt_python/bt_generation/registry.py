"""Typed access and validation for deterministic BT generation registries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROBOT_SKILL = "robot_skill"
HUMAN_STEP = "human_step"
VLM_GATE = "vlm_gate"
INFINITE_RETRY_ATTEMPTS = -1

ALLOWED_KINDS = {ROBOT_SKILL, HUMAN_STEP, VLM_GATE}
EXPECTED_EXECUTORS = {
    ROBOT_SKILL: "robot",
    HUMAN_STEP: "human",
    VLM_GATE: "vlm",
}


def is_valid_max_attempts(value: int) -> bool:
    """Return whether BehaviorTree.CPP accepts this retry budget."""

    return value == INFINITE_RETRY_ATTEMPTS or value >= 1


@dataclass(frozen=True)
class RegistryEntry:
    """One explicit registry item used by the deterministic planner."""

    name: str
    kind: str
    executor: str
    timeout_s: float
    max_attempts: int
    verify_after: str | None = None
    instruction: str = ""
    task: str = ""
    verify_after_declared: bool = True


@dataclass(frozen=True)
class Registry:
    """Validated registry grouped by generation kind."""

    version: int
    robot_skills: dict[str, RegistryEntry]
    human_steps: dict[str, RegistryEntry]
    vlm_gates: dict[str, RegistryEntry]

    def items_for_kind(self, kind: str) -> dict[str, RegistryEntry]:
        if kind == ROBOT_SKILL:
            return self.robot_skills
        if kind == HUMAN_STEP:
            return self.human_steps
        if kind == VLM_GATE:
            return self.vlm_gates
        raise KeyError(f"Unsupported registry kind: {kind}")

    def get(self, kind: str, name: str) -> RegistryEntry:
        return self.items_for_kind(kind)[name]

    def kind_for_name(self, name: str) -> str | None:
        found = [
            kind
            for kind in ALLOWED_KINDS
            if name in self.items_for_kind(kind)
        ]
        if not found:
            return None
        if len(found) > 1:
            return "ambiguous"
        return found[0]

    @property
    def all_entries(self) -> list[RegistryEntry]:
        return [
            *self.robot_skills.values(),
            *self.human_steps.values(),
            *self.vlm_gates.values(),
        ]


def load_registry(path: Path | str) -> Registry:
    """Load a registry YAML file without silently inventing entries."""

    registry_path = Path(path)
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{registry_path} must contain a YAML mapping.")
    return registry_from_dict(data)


def registry_from_dict(data: dict[str, Any]) -> Registry:
    """Build a Registry object from parsed YAML data."""

    return Registry(
        version=int(data.get("version", 0)),
        robot_skills=_entries_from_section(data.get("robot_skills", []), ROBOT_SKILL),
        human_steps=_entries_from_section(data.get("human_steps", []), HUMAN_STEP),
        vlm_gates=_entries_from_section(data.get("vlm_gates", []), VLM_GATE),
    )


def validate_registry(registry: Registry) -> list[str]:
    """Return every registry error found; an empty list means valid."""

    errors: list[str] = []
    if registry.version != 1:
        errors.append(f"registry.version must be 1, got {registry.version!r}.")

    names: dict[str, list[str]] = {}
    for entry in registry.all_entries:
        names.setdefault(entry.name, []).append(entry.kind)
    for name, kinds in sorted(names.items()):
        if len(kinds) > 1:
            errors.append(f"Registry name {name!r} appears in multiple sections: {sorted(kinds)}.")

    for entry in registry.all_entries:
        errors.extend(_validate_common_entry(entry))

    for entry in registry.robot_skills.values():
        if not entry.verify_after_declared:
            errors.append(f"robot_skill {entry.name!r} must declare verify_after, even when null.")
        if entry.verify_after is not None and entry.verify_after not in registry.vlm_gates:
            errors.append(
                f"robot_skill {entry.name!r} verify_after points to unknown vlm_gate "
                f"{entry.verify_after!r}."
            )

    for entry in registry.human_steps.values():
        if not entry.instruction.strip():
            errors.append(f"human_step {entry.name!r} must have a non-empty instruction.")
        if not entry.verify_after_declared:
            errors.append(f"human_step {entry.name!r} must declare verify_after, even when null.")
        if entry.verify_after is not None and entry.verify_after not in registry.vlm_gates:
            errors.append(
                f"human_step {entry.name!r} verify_after points to unknown vlm_gate "
                f"{entry.verify_after!r}."
            )

    for entry in registry.vlm_gates.values():
        if not entry.task.strip():
            errors.append(f"vlm_gate {entry.name!r} must have a non-empty task.")

    return errors


def _entries_from_section(raw_entries: Any, expected_kind: str) -> dict[str, RegistryEntry]:
    if raw_entries is None:
        raw_entries = []
    if not isinstance(raw_entries, list):
        raise ValueError(f"{expected_kind} section must be a list.")

    entries: dict[str, RegistryEntry] = {}
    for raw in raw_entries:
        if not isinstance(raw, dict):
            raise ValueError(f"{expected_kind} entry must be a mapping.")

        name = str(raw.get("name", ""))
        entry = RegistryEntry(
            name=name,
            kind=str(raw.get("kind", "")),
            executor=str(raw.get("executor", "")),
            timeout_s=float(raw.get("timeout_s", 0.0)),
            max_attempts=int(raw.get("max_attempts", 0)),
            verify_after=raw.get("verify_after"),
            instruction=str(raw.get("instruction", "")),
            task=str(raw.get("task", "")),
            verify_after_declared="verify_after" in raw,
        )
        if name in entries:
            raise ValueError(f"Duplicate {expected_kind} registry entry {name!r}.")
        entries[name] = entry

    return entries


def _validate_common_entry(entry: RegistryEntry) -> list[str]:
    errors: list[str] = []
    if not entry.name:
        errors.append(f"{entry.kind} entry has an empty name.")
    if entry.kind not in ALLOWED_KINDS:
        errors.append(f"Registry entry {entry.name!r} has unsupported kind {entry.kind!r}.")
    if entry.kind in EXPECTED_EXECUTORS and entry.executor != EXPECTED_EXECUTORS[entry.kind]:
        errors.append(
            f"{entry.kind} {entry.name!r} must use executor "
            f"{EXPECTED_EXECUTORS[entry.kind]!r}, got {entry.executor!r}."
        )
    if entry.timeout_s <= 0.0:
        errors.append(f"{entry.kind} {entry.name!r} timeout_s must be > 0.")
    if not is_valid_max_attempts(entry.max_attempts):
        errors.append(
            f"{entry.kind} {entry.name!r} max_attempts must be "
            f"{INFINITE_RETRY_ATTEMPTS} for infinite retries or a positive integer."
        )
    return errors
