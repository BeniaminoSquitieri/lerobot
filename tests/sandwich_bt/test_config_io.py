from __future__ import annotations

from pathlib import Path

from sandwich_bt_supervisor.config_io import load_supervisor_config


def test_load_supervisor_config_parses_reference_yaml() -> None:
    cfg = load_supervisor_config(
        Path("src/sandwich_bt_supervisor/sandwich_bt_supervisor.yaml")
    )

    assert cfg.goal == "make_sandwich"
    assert cfg.service.plan_service_name == "/sandwich_supervisor/next_action"
    assert [primitive.name for primitive in cfg.task_primitives] == [
        "place_first_toast",
        "pour_ingredient",
        "place_second_toast",
    ]


def test_load_supervisor_config_rejects_missing_file() -> None:
    try:
        load_supervisor_config(Path("/tmp/does_not_exist_supervisor.yaml"))
    except ValueError as exc:
        assert "was not found" in str(exc)
    else:  # pragma: no cover - explicit guard for readability
        raise AssertionError("Expected load_supervisor_config to reject a missing file.")
