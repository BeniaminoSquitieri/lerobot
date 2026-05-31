import json
import types
import pytest
from pathlib import Path
from lerobot_bt_python.bt_generation import generate

def test_generate_ros_service_mode(monkeypatch, tmp_path):
    # Monkeypatch the ROS client to return a valid make_sandwich Linear IR JSON
    def fake_request_plan_from_ros_service(task_name, planner_registry_payload, **kwargs):
        # Minimal valid plan for make_sandwich
        return json.dumps({
            "task_name": "make_sandwich",
            "steps": [
                {"kind": "vlm_gate", "name": "initial_scene_ready"},
                {"kind": "robot_skill", "name": "place_first_toast"},
                {"kind": "human_step", "name": "pour_ingredient"},
                {"kind": "vlm_gate", "name": "ingredient_poured"},
                {"kind": "vlm_gate", "name": "second_toast_ready"},
                {"kind": "robot_skill", "name": "place_second_toast"},
                {"kind": "vlm_gate", "name": "make_sandwich.task_complete"},
            ]
        })
    monkeypatch.setattr(
        "lerobot_bt_python.bt_generation.ros_plan_client.request_plan_from_ros_service",
        fake_request_plan_from_ros_service,
    )
    output_dir = tmp_path / "generated_bt"
    args = [
        "--task", "make_sandwich",
        "--planner", "ros-service",
        "--registry", "src/lerobot_bt_python/bt_generation/skills_registry.yaml",
        "--executor-yaml", "src/lerobot_bt_python/make_sandwich_executor.yaml",
        "--output-dir", str(output_dir),
    ]
    rc = generate.main(args)
    assert rc == 0
    assert (output_dir / "plans/make_sandwich_linear_ir.json").exists()
    assert (output_dir / "trees/make_sandwich.xml").exists()
    assert (output_dir / "config/make_sandwich_bt.yaml").exists()
    assert (output_dir / "raw_model_responses/make_sandwich_raw_response.json").exists()

def test_generate_ros_service_invalid_xml(monkeypatch, tmp_path):
    # Monkeypatch the ROS client to return invalid XML (not JSON)
    def fake_request_plan_from_ros_service(*a, **k):
        return "<xml>not json</xml>"
    monkeypatch.setattr(
        "lerobot_bt_python.bt_generation.ros_plan_client.request_plan_from_ros_service",
        fake_request_plan_from_ros_service,
    )
    output_dir = tmp_path / "generated_bt"
    args = [
        "--task", "make_sandwich",
        "--planner", "ros-service",
        "--registry", "src/lerobot_bt_python/bt_generation/skills_registry.yaml",
        "--executor-yaml", "src/lerobot_bt_python/make_sandwich_executor.yaml",
        "--output-dir", str(output_dir),
    ]
    rc = generate.main(args)
    assert rc != 0
    assert (output_dir / "raw_model_responses/make_sandwich_raw_response.txt").exists()

def test_generate_ros_service_invented_skill(monkeypatch, tmp_path):
    # Monkeypatch the ROS client to return a plan with an invented skill
    def fake_request_plan_from_ros_service(*a, **k):
        return json.dumps({
            "task_name": "make_sandwich",
            "steps": [
                {"kind": "robot_skill", "name": "invented_skill"},
            ]
        })
    monkeypatch.setattr(
        "lerobot_bt_python.bt_generation.ros_plan_client.request_plan_from_ros_service",
        fake_request_plan_from_ros_service,
    )
    output_dir = tmp_path / "generated_bt"
    args = [
        "--task", "make_sandwich",
        "--planner", "ros-service",
        "--registry", "src/lerobot_bt_python/bt_generation/skills_registry.yaml",
        "--executor-yaml", "src/lerobot_bt_python/make_sandwich_executor.yaml",
        "--output-dir", str(output_dir),
    ]
    rc = generate.main(args)
    assert rc != 0
    assert (output_dir / "raw_model_responses/make_sandwich_raw_response.json").exists()
