import json
from pathlib import Path
from lerobot_bt_python.bt_generation.export_planner_registry import build_planner_registry_payload
from lerobot_bt_python.bt_generation.registry import load_registry

def test_make_sandwich_registry_payload(tmp_path):
    registry = load_registry("src/lerobot_bt_python/bt_generation/skills_registry.yaml")
    payload = build_planner_registry_payload("make_sandwich", registry)
    # Check required steps
    robot_skill_names = {s["name"] for s in payload["robot_skills"]}
    human_step_names = {s["name"] for s in payload["human_steps"]}
    vlm_gate_names = {s["name"] for s in payload["vlm_gates"]}
    assert "place_first_toast" in robot_skill_names
    assert "place_second_toast" in robot_skill_names
    assert "pour_ingredient" in human_step_names
    assert "ingredient_poured" in vlm_gate_names
    assert "second_toast_ready" in vlm_gate_names
    assert "make_sandwich.task_complete" in vlm_gate_names
    # Check rules
    for rule in ["return_json_only", "no_xml", "registered_names_only", "do_not_change_step_kinds"]:
        assert rule in payload["rules"]
