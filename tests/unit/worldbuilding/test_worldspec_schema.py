# Compliance IDs: WORLD-050, WORLD-051, WORLD-052
import pytest
import yaml
from pathlib import Path
from pydantic import ValidationError
from src.worldbuilding.schema import (
    load_world_spec_from_yaml,
    InvalidWorldSpecError,
    WorldSpec
)

# Helper function to write a temporary yaml specification
def write_temp_spec(tmp_path: Path, data: dict) -> Path:
    spec_path = tmp_path / "world_spec.yaml"
    with open(spec_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)
    return spec_path

def test_valid_minimal_world_spec_loads(tmp_path):
    # Setup standard valid minimal configuration
    data = {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley",
        "name": "Test Valley",
        "description": "A tranquil testing valley.",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        }
    }
    
    spec_path = write_temp_spec(tmp_path, data)
    spec = load_world_spec_from_yaml(spec_path)
    
    assert isinstance(spec, WorldSpec)
    assert spec.schema_version == "worldspec.v1"
    assert spec.world_id == "test_valley"
    assert spec.topology.width == 100
    assert spec.topology.height == 100
    assert spec.topology.coordinate_system == "grid"
    # Defaults should load correctly
    assert spec.regions == []
    assert spec.factions == []
    assert spec.entities == []
    assert spec.resources == []
    assert spec.buildings == []
    assert spec.quest_definitions == []
    assert spec.validation.expected_min_entities == 1
    assert spec.validation.allow_overlapping_regions is False

def test_missing_schema_version_rejected(tmp_path):
    data = {
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        }
    }
    spec_path = write_temp_spec(tmp_path, data)
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        load_world_spec_from_yaml(spec_path)
    assert "schema_version" in str(exc_info.value)

def test_invalid_schema_version_rejected(tmp_path):
    data = {
        "schema_version": "worldspec.v2",  # Invalid version
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        }
    }
    spec_path = write_temp_spec(tmp_path, data)
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        load_world_spec_from_yaml(spec_path)
    assert "schema_version" in str(exc_info.value)

def test_missing_world_id_rejected(tmp_path):
    data = {
        "schema_version": "worldspec.v1",
        "name": "Test Valley",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        }
    }
    spec_path = write_temp_spec(tmp_path, data)
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        load_world_spec_from_yaml(spec_path)
    assert "world_id" in str(exc_info.value)

def test_invalid_topology_dimensions_rejected(tmp_path):
    # Test width == 0
    data = {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {
            "width": 0,
            "height": 100,
            "coordinate_system": "grid"
        }
    }
    spec_path = write_temp_spec(tmp_path, data)
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        load_world_spec_from_yaml(spec_path)
    assert "width" in str(exc_info.value)

    # Test negative height
    data["topology"]["width"] = 100
    data["topology"]["height"] = -5
    spec_path = write_temp_spec(tmp_path, data)
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        load_world_spec_from_yaml(spec_path)
    assert "height" in str(exc_info.value)

def test_invalid_coordinate_system_rejected(tmp_path):
    data = {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "hexagonal"  # Invalid coordinate system
        }
    }
    spec_path = write_temp_spec(tmp_path, data)
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        load_world_spec_from_yaml(spec_path)
    assert "coordinate_system" in str(exc_info.value)

def test_region_bounds_validation(tmp_path):
    # Invalid region bounds: min_x > max_x
    data = {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        },
        "regions": [
            {
                "id": "invalid_region",
                "type": "forest",
                "bounds": [50, 10, 20, 30]  # min_x (50) > max_x (20)
            }
        ]
    }
    spec_path = write_temp_spec(tmp_path, data)
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        load_world_spec_from_yaml(spec_path)
    assert "bounds min_x" in str(exc_info.value)

def test_duplicate_identifiers_rejected(tmp_path):
    data = {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        },
        "regions": [
            {"id": "forest_zone", "type": "forest", "bounds": [0, 0, 10, 10]},
            {"id": "forest_zone", "type": "swamp", "bounds": [20, 20, 30, 30]} # Duplicate region ID
        ]
    }
    spec_path = write_temp_spec(tmp_path, data)
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        load_world_spec_from_yaml(spec_path)
    assert "Duplicate region ID" in str(exc_info.value)

def test_nonexistent_file_raises_custom_error():
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        load_world_spec_from_yaml("nonexistent_world_spec.yaml")
    assert "file not found" in str(exc_info.value).lower()

def test_empty_yaml_raises_custom_error(tmp_path):
    spec_path = tmp_path / "empty.yaml"
    spec_path.touch()
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        load_world_spec_from_yaml(spec_path)
    assert "empty" in str(exc_info.value).lower()

def test_schema_no_side_effects(tmp_path):
    # Verify that parsing the schema creates a read-only WorldSpec and touches no engine states
    data = {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        }
    }
    spec_path = write_temp_spec(tmp_path, data)
    spec = load_world_spec_from_yaml(spec_path)
    
    # Assert returning model properties
    assert spec.world_id == "test_valley"
    
    # Verify Pydantic frozen model config prevents mutating fields
    with pytest.raises(ValidationError):
        spec.name = "Mutated Name"
