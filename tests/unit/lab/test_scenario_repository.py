# Compliance IDs: SCENARIO-TEST-007, SCENARIO-TEST-008, SCENARIO-TEST-009
import pytest
import json
from pathlib import Path
from src.lab.schema import ScenarioSpec
from src.lab.repository import ScenarioRepository

@pytest.fixture
def sample_spec_dict():
    return {
        "schema_version": "scenariospec.v1",
        "scenario_id": "test_scenario_abc",
        "name": "Sample Test Scenario",
        "world_id": "resource_valley_basic",
        "scenario_type": "resource_economy",
        "intent": {
            "primary_goal": "validate_economy",
            "description": "Standard economy check"
        },
        "expected_behavior": {
            "resource_production_rate": {"min": 1.0}
        },
        "required_signals": {
            "metrics": ["resource_production_rate"],
            "events": ["ResourceNodeDepleted"],
            "cognition": ["current_project"]
        },
        "allowed_anomalies": ["NavigationStuckBasic"],
        "critical_anomalies": ["HardLawViolationDetected"],
        "tags": ["economy", "workers"]
    }

def test_repository_save_and_load(tmp_path: Path, sample_spec_dict):
    """Verify that saving a scenario stores a valid yaml, and loading retrieves it."""
    repo = ScenarioRepository(tmp_path)
    spec = ScenarioSpec(**sample_spec_dict)
    
    # Save the scenario spec
    repo.save_scenario(spec)
    
    # Assert YAML file was created at target subfolder
    expected_yaml = tmp_path / "test_scenario_abc" / "scenario.yaml"
    assert expected_yaml.is_file()
    
    # Load back and verify equality
    loaded_spec = repo.load_scenario("test_scenario_abc")
    assert loaded_spec.scenario_id == spec.scenario_id
    assert loaded_spec.name == spec.name
    assert loaded_spec.intent.primary_goal == spec.intent.primary_goal
    assert loaded_spec.expected_behavior["resource_production_rate"].min == 1.0
    
    # List scenarios should return it
    assert repo.list_scenarios() == ["test_scenario_abc"]

def test_repository_index_rebuild(tmp_path: Path, sample_spec_dict):
    """Verify that the repository manifest index is rebuilt and accurate."""
    repo = ScenarioRepository(tmp_path)
    spec1 = ScenarioSpec(**sample_spec_dict)
    
    # Save 1st scenario
    repo.save_scenario(spec1)
    
    # Save 2nd scenario
    sample_spec_dict["scenario_id"] = "another_scenario"
    sample_spec_dict["name"] = "Another Scenario"
    sample_spec_dict["tags"] = ["combat"]
    spec2 = ScenarioSpec(**sample_spec_dict)
    repo.save_scenario(spec2)
    
    # Verify both exist in list
    assert repo.list_scenarios() == ["another_scenario", "test_scenario_abc"]
    
    # Index path should exist and contain both entries
    index_path = tmp_path / "scenario_index.json"
    assert index_path.is_file()
    
    index_data = repo.get_index()
    assert len(index_data) == 2
    assert index_data["test_scenario_abc"]["status"] == "VALIDATED"
    assert "economy" in index_data["test_scenario_abc"]["tags"]
    
    assert index_data["another_scenario"]["name"] == "Another Scenario"
    assert index_data["another_scenario"]["status"] == "VALIDATED"
    assert "combat" in index_data["another_scenario"]["tags"]

def test_repository_handles_broken_scenarios(tmp_path: Path, sample_spec_dict):
    """Verify that broken/malformed scenario files are handled gracefully by indexer."""
    repo = ScenarioRepository(tmp_path)
    
    # Write a broken YAML manually under target folder
    broken_dir = tmp_path / "broken_scenario"
    broken_dir.mkdir(parents=True, exist_ok=True)
    (broken_dir / "scenario.yaml").write_text("invalid yaml text [hello: world")
    
    # List scenarios should still find the folder containing scenario.yaml
    assert repo.list_scenarios() == ["broken_scenario"]
    
    # Rebuild index should handle broken file cleanly
    repo.rebuild_index()
    index_data = repo.get_index()
    assert index_data["broken_scenario"]["status"] == "BROKEN"
    assert index_data["broken_scenario"]["name"] == "Unknown (Broken)"

def test_repository_path_traversal_guards(tmp_path: Path, sample_spec_dict):
    """Verify that path traversal attempts are blocked via security boundaries."""
    repo = ScenarioRepository(tmp_path)
    
    # 1. Unsafe pattern in ID should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        repo.load_scenario("../unsafe_id")
    assert "Invalid or unsafe scenario_id pattern" in str(exc_info.value)
    
    # 2. Bypassing check if someone constructs a spec with unsafe ID and tries to save it
    # We validate scenario_id regex in _resolve_scenario_path, so even saving will check it
    sample_spec_dict["scenario_id"] = "unsafe/path"
    with pytest.raises(ValueError):
        repo.save_scenario(ScenarioSpec(**sample_spec_dict))
