# Compliance IDs: MUTATION-TEST-004, MUTATION-TEST-005, MUTATION-TEST-006
import pytest
from unittest.mock import MagicMock
from src.worldbuilding.repository import WorldRepository
from src.lab.schema import MutationSpec, InvalidMutationSpecError
from src.lab.validator import (
    MutationValidator,
    BaseReferencesRule,
    MetamorphicRelationshipRule
)


@pytest.fixture
def base_mutation_spec_dict():
    return {
        "schema_version": "mutationspec.v1",
        "mutation_id": "economy_density_sweep",
        "name": "Economy Density Sweep",
        "base_world_id": "existing_world",
        "base_scenario_id": "existing_scenario",
        "mutations": [
            {
                "id": "wood_low",
                "target": "resources.wood_zone.count",
                "operation": "multiply",
                "value": 0.5
            },
            {
                "id": "gold_high",
                "target": "resources.gold_mine.count",
                "operation": "add",
                "value": 10.0
            }
        ],
        "matrix": {
            "mode": "one_at_a_time",
            "max_variants": 10
        },
        "expected_relationships": [
            {
                "id": "wood_impact",
                "type": "monotonic_non_decreasing",
                "metric": "resource_production_rate",
                "baseline_variant": "base",
                "compared_variant": "wood_low"
            }
        ],
        "budgets": {
            "max_variant_count": 5,
            "max_total_ticks": 1000
        },
        "tags": ["economy"]
    }


def test_validator_base_references_success(base_mutation_spec_dict):
    """Verify validation passes when base world and scenario exist in repositories."""
    spec = MutationSpec(**base_mutation_spec_dict)
    
    mock_world_repo = MagicMock(spec=WorldRepository)
    mock_world_repo.list_worlds.return_value = ["existing_world", "other_world"]
    
    # We mock scenario_repo as a generic object with a list_scenarios method
    mock_scenario_repo = MagicMock()
    mock_scenario_repo.list_scenarios.return_value = ["existing_scenario", "other_scenario"]

    validator = MutationValidator(world_repo=mock_world_repo, scenario_repo=mock_scenario_repo)
    issues = validator.validate(spec, strict=False)
    
    # No error or warning issues should exist
    assert len(issues) == 0


def test_validator_base_references_missing_world(base_mutation_spec_dict):
    """Verify error is raised when base world does not exist."""
    base_mutation_spec_dict["base_world_id"] = "nonexistent_world"
    spec = MutationSpec(**base_mutation_spec_dict)
    
    mock_world_repo = MagicMock(spec=WorldRepository)
    mock_world_repo.list_worlds.return_value = ["existing_world"]
    
    mock_scenario_repo = MagicMock()
    mock_scenario_repo.list_scenarios.return_value = ["existing_scenario"]

    validator = MutationValidator(world_repo=mock_world_repo, scenario_repo=mock_scenario_repo)
    
    with pytest.raises(InvalidMutationSpecError) as exc_info:
        validator.validate(spec, strict=False)
    assert "references a non-existent base_world_id" in str(exc_info.value)


def test_validator_base_references_missing_scenario(base_mutation_spec_dict):
    """Verify error is raised when base scenario does not exist."""
    base_mutation_spec_dict["base_scenario_id"] = "nonexistent_scenario"
    spec = MutationSpec(**base_mutation_spec_dict)
    
    mock_world_repo = MagicMock(spec=WorldRepository)
    mock_world_repo.list_worlds.return_value = ["existing_world"]
    
    mock_scenario_repo = MagicMock()
    mock_scenario_repo.list_scenarios.return_value = ["existing_scenario"]

    validator = MutationValidator(world_repo=mock_world_repo, scenario_repo=mock_scenario_repo)
    
    with pytest.raises(InvalidMutationSpecError) as exc_info:
        validator.validate(spec, strict=False)
    assert "references a non-existent base_scenario_id" in str(exc_info.value)


def test_validator_metamorphic_variant_existence_invalid_baseline(base_mutation_spec_dict):
    """Verify error is raised when a metamorphic rule references an undefined baseline variant."""
    base_mutation_spec_dict["expected_relationships"][0]["baseline_variant"] = "undefined_variant"
    spec = MutationSpec(**base_mutation_spec_dict)
    
    validator = MutationValidator()
    with pytest.raises(InvalidMutationSpecError) as exc_info:
        validator.validate(spec, strict=False)
    assert "references an undefined baseline variant ID" in str(exc_info.value)


def test_validator_metamorphic_variant_existence_invalid_compared(base_mutation_spec_dict):
    """Verify error is raised when a metamorphic rule references an undefined compared variant."""
    base_mutation_spec_dict["expected_relationships"][0]["compared_variant"] = "undefined_variant"
    spec = MutationSpec(**base_mutation_spec_dict)
    
    validator = MutationValidator()
    with pytest.raises(InvalidMutationSpecError) as exc_info:
        validator.validate(spec, strict=False)
    assert "references an undefined compared variant ID" in str(exc_info.value)


def test_validator_unrecognized_metric_warning(base_mutation_spec_dict):
    """Verify that referencing an unrecognized custom metric yields a warning but permits validation under non-strict mode."""
    base_mutation_spec_dict["expected_relationships"][0]["metric"] = "unrecognized_custom_telemetry_metric"
    spec = MutationSpec(**base_mutation_spec_dict)
    
    validator = MutationValidator()
    issues = validator.validate(spec, strict=False)
    
    # Non-strict mode: validation completes and returns the warning issue
    warnings = [x for x in issues if x.severity == "WARNING" and x.rule_id == "MUTATION-META-WARN"]
    assert len(warnings) == 1
    assert "references unrecognized metric 'unrecognized_custom_telemetry_metric'" in warnings[0].message


def test_validator_strict_mode_elevates_warning(base_mutation_spec_dict):
    """Verify that strict mode elevates metric warnings to errors, blocking validation."""
    base_mutation_spec_dict["expected_relationships"][0]["metric"] = "unrecognized_custom_telemetry_metric"
    spec = MutationSpec(**base_mutation_spec_dict)
    
    validator = MutationValidator()
    with pytest.raises(InvalidMutationSpecError) as exc_info:
        validator.validate(spec, strict=True)
    assert "strict validation failed" in str(exc_info.value)
    assert "references unrecognized metric 'unrecognized_custom_telemetry_metric'" in str(exc_info.value)
