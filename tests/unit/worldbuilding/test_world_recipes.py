# Compliance IDs: WORLD-070, WORLD-071, WORLD-072
import pytest
from src.worldbuilding.recipe import WorldTemplateSpec, WorldTemplateExpander
from src.worldbuilding.schema import WorldSpec, InvalidWorldSpecError


def create_base_template_data() -> dict:
    return {
        "schema_version": "worldtemplate.v1",
        "world_id": "test_recipe_valley",
        "name": "Recipe Valley",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        },
        "regions": [
            {"id": "village", "type": "town", "grid_bounds": [0, 0, 30, 30], "terrain": "GRASS"},
            {"id": "woods", "type": "wilderness", "grid_bounds": [40, 40, 90, 90], "terrain": "FOREST"}
        ],
        "factions": [
            {"id": "villagers", "type": "civilian"},
            {"id": "monsters", "type": "hostile"}
        ],
        "entities": {
            "populations": [
                {
                    "role": "worker",
                    "count": 5,
                    "faction": "villagers",
                    "spawn_region": "village"
                },
                {
                    "role": "monster",
                    "count": 3,
                    "faction": "monsters",
                    "spawn_distribution": {
                        "type": "region_random",
                        "region": "woods"
                    }
                }
            ]
        },
        "resources": [
            {
                "resource_type": "wood",
                "count": 12,
                "region": "woods"
            }
        ],
        "buildings": [
            {
                "building_type": "inn",
                "count": 4,
                "region": "village"
            }
        ],
        "quests": []
    }


def test_population_recipe_expands_to_expected_count():
    """
    Verify that population recipe converts to PopulationSpec with expected counts
    and correct spawn regions.
    """
    data = create_base_template_data()
    template = WorldTemplateSpec.model_validate(data)
    
    spec = WorldTemplateExpander.expand(template, seed=42)
    assert isinstance(spec, WorldSpec)
    
    # We should have 2 population group specifications
    assert len(spec.entities) == 2
    
    # First: 5 workers in village
    p1 = spec.entities[0]
    assert p1.role == "worker"
    assert p1.count == 5
    assert p1.spawn_region == "village"
    
    # Second: 3 monsters in woods
    p2 = spec.entities[1]
    assert p2.role == "monster"
    assert p2.count == 3
    assert p2.spawn_region == "woods"


def test_resource_recipe_expands_to_expected_node_count():
    """
    Verify that a resource recipe of count N expands to exactly N distinct resource nodes.
    """
    data = create_base_template_data()
    template = WorldTemplateSpec.model_validate(data)
    
    spec = WorldTemplateExpander.expand(template, seed=42)
    
    # Count of resource specifications must be 12
    assert len(spec.resources) == 12
    for node in spec.resources:
        assert node.resource_type == "wood"
        assert node.region == "woods"
        assert node.count == 10  # default node charges


def test_building_recipe_expands_to_expected_building_count():
    """
    Verify that a building recipe of count N expands to exactly N building specs.
    """
    data = create_base_template_data()
    template = WorldTemplateSpec.model_validate(data)
    
    spec = WorldTemplateExpander.expand(template, seed=42)
    
    # Count of building specifications must be 4
    assert len(spec.buildings) == 4
    for bld in spec.buildings:
        assert bld.type == "inn"
        assert bld.region == "village"


def test_recipe_expansion_is_deterministic_by_seed():
    """
    Verify that identical template specifications compile to identical WorldSpec
    objects when run with the same seed.
    """
    data = create_base_template_data()
    template = WorldTemplateSpec.model_validate(data)
    
    spec1 = WorldTemplateExpander.expand(template, seed=99)
    spec2 = WorldTemplateExpander.expand(template, seed=99)
    
    # Pydantic dump of models must match perfectly
    assert spec1.model_dump() == spec2.model_dump()


def test_recipe_cannot_create_objects_outside_topology():
    """
    Verify that region recipe boundaries outside topological bounds trigger clear value errors.
    """
    data = create_base_template_data()
    # Map is 100x100. Let's make region bounds exceed 100
    data["regions"][0]["grid_bounds"] = [0, 0, 110, 20]
    
    template = WorldTemplateSpec.model_validate(data)
    
    with pytest.raises(ValueError, match="exceed map topology dimensions"):
        WorldTemplateExpander.expand(template, seed=42)


def test_recipe_ids_are_stable_and_traceable():
    """
    Verify that generated ID names are stable, repeatable, and easily traced.
    """
    data = create_base_template_data()
    template = WorldTemplateSpec.model_validate(data)
    
    spec = WorldTemplateExpander.expand(template, seed=42)
    
    # Entity ID tracing: pop_<role>_<faction>_<region>
    assert spec.entities[0].id == "pop_worker_villagers_village"
    assert spec.entities[1].id == "pop_monster_monsters_woods"
    
    # Resource node tracing: res_<resource_type>_<region>_<index>
    assert spec.resources[0].id == "res_wood_woods_0"
    assert spec.resources[11].id == "res_wood_woods_11"
    
    # Building tracing: bld_<building_type>_<region>_<index>
    assert spec.buildings[0].id == "bld_inn_village_0"
    assert spec.buildings[3].id == "bld_inn_village_3"


def test_recipe_expansion_does_not_bypass_validation():
    """
    Verify that expanded WorldSpec still passes through the validator engine,
    and invalid recipe configurations correctly throw InvalidWorldSpecError.
    """
    data = create_base_template_data()
    # Put a nonexistent faction on the entities recipe
    data["entities"]["populations"][0]["faction"] = "nonexistent_faction"
    
    template = WorldTemplateSpec.model_validate(data)
    
    # Validator should catch that nonexistent faction affiliation
    with pytest.raises(InvalidWorldSpecError, match="non-existent faction"):
        WorldTemplateExpander.expand(template, seed=42)
