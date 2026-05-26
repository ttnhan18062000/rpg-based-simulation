# Compliance IDs: MUTATION-TEST-001, MUTATION-TEST-002, MUTATION-TEST-003
import pytest
from pathlib import Path
from src.lab.schema import (
    MutationSpec,
    InvalidMutationSpecError,
    load_mutation_spec_from_yaml,
    SetMutation,
    AddMutation,
    MultiplyMutation,
    ToggleMutation,
    RemoveMutation,
    DuplicateMutation
)


def test_valid_mutationspec_loads(tmp_path: Path):
    """Verify that a standard valid mutation spec with all operation types loads cleanly."""
    raw_yaml = """
schema_version: mutationspec.v1
mutation_id: resource_density_matrix
name: Resource Density Matrix

base_world_id: resource_valley_basic
base_scenario_id: resource_economy_basic

mutations:
  - id: wood_density_low
    target: resources.wood_zone.count
    operation: multiply
    value: 0.5
  - id: gold_density_high
    target: resources.gold_mine.count
    operation: add
    value: 5
  - id: set_max_entities
    target: entities.max_count
    operation: set
    value: 100
  - id: toggle_safety
    target: options.safety_enabled
    operation: toggle
    value: false
  - id: remove_building
    target: buildings.village_shop
    operation: remove
  - id: duplicate_miner
    target: entities.miner
    operation: duplicate
    value: super_miner

matrix:
  mode: one_at_a_time
  max_variants: 20

expected_relationships:
  - id: wood_reduction_decreases_production
    type: monotonic_non_decreasing
    metric: resource_production_rate
    baseline_variant: base
    compared_variant: wood_density_low

budgets:
  max_variant_count: 10
  max_total_ticks: 50000

tags:
  - economy
  - unit_test
"""
    yaml_file = tmp_path / "mutation.yaml"
    yaml_file.write_text(raw_yaml)

    spec = load_mutation_spec_from_yaml(yaml_file)
    assert spec.schema_version == "mutationspec.v1"
    assert spec.mutation_id == "resource_density_matrix"
    assert spec.base_world_id == "resource_valley_basic"
    assert spec.base_scenario_id == "resource_economy_basic"
    
    # Verify polymorphic mutation items list
    assert len(spec.mutations) == 6
    
    # 1. multiply
    m0 = spec.mutations[0]
    assert isinstance(m0, MultiplyMutation)
    assert m0.id == "wood_density_low"
    assert m0.operation == "multiply"
    assert m0.value == 0.5
    
    # 2. add
    m1 = spec.mutations[1]
    assert isinstance(m1, AddMutation)
    assert m1.id == "gold_density_high"
    assert m1.operation == "add"
    assert m1.value == 5.0
    
    # 3. set
    m2 = spec.mutations[2]
    assert isinstance(m2, SetMutation)
    assert m2.id == "set_max_entities"
    assert m2.operation == "set"
    assert m2.value == 100
    
    # 4. toggle
    m3 = spec.mutations[3]
    assert isinstance(m3, ToggleMutation)
    assert m3.id == "toggle_safety"
    assert m3.operation == "toggle"
    assert m3.value is False
    
    # 5. remove
    m4 = spec.mutations[4]
    assert isinstance(m4, RemoveMutation)
    assert m4.id == "remove_building"
    assert m4.operation == "remove"
    
    # 6. duplicate
    m5 = spec.mutations[5]
    assert isinstance(m5, DuplicateMutation)
    assert m5.id == "duplicate_miner"
    assert m5.operation == "duplicate"
    assert m5.value == "super_miner"

    # Verify matrix, expected_relationships, budgets, tags
    assert spec.matrix.mode == "one_at_a_time"
    assert spec.matrix.max_variants == 20
    assert len(spec.expected_relationships) == 1
    assert spec.expected_relationships[0].id == "wood_reduction_decreases_production"
    assert spec.expected_relationships[0].type == "monotonic_non_decreasing"
    assert spec.budgets.max_variant_count == 10
    assert spec.budgets.max_total_ticks == 50000
    assert "economy" in spec.tags


