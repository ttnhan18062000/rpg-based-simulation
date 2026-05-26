# Compliance IDs: MUTATION-TEST-001, MUTATION-TEST-002, MUTATION-TEST-003
import pytest
from unittest.mock import MagicMock

from src.worldbuilding.schema import WorldSpec, InvalidWorldSpecError
from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.validator import WorldValidator
from src.lab.schema import ScenarioSpec, MutationSpec, InvalidScenarioSpecError
from src.lab.mutation import MutationEngine, InvalidMutationTargetError


@pytest.fixture
def base_world_dict():
    return {
        "schema_version": "worldspec.v1",
        "world_id": "test_world",
        "name": "Test World",
        "description": "Base world for testing mutations",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        },
        "regions": [
            {
                "id": "wood_zone",
                "type": "forest",
                "bounds": [0, 0, 50, 50],
                "terrain": "GRASS",
                "hazard_level": 0.1
            }
        ],
        "factions": [
            {
                "id": "village",
                "type": "settlement"
            }
        ],
        "entities": [
            {
                "id": "miner",
                "count": 5,
                "role": "gatherer",
                "faction": "village",
                "spawn_region": "wood_zone"
            }
        ],
        "resources": [
            {
                "id": "oak_tree",
                "resource_type": "wood",
                "count": 100,
                "region": "wood_zone"
            }
        ],
        "buildings": [
            {
                "id": "shop",
                "type": "store",
                "region": "wood_zone"
            }
        ],
        "quests": []
    }


@pytest.fixture
def base_scenario_dict():
    return {
        "schema_version": "scenariospec.v1",
        "scenario_id": "test_scenario",
        "name": "Test Scenario",
        "world_id": "test_world",
        "scenario_type": "resource_economy",
        "intent": {
            "primary_goal": "test_mutation",
            "description": "Standard base scenario"
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
        "tags": ["test"]
    }


def test_set_operation_works(base_world_dict, base_scenario_dict):
    """Verify that the set operation correctly replaces target values."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    mutation_dict = {
        "schema_version": "mutationspec.v1",
        "mutation_id": "test_sweep",
        "name": "Test sweep matrix",
        "base_world_id": "test_world",
        "base_scenario_id": "test_scenario",
        "mutations": [
            {
                "id": "set_width",
                "target": "topology.width",
                "operation": "set",
                "value": 200
            }
        ],
        "matrix": {
            "mode": "one_at_a_time",
            "max_variants": 10
        }
    }
    mutation_spec = MutationSpec(**mutation_dict)

    engine = MutationEngine()
    mutated_world, mutated_scenario, reports = engine.apply_mutations(world, scenario, mutation_spec)

    assert len(reports) == 1
    assert reports[0].status == "SUCCESS"
    assert reports[0].old_value == 100
    assert reports[0].new_value == 200
    assert mutated_world.topology.width == 200


def test_add_operation_works(base_world_dict, base_scenario_dict):
    """Verify that the add operation correctly applies numeric shifts."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    mutation_dict = {
        "schema_version": "mutationspec.v1",
        "mutation_id": "test_sweep",
        "name": "Test sweep matrix",
        "base_world_id": "test_world",
        "base_scenario_id": "test_scenario",
        "mutations": [
            {
                "id": "add_miner_count",
                "target": "entities.miner.count",
                "operation": "add",
                "value": 10
            }
        ],
        "matrix": {
            "mode": "one_at_a_time",
            "max_variants": 10
        }
    }
    mutation_spec = MutationSpec(**mutation_dict)

    engine = MutationEngine()
    mutated_world, mutated_scenario, reports = engine.apply_mutations(world, scenario, mutation_spec)

    assert len(reports) == 1
    assert reports[0].status == "SUCCESS"
    assert reports[0].old_value == 5
    assert reports[0].new_value == 15
    assert mutated_world.entities[0].count == 15


