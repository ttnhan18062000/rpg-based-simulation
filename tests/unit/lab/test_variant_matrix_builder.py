# Compliance IDs: MUTATION-MATRIX-TEST-001, MUTATION-MATRIX-TEST-002, MUTATION-MATRIX-TEST-003
import pytest
from pathlib import Path
import yaml

from src.worldbuilding.schema import WorldSpec
from src.lab.schema import ScenarioSpec, MutationSpec, VariantManifest
from src.lab.mutation import VariantMatrixBuilder, MutationEngine


@pytest.fixture
def base_world_dict():
    return {
        "schema_version": "worldspec.v1",
        "world_id": "test_world",
        "name": "Test World",
        "description": "Base world for testing",
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
        "resources": [],
        "buildings": [],
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
            "primary_goal": "test_matrix",
            "description": "Standard base scenario"
        },
        "expected_behavior": {},
        "required_signals": {
            "metrics": [],
            "events": [],
            "cognition": []
        },
        "allowed_anomalies": [],
        "critical_anomalies": [],
        "tags": ["test"]
    }


def test_base_variant_is_included(base_world_dict, base_scenario_dict, tmp_path):
    """Verify that the base variant is always included and saved first."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    mutation_spec = MutationSpec(
        schema_version="mutationspec.v1",
        mutation_id="test_sweep",
        name="Test sweep",
        base_world_id="test_world",
        base_scenario_id="test_scenario",
        mutations=[],
        matrix={"mode": "one_at_a_time", "max_variants": 10}
    )

    builder = VariantMatrixBuilder()
    manifests = builder.build_matrix(world, scenario, mutation_spec, tmp_path)

    assert len(manifests) == 1
    assert manifests[0].variant_id == "base"
    assert manifests[0].applied_mutations == []
    assert manifests[0].status == "VALIDATED"
    assert Path(manifests[0].world_spec_path).exists()
    assert Path(manifests[0].scenario_spec_path).exists()


def test_one_at_a_time_creates_expected_variants(base_world_dict, base_scenario_dict, tmp_path):
    """Verify that one_at_a_time mode generates base + one variant per mutation."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    mutation_spec = MutationSpec(
        schema_version="mutationspec.v1",
        mutation_id="test_sweep",
        name="Test sweep",
        base_world_id="test_world",
        base_scenario_id="test_scenario",
        mutations=[
            {
                "id": "mut_width",
                "target": "topology.width",
                "operation": "set",
                "value": 200
            },
            {
                "id": "mut_height",
                "target": "topology.height",
                "operation": "set",
                "value": 300
            }
        ],
        matrix={"mode": "one_at_a_time", "max_variants": 10}
    )

    builder = VariantMatrixBuilder()
    manifests = builder.build_matrix(world, scenario, mutation_spec, tmp_path)

    # Base + 2 mutations = 3 variants total
    assert len(manifests) == 3
    assert manifests[0].variant_id == "base"
    assert manifests[1].variant_id == "var_one_mut_width"
    assert manifests[1].applied_mutations == ["mut_width"]
    assert manifests[2].variant_id == "var_one_mut_height"
    assert manifests[2].applied_mutations == ["mut_height"]

    # Verify content of the first mutated variant
    var1_world_path = Path(manifests[1].world_spec_path)
    with open(var1_world_path, "r") as f:
        data = yaml.safe_load(f)
    assert data["topology"]["width"] == 200
    assert data["topology"]["height"] == 100  # remains unchanged in this variant


