from __future__ import annotations

from types import SimpleNamespace

from sandwich_bt_python.executor import SkillCommandExecutor
from sandwich_bt_python.verification import VLM_SUCCESS


class _RecordingRobot:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def reset(self) -> None:
        self.events.append("robot_reset")

    def get_observation(self) -> dict[str, float]:
        self.events.append("get_observation")
        return {"position.x": 0.0}


class _RecordingProcessor:
    def __init__(self, name: str, events: list[str]) -> None:
        self.name = name
        self.events = events

    def reset(self) -> None:
        self.events.append(f"{self.name}_reset")

    def __call__(self, value):
        self.events.append(f"{self.name}_call")
        return value


class _RecordingSkillRuntime:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.cfg = SimpleNamespace(
            name="demo_skill",
            settle_time_s=0.0,
            transition=SimpleNamespace(mode="timeout", max_duration_s=1.0),
        )

    def reset(self) -> None:
        self.events.append("runtime_reset")


def test_skill_executor_resets_robot_after_lazy_runtime_load_and_before_rollout() -> None:
    events: list[str] = []
    cfg = SimpleNamespace(
        skills=[SimpleNamespace(name="demo_skill")],
        reset_robot_before_skill=True,
        fps=10,
    )
    executor = SkillCommandExecutor(cfg=cfg, robot=_RecordingRobot(events))
    runtime = _RecordingSkillRuntime(events)

    def get_skill_runtime(skill_name, robot_action_processor, robot_observation_processor):
        del skill_name, robot_action_processor, robot_observation_processor
        events.append("load_runtime")
        return runtime

    def skill_status(skill, obs_processed, elapsed_s, timeout_s):
        del skill, obs_processed, elapsed_s, timeout_s
        events.append("status")
        return "SUCCESS"

    executor._get_skill_runtime = get_skill_runtime
    executor._skill_status = skill_status

    result = executor.execute_skill(
        "demo_skill",
        robot_action_processor=_RecordingProcessor("action_processor", events),
        robot_observation_processor=_RecordingProcessor("observation_processor", events),
    )

    assert result.success
    assert events == [
        "load_runtime",
        "robot_reset",
        "runtime_reset",
        "action_processor_reset",
        "observation_processor_reset",
        "get_observation",
        "observation_processor_call",
        "status",
    ]


def test_active_vlm_success_stops_rollout_before_next_action() -> None:
    events: list[str] = []
    cfg = SimpleNamespace(
        skills=[SimpleNamespace(name="demo_skill")],
        reset_robot_before_skill=False,
        fps=1000,
    )
    executor = SkillCommandExecutor(cfg=cfg, robot=_RecordingRobot(events))
    runtime = _RecordingSkillRuntime(events)

    def get_skill_runtime(skill_name, robot_action_processor, robot_observation_processor):
        del skill_name, robot_action_processor, robot_observation_processor
        events.append("load_runtime")
        return runtime

    def skill_status(skill, obs_processed, elapsed_s, timeout_s):
        del skill, obs_processed, elapsed_s, timeout_s
        events.append("status")
        return "RUNNING"

    def run_skill_step(skill, obs, obs_processed, robot_action_processor, *, step_idx):
        del skill, obs, obs_processed, robot_action_processor, step_idx
        events.append("action")
        accepted = executor.report_active_vlm_result(
            skill_name="demo_skill",
            status=VLM_SUCCESS,
            message="scene ok",
        )
        events.append(f"active_vlm_accepted={accepted}")

    executor._get_skill_runtime = get_skill_runtime
    executor._skill_status = skill_status
    executor._run_skill_step = run_skill_step

    result = executor.execute_skill(
        "demo_skill",
        robot_action_processor=_RecordingProcessor("action_processor", events),
        robot_observation_processor=_RecordingProcessor("observation_processor", events),
    )

    assert result.success
    assert result.vlm_status == VLM_SUCCESS
    assert result.vlm_message == "scene ok"
    assert events.count("action") == 1
    assert "active_vlm_accepted=True" in events