def test_multiply_operation_works(base_world_dict, base_scenario_dict):
    """Verify that multiply operation correctly scales targets."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    mutation_dict = {
        "schema_version": "mutationspec.v1",
        "mutation_id": "test_sweep",
        "name": "Test sweep matrix",
        "base_world_id": "test_world",
        "base_scenario_id": "test_scenario",
        "mutations": [
            {
                "id": "multiply_resource",
                "target": "resources.oak_tree.count",
                "operation": "multiply",
                "value": 2.5
            }
        ],
        "matrix": {
            "mode": "one_at_a_time",
            "max_variants": 10
        }
    }
    mutation_spec = MutationSpec(**mutation_dict)

    engine = MutationEngine()
    mutated_world, mutated_scenario, reports = engine.apply_mutations(world, scenario, mutation_spec)

    assert len(reports) == 1
    assert reports[0].status == "SUCCESS"
    assert reports[0].old_value == 100
    assert reports[0].new_value == 250
    assert mutated_world.resources[0].count == 250


def test_toggle_operation_works(base_world_dict, base_scenario_dict):
    """Verify boolean toggle switches behave properly."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    mutation_dict = {
        "schema_version": "mutationspec.v1",
        "mutation_id": "test_sweep",
        "name": "Test sweep matrix",
        "base_world_id": "test_world",
        "base_scenario_id": "test_scenario",
        "mutations": [
            {
                "id": "toggle_bounds",
                "target": "validation.allow_overlapping_regions",
                "operation": "toggle"
            }
        ],
        "matrix": {
            "mode": "one_at_a_time",
            "max_variants": 10
        }
    }
    mutation_spec = MutationSpec(**mutation_dict)

    engine = MutationEngine()
    mutated_world, mutated_scenario, reports = engine.apply_mutations(world, scenario, mutation_spec)

    assert len(reports) == 1
    assert reports[0].status == "SUCCESS"
    assert reports[0].old_value is False
    assert reports[0].new_value is True
    assert mutated_world.validation.allow_overlapping_regions is True


def test_remove_operation_works(base_world_dict, base_scenario_dict):
    """Verify targets can be safely removed."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    mutation_dict = {
        "schema_version": "mutationspec.v1",
        "mutation_id": "test_sweep",
        "name": "Test sweep matrix",
        "base_world_id": "test_world",
        "base_scenario_id": "test_scenario",
        "mutations": [
            {
                "id": "remove_miner",
                "target": "entities.miner",
                "operation": "remove"
            }
        ],
        "matrix": {
            "mode": "one_at_a_time",
            "max_variants": 10
        }
    }
    mutation_spec = MutationSpec(**mutation_dict)

    engine = MutationEngine()
    mutated_world, mutated_scenario, reports = engine.apply_mutations(world, scenario, mutation_spec)

    assert len(reports) == 1
    assert reports[0].status == "SUCCESS"
    assert len(mutated_world.entities) == 0


def test_duplicate_operation_works(base_world_dict, base_scenario_dict):
    """Verify list structures can duplicate entities with new IDs."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    mutation_dict = {
        "schema_version": "mutationspec.v1",
        "mutation_id": "test_sweep",
        "name": "Test sweep matrix",
        "base_world_id": "test_world",
        "base_scenario_id": "test_scenario",
        "mutations": [
            {
                "id": "duplicate_miner",
                "target": "entities.miner",
                "operation": "duplicate",
                "value": "super_miner"
            }
        ],
        "matrix": {
            "mode": "one_at_a_time",
            "max_variants": 10
        }
    }
    mutation_spec = MutationSpec(**mutation_dict)

    engine = MutationEngine()
    mutated_world, mutated_scenario, reports = engine.apply_mutations(world, scenario, mutation_spec)

    assert len(reports) == 1
    assert reports[0].status == "SUCCESS"
    assert len(mutated_world.entities) == 2
    assert mutated_world.entities[0].id == "miner"
    assert mutated_world.entities[1].id == "super_miner"
    assert mutated_world.entities[1].count == 5


def test_base_spec_remains_unmutated(base_world_dict, base_scenario_dict):
    """Verify that applying mutations leaves base WorldSpec and ScenarioSpec completely untouched."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    mutation_dict = {
        "schema_version": "mutationspec.v1",
        "mutation_id": "test_sweep",
        "name": "Test sweep matrix",
        "base_world_id": "test_world",
        "base_scenario_id": "test_scenario",
        "mutations": [
            {
                "id": "set_width",
                "target": "topology.width",
                "operation": "set",
                "value": 999
            }
        ],
        "matrix": {
            "mode": "one_at_a_time",
            "max_variants": 10
        }
    }
    mutation_spec = MutationSpec(**mutation_dict)

    engine = MutationEngine()
    mutated_world, mutated_scenario, reports = engine.apply_mutations(world, scenario, mutation_spec)

    assert world.topology.width == 100
    assert mutated_world.topology.width == 999


def test_invalid_target_fails_clearly(base_world_dict, base_scenario_dict):
    """Verify non-existent target paths fail gracefully with clear reports in non-strict mode."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    mutation_dict = {
        "schema_version": "mutationspec.v1",
        "mutation_id": "test_sweep",
        "name": "Test sweep matrix",
        "base_world_id": "test_world",
        "base_scenario_id": "test_scenario",
        "mutations": [
            {
                "id": "invalid_path",
                "target": "topology.depth_xyz",
                "operation": "set",
                "value": 10
            }
        ],
        "matrix": {
            "mode": "one_at_a_time",
            "max_variants": 10
        }
    }
    mutation_spec = MutationSpec(**mutation_dict)

    engine = MutationEngine()
    mutated_world, mutated_scenario, reports = engine.apply_mutations(world, scenario, mutation_spec)

    assert len(reports) == 1
    assert reports[0].status == "FAILED"
    assert "not found in dictionary" in reports[0].errors[0]


