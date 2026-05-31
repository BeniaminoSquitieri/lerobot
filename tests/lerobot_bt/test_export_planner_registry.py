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
    # Check rules as dict
    rules = payload["rules"]
    assert isinstance(rules, dict)
    for rule in ["return_json_only", "no_xml", "registered_names_only", "do_not_change_step_kinds"]:
        assert rules[rule] is True

def test_export_fails_on_missing_registry_entry():
    class DummyRegistry:
        def kind_for_name(self, name):
            return None
    dummy = DummyRegistry()
    with pytest.raises(ValueError, match="not present in registry"):
        build_planner_registry_payload("make_sandwich", dummy)

def test_export_fails_on_kind_mismatch(monkeypatch):
    registry = load_registry("src/lerobot_bt_python/bt_generation/skills_registry.yaml")
    # Patch kind_for_name to return wrong kind for a known step
    orig = registry.kind_for_name
    def wrong_kind(name):
        if name == "pour_ingredient":
            return "robot_skill"
        return orig(name)
    monkeypatch.setattr(registry, "kind_for_name", wrong_kind)
    with pytest.raises(ValueError, match="kind mismatch"):
        build_planner_registry_payload("make_sandwich", registry)

def test_exported_payload_is_json_serializable():
    registry = load_registry("src/lerobot_bt_python/bt_generation/skills_registry.yaml")
    payload = build_planner_registry_payload("make_sandwich", registry)
    json.dumps(payload)

def test_objects_are_serialized_as_dicts():
    registry = load_registry("src/lerobot_bt_python/bt_generation/skills_registry.yaml")
    payload = build_planner_registry_payload("make_sandwich", registry)
    if "objects" in payload:
        for obj in payload["objects"]:
            assert isinstance(obj, dict)
            assert "canonical_name" in obj
            assert isinstance(obj["aliases"], list)