def test_combined_creates_expected_variant(base_world_dict, base_scenario_dict, tmp_path):
    """Verify that combined mode generates base + one combined variant applying all mutations."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    mutation_spec = MutationSpec(
        schema_version="mutationspec.v1",
        mutation_id="test_sweep",
        name="Test sweep",
        base_world_id="test_world",
        base_scenario_id="test_scenario",
        mutations=[
            {
                "id": "mut_width",
                "target": "topology.width",
                "operation": "set",
                "value": 200
            },
            {
                "id": "mut_height",
                "target": "topology.height",
                "operation": "set",
                "value": 300
            }
        ],
        matrix={"mode": "combined", "max_variants": 10}
    )

    builder = VariantMatrixBuilder()
    manifests = builder.build_matrix(world, scenario, mutation_spec, tmp_path)

    # Base + 1 combined variant = 2 variants total
    assert len(manifests) == 2
    assert manifests[0].variant_id == "base"
    assert manifests[1].variant_id == "var_combined_all"
    assert manifests[1].applied_mutations == ["mut_width", "mut_height"]

    # Verify both mutations were applied to the combined variant
    var_combined_world_path = Path(manifests[1].world_spec_path)
    with open(var_combined_world_path, "r") as f:
        data = yaml.safe_load(f)
    assert data["topology"]["width"] == 200
    assert data["topology"]["height"] == 300


def test_factorial_limited_respects_max_variant_count(base_world_dict, base_scenario_dict, tmp_path):
    """Verify that factorial_limited mode generates size-ordered combinations and respects limit."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    # 3 mutations -> total combinations (base, 3 size-1, 3 size-2, 1 size-3 = 8 variants total)
    mutation_spec = MutationSpec(
        schema_version="mutationspec.v1",
        mutation_id="test_sweep",
        name="Test sweep",
        base_world_id="test_world",
        base_scenario_id="test_scenario",
        mutations=[
            {"id": "mut_a", "target": "topology.width", "operation": "set", "value": 110},
            {"id": "mut_b", "target": "topology.height", "operation": "set", "value": 120},
            {"id": "mut_c", "target": "name", "operation": "set", "value": "Mutated name"}
        ],
        # Cap strictly at 5 variants (should generate base + 3 size-1 combinations + 1 size-2 combination)
        matrix={"mode": "factorial_limited", "max_variants": 5}
    )

    builder = VariantMatrixBuilder()
    manifests = builder.build_matrix(world, scenario, mutation_spec, tmp_path)

    assert len(manifests) == 5
    assert manifests[0].variant_id == "base"
    
    # Next 3 variants should be size 1 combinations
    assert len(manifests[1].applied_mutations) == 1
    assert len(manifests[2].applied_mutations) == 1
    assert len(manifests[3].applied_mutations) == 1

    # 5th variant should be size 2 combination
    assert len(manifests[4].applied_mutations) == 2


def test_matrix_builder_refuses_unbounded_factorial(base_world_dict, base_scenario_dict, tmp_path):
    """Verify that builder refuses unbounded/excessive factorial sweeps by default."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    # 11 mutations, max_variants=2000 -> refused to prevent combinatorial crash
    mutation_spec = MutationSpec(
        schema_version="mutationspec.v1",
        mutation_id="test_sweep",
        name="Test sweep",
        base_world_id="test_world",
        base_scenario_id="test_scenario",
        mutations=[{"id": f"m_{i}", "target": "topology.width", "operation": "set", "value": 100} for i in range(11)],
        matrix={"mode": "factorial_limited", "max_variants": 2000}
    )

    builder = VariantMatrixBuilder()
    with pytest.raises(ValueError) as exc_info:
        builder.build_matrix(world, scenario, mutation_spec, tmp_path)
    assert "Combinatorial explosion check" in str(exc_info.value)


def test_failed_validation_records_failed_status(base_world_dict, base_scenario_dict, tmp_path):
    """Verify that variants failing validation are recorded with FAILED status and error logs."""
    world = WorldSpec(**base_world_dict)
    scenario = ScenarioSpec(**base_scenario_dict)

    # Set negative bounds causing schema validation failure
    mutation_spec = MutationSpec(
        schema_version="mutationspec.v1",
        mutation_id="test_sweep",
        name="Test sweep",
        base_world_id="test_world",
        base_scenario_id="test_scenario",
        mutations=[
            {
                "id": "mut_invalid",
                "target": "topology.width",
                "operation": "set",
                "value": -100
            }
        ],
        matrix={"mode": "one_at_a_time", "max_variants": 10}
    )

    builder = VariantMatrixBuilder()
    manifests = builder.build_matrix(world, scenario, mutation_spec, tmp_path)

    # Base + 1 failed variant = 2 total
    assert len(manifests) == 2
    assert manifests[0].status == "VALIDATED"
    assert manifests[1].status == "FAILED"
    assert manifests[1].validation_result is not None
    assert "error" in manifests[1].validation_result
    assert "width" in manifests[1].validation_result["error"]
