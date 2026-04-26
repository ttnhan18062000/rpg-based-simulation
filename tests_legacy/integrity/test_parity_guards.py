import pytest
import json
import os

ORACLE_ROOT = "tests/parity"
REQUIRED_ORACLES = {
    "movement_oracle": "results.json",
    "interaction_oracle": "results.json",
    "town_oracle": "results.json"
}

def test_oracle_artifact_existence():
    """
    STRICT LAW: Every oracle directory required for parity must contain a results.json.
    Missing artifacts break the parity truth surface.
    """
    for oracle_dir, filename in REQUIRED_ORACLES.items():
        path = os.path.join(ORACLE_ROOT, oracle_dir, filename)
        assert os.path.exists(path), f"ORACLE DRIFT: Required oracle artifact missing: {path}"

def test_oracle_schema_integrity():
    """
    LAW: Oracle results.json must be valid JSON and follow the expected list-of-scenarios structure.
    """
    for oracle_dir, filename in REQUIRED_ORACLES.items():
        path = os.path.join(ORACLE_ROOT, oracle_dir, filename)
        if not os.path.exists(path):
            continue
            
        with open(path, "r") as f:
            try:
                data = json.load(f)
                assert isinstance(data, list), f"SCHEMA DRIFT: Oracle {path} must be a JSON list of scenarios"
                for i, entry in enumerate(data):
                    assert "scenario" in entry, f"SCHEMA DRIFT: Oracle {path} entry {i} missing 'scenario' key"
            except json.JSONDecodeError:
                pytest.fail(f"SCHEMA DRIFT: Oracle {path} is not valid JSON")

def test_critical_parity_scenarios_presence():
    """
    LAW: High-priority Phase 5 scenarios must be present in the oracles.
    """
    # 1. Town Oracle must cover blacksmith success and material failure
    town_path = os.path.join(ORACLE_ROOT, "town_oracle", "results.json")
    if os.path.exists(town_path):
        with open(town_path, "r") as f:
            town_data = json.load(f)
            scenarios = {entry["scenario"] for entry in town_data}
            required = {"blacksmith_craft_success", "blacksmith_missing_materials", "shop_sell_materials"}
            missing = required - scenarios
            assert not missing, f"PARITY GAP: Town oracle missing critical Phase 5 scenarios: {missing}"

    # 2. Movement Oracle must cover basic success
    move_path = os.path.join(ORACLE_ROOT, "movement_oracle", "results.json")
    if os.path.exists(move_path):
        with open(move_path, "r") as f:
            move_data = json.load(f)
            scenarios = {entry["scenario"] for entry in move_data}
            assert "success_move" in scenarios, "PARITY GAP: Movement oracle missing 'success_move' scenario"

    # 3. Interaction Oracle must cover harvest success
    interact_path = os.path.join(ORACLE_ROOT, "interaction_oracle", "results.json")
    if os.path.exists(interact_path):
        with open(interact_path, "r") as f:
            interact_data = json.load(f)
            scenarios = {entry["scenario"] for entry in interact_data}
            assert "harvest_done" in scenarios, "PARITY GAP: Interaction oracle missing 'harvest_done' scenario"