def test_missing_required_fields(tmp_path: Path):
    """Verify that missing required top-level fields are rejected."""
    raw_yaml = """
schema_version: mutationspec.v1
name: Resource Density Matrix
base_world_id: resource_valley_basic
# missing base_scenario_id, mutation_id, and matrix
"""
    yaml_file = tmp_path / "mutation_invalid.yaml"
    yaml_file.write_text(raw_yaml)

    with pytest.raises(InvalidMutationSpecError) as exc_info:
        load_mutation_spec_from_yaml(yaml_file)
    assert "validation failed" in str(exc_info.value)
    assert "mutation_id" in str(exc_info.value)
    assert "base_scenario_id" in str(exc_info.value)
    assert "matrix" in str(exc_info.value)


def test_invalid_operation_rejected(tmp_path: Path):
    """Verify that an invalid operation literal is rejected."""
    raw_yaml = """
schema_version: mutationspec.v1
mutation_id: resource_density_matrix
name: Resource Density Matrix
base_world_id: resource_valley_basic
base_scenario_id: resource_economy_basic
mutations:
  - id: wood_density_low
    target: resources.wood_zone.count
    operation: divide  # invalid operation
    value: 0.5
matrix:
  mode: one_at_a_time
"""
    yaml_file = tmp_path / "mutation_invalid_op.yaml"
    yaml_file.write_text(raw_yaml)

    with pytest.raises(InvalidMutationSpecError) as exc_info:
        load_mutation_spec_from_yaml(yaml_file)
    assert "validation failed" in str(exc_info.value)
    assert "mutations" in str(exc_info.value)


def test_invalid_numeric_operands(tmp_path: Path):
    """Verify that numeric operations multiply/add require numeric values."""
    raw_yaml = """
schema_version: mutationspec.v1
mutation_id: resource_density_matrix
name: Resource Density Matrix
base_world_id: resource_valley_basic
base_scenario_id: resource_economy_basic
mutations:
  - id: wood_density_low
    target: resources.wood_zone.count
    operation: multiply
    value: "not_a_number"  # invalid value type
matrix:
  mode: one_at_a_time
"""
    yaml_file = tmp_path / "mutation_invalid_val.yaml"
    yaml_file.write_text(raw_yaml)

    with pytest.raises(InvalidMutationSpecError) as exc_info:
        load_mutation_spec_from_yaml(yaml_file)
    assert "validation failed" in str(exc_info.value)


def test_matrix_modes_validation(tmp_path: Path):
    """Verify that matrix config rejects invalid modes."""
    raw_yaml = """
schema_version: mutationspec.v1
mutation_id: resource_density_matrix
name: Resource Density Matrix
base_world_id: resource_valley_basic
base_scenario_id: resource_economy_basic
matrix:
  mode: invalid_sweep_mode
"""
    yaml_file = tmp_path / "mutation_invalid_mode.yaml"
    yaml_file.write_text(raw_yaml)

    with pytest.raises(InvalidMutationSpecError) as exc_info:
        load_mutation_spec_from_yaml(yaml_file)
    assert "mode must be one of" in str(exc_info.value)


def test_extra_fields_preserved(tmp_path: Path):
    """Verify that unrecognized metadata or future fields are preserved under model_extra."""
    raw_yaml = """
schema_version: mutationspec.v1
mutation_id: resource_density_matrix
name: Resource Density Matrix
base_world_id: resource_valley_basic
base_scenario_id: resource_economy_basic
matrix:
  mode: one_at_a_time
future_expansion_field:
  nested_key: nested_value
"""
    yaml_file = tmp_path / "mutation_extra.yaml"
    yaml_file.write_text(raw_yaml)

    spec = load_mutation_spec_from_yaml(yaml_file)
    assert hasattr(spec, "future_expansion_field")
    assert spec.future_expansion_field == {"nested_key": "nested_value"}
