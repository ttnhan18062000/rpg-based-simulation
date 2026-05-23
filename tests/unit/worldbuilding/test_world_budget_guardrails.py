# Compliance IDs: WORLD-073, WORLD-074
import pytest
from src.worldbuilding.schema import WorldSpec, TopologySpec, RegionSpec, FactionSpec, PopulationSpec, ResourceNodeSpec, BuildingSpec, BudgetSpec
from src.worldbuilding.validator import WorldValidator, InvalidWorldSpecError

def create_base_world_spec(
    entities_count: int = 10,
    regions_count: int = 1,
    resources_count: int = 5,
    buildings_count: int = 1,
    width: int = 100,
    height: int = 100,
    budgets: BudgetSpec = None
) -> WorldSpec:
    """Helper to create a fully valid minimal spec with parameterized counts."""
    # Factions
    factions = [FactionSpec(id="villagers", type="civilian")]
    
    # Regions
    regions = []
    for idx in range(regions_count):
        regions.append(RegionSpec(id=f"region_{idx}", type="forest", bounds=(0, 0, width - 1, height - 1)))
        
    # Entities
    entities = []
    # Create population groups
    if entities_count > 0:
        entities.append(PopulationSpec(
            id="pop_group",
            count=entities_count,
            role="worker",
            faction="villagers",
            spawn_region="region_0"
        ))
        
    # Resources
    resources = []
    for idx in range(resources_count):
        resources.append(ResourceNodeSpec(
            id=f"res_{idx}",
            resource_type="wood",
            count=10,
            region="region_0"
        ))
        
    # Buildings
    buildings = []
    for idx in range(buildings_count):
        buildings.append(BuildingSpec(
            id=f"bld_{idx}",
            type="shop",
            region="region_0"
        ))
        
    return WorldSpec(
        schema_version="worldspec.v1",
        world_id="test_world",
        name="Test World",
        topology=TopologySpec(width=width, height=height, coordinate_system="grid"),
        regions=regions,
        factions=factions,
        entities=entities,
        resources=resources,
        buildings=buildings,
        budgets=budgets
    )

def test_local_dev_rejects_oversized_world():
    """Verify that the local_dev profile rejects a world with > 1000 entities."""
    # 1. 800 entities fits under local_dev (max 1000)
    spec_ok = create_base_world_spec(entities_count=800)
    validator = WorldValidator(profile="local_dev")
    issues = validator.validate(spec_ok)
    errors = [x for x in issues if x.severity == "ERROR"]
    assert not errors

    # 2. 1200 entities exceeds local_dev (max 1000)
    spec_fail = create_base_world_spec(entities_count=1200)
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        validator.validate(spec_fail)
    assert "Total entities count (1200) exceeds maximum allowed budget (1000)" in str(exc_info.value)

def test_ci_rejects_oversized_world():
    """Verify that the ci profile rejects a world with > 500 entities."""
    spec_fail = create_base_world_spec(entities_count=600)
    validator = WorldValidator(profile="ci")
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        validator.validate(spec_fail)
    assert "Total entities count (600) exceeds maximum allowed budget (500)" in str(exc_info.value)

def test_long_run_lab_allows_larger_world():
    """Verify that long_run_lab allows up to 10,000 entities, so 1500 entities is perfectly fine."""
    spec_ok = create_base_world_spec(entities_count=1500)
    validator = WorldValidator(profile="long_run_lab")
    issues = validator.validate(spec_ok)
    errors = [x for x in issues if x.severity == "ERROR"]
    assert not errors

def test_custom_budgets_override_profile_defaults():
    """Verify that explicitly configuring budgets inside the spec overrides the profile default limits."""
    # Normally, 1200 entities is blocked under local_dev.
    # But if we configure max_entities: 2000 in the budgets, it must be allowed!
    spec = create_base_world_spec(
        entities_count=1200,
        budgets=BudgetSpec(max_entities=2000)
    )
    validator = WorldValidator(profile="local_dev")
    issues = validator.validate(spec)
    errors = [x for x in issues if x.severity == "ERROR"]
    assert not errors

    # Conversely, if we specify max_entities: 100, then even 150 entities must fail.
    spec_fail = create_base_world_spec(
        entities_count=150,
        budgets=BudgetSpec(max_entities=100)
    )
    with pytest.raises(InvalidWorldSpecError) as exc_info:
        validator.validate(spec_fail)
    assert "Total entities count (150) exceeds maximum allowed budget (100)" in str(exc_info.value)

def test_warning_level_budget_guardrails():
    """Verify that resource node, building, area, and estimated artifact budgets produce warnings."""
    # Create a spec that exceeds the warning threshold for resource nodes in the 'ci' profile (limit is 100 resource nodes)
    # We specify 120 resource nodes
    spec = create_base_world_spec(resources_count=120)
    validator = WorldValidator(profile="ci")
    issues = validator.validate(spec)
    
    # Verify that WORLD-BUDGET-003 warning is present
    warnings = [x for x in issues if x.severity == "WARNING"]
    warning_ids = {x.rule_id for x in warnings}
    assert "WORLD-BUDGET-003" in warning_ids
    assert any("Total resource nodes count (120) exceeds maximum allowed budget (100)" in x.message for x in warnings)

def test_world_area_topology_warning():
    """Verify that a massive topological area triggers a WARNING."""
    spec = create_base_world_spec(width=2000, height=1000) # Area = 2,000,000 > 1,000,000
    validator = WorldValidator(profile="local_dev")
    issues = validator.validate(spec)
    
    warnings = [x for x in issues if x.severity == "WARNING"]
    warning_ids = {x.rule_id for x in warnings}
    assert "WORLD-BUDGET-005" in warning_ids
    assert any("World topology area (2000000 tiles) is very large" in x.message for x in warnings)

def test_estimated_artifact_size_warning():
    """Verify that forecasted log size exceeding max_expected_artifact_mb triggers a WARNING."""
    # Under CI profile, max_expected_artifact_mb is 100 MB.
    # Artifact Size Estimate = (Entities * Ticks * 0.0001) + (ResourceNodes * Ticks * 0.00005)
    # If we have 1,000,000 ticks or 1,200 entities:
    # 450 entities * 1000 ticks * 0.0001 = 45.0 MB
    # 1200 resources * 1000 ticks * 0.00005 = 60.0 MB
    # Total = 105.0 MB > 100 MB
    spec = create_base_world_spec(entities_count=450, resources_count=1200)
    validator = WorldValidator(profile="ci")
    issues = validator.validate(spec)
    
    warnings = [x for x in issues if x.severity == "WARNING"]
    warning_ids = {x.rule_id for x in warnings}
    assert "WORLD-BUDGET-006" in warning_ids
    assert any("Estimated artifact size" in x.message and "exceeds maximum allowed budget" in x.message for x in warnings)