def test_strict_mode_raises_exceptions(base_world_dict, base_scenario_dict):
    """Verify strict mode raises explicit exceptions for invalid paths."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    mutation_spec = MutationSpec(
        schema_version="mutationspec.v1",
        mutation_id="test_sweep",
        name="Test sweep matrix",
        base_world_id="test_world",
        base_scenario_id="test_scenario",
        mutations=[
            {
                "id": "invalid_path",
                "target": "topology.depth_xyz",
                "operation": "set",
                "value": 10
            }
        ],
        matrix={"mode": "one_at_a_time", "max_variants": 10}
    )

    engine = MutationEngine()
    with pytest.raises(InvalidMutationTargetError) as exc_info:
        engine.apply_mutations(world, scenario, mutation_spec, strict=True)
    assert "not found in dictionary" in str(exc_info.value)


def test_invalid_resulting_world_fails_validation(base_world_dict, base_scenario_dict):
    """Verify invalid mutations resulting in invalid schema states are blocked."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    # Set topology height to a negative number which violates schema constraints
    mutation_spec = MutationSpec(
        schema_version="mutationspec.v1",
        mutation_id="test_sweep",
        name="Test sweep matrix",
        base_world_id="test_world",
        base_scenario_id="test_scenario",
        mutations=[
            {
                "id": "invalid_height",
                "target": "topology.height",
                "operation": "set",
                "value": -50
            }
        ],
        matrix={"mode": "one_at_a_time", "max_variants": 10}
    )

    engine = MutationEngine()
    mutated_world, mutated_scenario, reports = engine.apply_mutations(world, scenario, mutation_spec)

    assert len(reports) == 1
    assert reports[0].status == "FAILED"
    assert "height" in reports[0].errors[0]


def test_mutation_cannot_bypass_world_validator(base_world_dict, base_scenario_dict):
    """Verify that semantic validation (e.g. SpawnRegionExistenceRule) blocks invalid worlds."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    # Change miner spawn_region to a missing region name
    mutation_spec = MutationSpec(
        schema_version="mutationspec.v1",
        mutation_id="test_sweep",
        name="Test sweep matrix",
        base_world_id="test_world",
        base_scenario_id="test_scenario",
        mutations=[
            {
                "id": "invalid_spawn_region",
                "target": "entities.miner.spawn_region",
                "operation": "set",
                "value": "missing_ghost_zone"
            }
        ],
        matrix={"mode": "one_at_a_time", "max_variants": 10}
    )

    engine = MutationEngine()
    mutated_world, mutated_scenario, reports = engine.apply_mutations(world, scenario, mutation_spec)

    assert len(reports) == 1
    assert reports[0].status == "FAILED"
    assert "spawn region 'missing_ghost_zone' does not exist" in reports[0].errors[0]


def test_layout_placeholder_skipping(base_world_dict, base_scenario_dict):
    """Verify that optional dummy layout sections (like resources.nodes.oak_tree) are skipped gracefully."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    mutation_spec = MutationSpec(
        schema_version="mutationspec.v1",
        mutation_id="test_sweep",
        name="Test sweep matrix",
        base_world_id="test_world",
        base_scenario_id="test_scenario",
        mutations=[
            {
                "id": "skip_placeholder",
                "target": "resources.nodes.oak_tree.count",
                "operation": "set",
                "value": 888
            }
        ],
        matrix={"mode": "one_at_a_time", "max_variants": 10}
    )

    engine = MutationEngine()
    mutated_world, mutated_scenario, reports = engine.apply_mutations(world, scenario, mutation_spec)

    assert len(reports) == 1
    assert reports[0].status == "SUCCESS"
    assert mutated_world.resources[0].count == 888
