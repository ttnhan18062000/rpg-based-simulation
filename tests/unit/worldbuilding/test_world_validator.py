# Compliance IDs: WORLD-070, WORLD-071, WORLD-072
import pytest
from src.worldbuilding.schema import WorldSpec, InvalidWorldSpecError
from src.worldbuilding.validator import WorldValidator, ValidationContext

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

def test_validator_context_aware_filtering():
    data = create_valid_base_spec()
    # 1. No resources in MODULE context must pass without issues (NoResourcesWarningRule skipped)
    data["resources"] = []
    spec = WorldSpec.model_validate(data)
    
    validator = WorldValidator()
    issues = validator.validate(spec, context=ValidationContext.MODULE)
    assert issues == []  # Warning bypassed in MODULE context!

    # 2. Unknown spawn region in MODULE context should be bypassed because SpawnRegionExistenceRule is skipped in MODULE
    data["entities"][0]["spawn_region"] = "unknown_region"
    spec = WorldSpec.model_validate(data)
    issues = validator.validate(spec, context=ValidationContext.MODULE)
    assert issues == []

    # 3. FactionExistenceRule still runs in MODULE context
    data["entities"][0]["faction"] = "unknown_faction"
    spec = WorldSpec.model_validate(data)
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        validator.validate(spec, context=ValidationContext.MODULE)
    assert "WORLD-REF-001" in str(exc_info.value)

def test_validator_strict_mode_context_aware():
    data = create_valid_base_spec()
    data["resources"] = []  # Triggers warning in WORLD context, skipped in MODULE context
    spec = WorldSpec.model_validate(data)
    
    validator = WorldValidator()
    
    # Passing in MODULE context with strict=True must succeed (warning is skipped entirely)
    issues = validator.validate(spec, strict=True, context=ValidationContext.MODULE)
    assert issues == []

    # Passing in WORLD context with strict=True must fail (warning is evaluated and strict mode raises exception)
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        validator.validate(spec, strict=True, context=ValidationContext.WORLD)
    assert "WORLD-WARN-001" in str(exc_info.value)

def test_validator_custom_context_overrides():
    from src.worldbuilding.validator import WorldValidationRule, ValidationIssue
    
    # Create custom rule with context-specific overrides
    class ContextOverrideRule(WorldValidationRule):
        rule_id = "CUSTOM-001"
        severity = "WARNING"
        description = "Test custom overrides"
        severity_overrides = {
            ValidationContext.MODULE: "ERROR"
        }
        
        def validate(self, spec: WorldSpec, context: ValidationContext = ValidationContext.WORLD) -> list[ValidationIssue]:
            return [ValidationIssue(
                rule_id=self.rule_id,
                severity=self.get_severity(context),
                message="Custom warning raised"
            )]
            
    rule = ContextOverrideRule()
    
    # 1. Under WORLD, severity should remain default (WARNING)
    assert rule.get_severity(ValidationContext.WORLD) == "WARNING"
    
    # 2. Under MODULE, severity should override to (ERROR)
    assert rule.get_severity(ValidationContext.MODULE) == "ERROR"
