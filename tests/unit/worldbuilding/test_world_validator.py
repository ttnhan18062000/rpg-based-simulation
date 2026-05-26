# Compliance IDs: WORLD-070, WORLD-071, WORLD-072
import pytest
from src.worldbuilding.schema import WorldSpec, InvalidWorldSpecError
from src.worldbuilding.validator import WorldValidator

def create_valid_base_spec() -> dict:
    return {
        "schema_version": "worldspec.v1",
        "world_id": "valid_valley",
        "name": "Valid Valley",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        },
        "regions": [
            {"id": "village", "type": "settlement", "bounds": [0, 0, 30, 30]}
        ],
        "factions": [
            {"id": "villagers", "type": "civilian"}
        ],
        "entities": [
            {"id": "workers", "count": 10, "role": "worker", "faction": "villagers", "spawn_region": "village"}
        ],
        "resources": [
            {"id": "wood_node", "resource_type": "wood", "count": 10, "region": "village"}
        ]
    }

def test_validator_valid_world():
    data = create_valid_base_spec()
    spec = WorldSpec.model_validate(data)
    
    validator = WorldValidator()
    issues = validator.validate(spec)
    
    # Valid world should have no issues (no warnings or errors)
    assert issues == []

def test_validator_raises_error_on_violations():
    data = create_valid_base_spec()
    # Induce an ERROR violation: unknown spawn region
    data["entities"][0]["spawn_region"] = "missing_region"
    
    spec = WorldSpec.model_validate(data)
    validator = WorldValidator()
    
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        validator.validate(spec)
    assert "WORLD-REF-002" in str(exc_info.value)

def test_validator_determinism():
    data = create_valid_base_spec()
    # Induce multiple violations
    data["entities"][0]["spawn_region"] = "missing_region"
    data["entities"][0]["faction"] = "missing_faction"
    
    spec = WorldSpec.model_validate(data)
    validator = WorldValidator()
    
    # Running multiple times must yield exact same order
    res1 = validator.validate
    with pytest.raises(InvalidWorldSpecError) as err1:
        validator.validate(spec)
    
    with pytest.raises(InvalidWorldSpecError) as err2:
        validator.validate(spec)
        
    assert str(err1.value) == str(err2.value)

def test_validator_strict_mode_blocks_warnings():
    data = create_valid_base_spec()
    # Empty out resources to trigger WORLD-WARN-001 (WARNING)
    data["resources"] = []
    
    spec = WorldSpec.model_validate(data)
    validator = WorldValidator()
    
    # 1. Non-strict mode should allow warnings and return them
    issues = validator.validate(spec, strict=False)
    assert len(issues) == 1
    assert issues[0].rule_id == "WORLD-WARN-001"
    assert issues[0].severity == "WARNING"

    # 2. Strict mode should raise InvalidWorldSpecError for warnings
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        validator.validate(spec, strict=True)
    assert "WORLD-WARN-001" in str(exc_info.value)

def test_validator_unknown_sections():
    raw_data = create_valid_base_spec()
    # Add an unexpected/unknown top-level section
    raw_data["future_expansion_intent"] = {"custom_key": "custom_val"}
    
    # Pydantic validates the spec and ignores extra keys
    spec = WorldSpec.model_validate(raw_data)
    
    validator = WorldValidator()
    issues = validator.validate(spec, raw_data=raw_data)
    
    # Validator should detect the extra section and flag it as a WARNING
    assert len(issues) == 1
    assert issues[0].rule_id == "WORLD-UNEXPECTED-SECTION"
    assert issues[0].severity == "WARNING"
    assert "future_expansion_intent" in issues[0].message
    assert issues[0].path == "future_expansion_intent"

def test_validator_does_not_modify_spec():
    raw_data = create_valid_base_spec()
    spec = WorldSpec.model_validate(raw_data)
    
    # Cache attributes
    orig_name = spec.name
    orig_width = spec.topology.width
    
    validator = WorldValidator()
    validator.validate(spec)
    
    # Values must remain identical (Pydantic model is frozen, but we assert state stability)
    assert spec.name == orig_name
    assert spec.topology.width == orig_width
