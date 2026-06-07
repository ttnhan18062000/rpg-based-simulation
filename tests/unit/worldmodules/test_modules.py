# Compliance IDs: WORLD-MOD-TEST
import pytest
from src.worldmodules.repository import WorldModuleRepository
from src.worldmodules.schema import WorldModuleSpec
from src.worldmodules.utils import topological_sort_modules


@pytest.fixture
def base_repo():
    repo = WorldModuleRepository("data/world_modules")
    repo.load_all()
    return repo


def test_reusable_module_loading(base_repo):
    """Verify that the module repository discovers and parses standard baseline module configs."""
    assert "plains_layout" in base_repo.modules
    assert "standard_villagers" in base_repo.modules

    m_layout = base_repo.get_module("plains_layout")
    assert m_layout is not None
    assert m_layout.module_type == "terrain"
    assert m_layout.provides == ["baseline_layout"]
    assert len(m_layout.regions) == 1
    assert m_layout.regions[0].id == "town_center"

    m_pop = base_repo.get_module("standard_villagers")
    assert m_pop is not None
    assert m_pop.module_type == "population"
    assert m_pop.requires == ["plains_layout"]
    assert len(m_pop.population_recipes) == 2

    # Check fingerprint hash is available
    assert base_repo.module_fingerprint("plains_layout") is not None


def test_topological_sort():
    """Verify Kahn's topological sort and determinism."""
    # Define three specifications with sequential dependencies: C requires B, B requires A
    # We pass mock specs (simple namespace dictionaries simulating pydantic class interfaces)
    class MockSpec:
        def __init__(self, requires):
            self.requires = requires

    graph = {
        "C": MockSpec(requires=["B"]),
        "B": MockSpec(requires=["A"]),
        "A": MockSpec(requires=[]),
    }

    order = topological_sort_modules(graph)
    assert order == ["A", "B", "C"]


def test_circular_dependency_checks():
    """Verify circular references raise structural error."""
    class MockSpec:
        def __init__(self, requires):
            self.requires = requires

    circular_graph = {
        "A": MockSpec(requires=["B"]),
        "B": MockSpec(requires=["A"]),
    }

    with pytest.raises(ValueError) as exc_info:
        topological_sort_modules(circular_graph)
    assert "Circular dependency detected" in str(exc_info.value)


def test_normalizer_v1_and_v2():
    """Verify v1 and v2 modules parse correctly and normalize to NormalizedWorldModule."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer, NormalizedWorldModule

    # v1 spec
    v1_data = {
        "schema_version": "worldmodule.v1",
        "module_id": "v1_test_module",
        "module_type": "terrain",
        "display_name": "V1 Test Module",
        "description": "A v1 module",
        "version": "1.0.0",
        "regions": [
            {
                "id": "region_v1",
                "type": "forest",
                "grid_bounds": [0, 0, 10, 10],
            }
        ]
    }
    v1_spec = WorldModuleSpec(**v1_data)
    normalized_v1 = WorldModuleAuthoringNormalizer.normalize(v1_spec)
    assert isinstance(normalized_v1, NormalizedWorldModule)
    assert normalized_v1.module_id == "v1_test_module"
    assert len(normalized_v1.regions) == 1
    assert normalized_v1.regions[0].id == "region_v1"
    assert len(normalized_v1.biomes) == 0

    # v2 spec
    v2_data = {
        "schema_version": "worldmodule.v2",
        "module_id": "v2_test_module",
        "module_type": "ecology",
        "display_name": "V2 Test Module",
        "description": "A v2 module",
        "version": "2.0.0",
        "biomes": ["biome_v2"],
        "ecologies": ["ecology_v2"]
    }
    v2_spec = WorldModuleSpec(**v2_data)
    normalized_v2 = WorldModuleAuthoringNormalizer.normalize(v2_spec)
    assert isinstance(normalized_v2, NormalizedWorldModule)
    assert normalized_v2.module_id == "v2_test_module"
    assert len(normalized_v2.biomes) == 1
    assert normalized_v2.biomes[0] == "biome_v2"
    assert len(normalized_v2.regions) == 0


def test_invalid_v2_field_fails():
    """Verify that unknown fields on v2 modules cause a validation error."""
    from pydantic import ValidationError

    v2_invalid_data = {
        "schema_version": "worldmodule.v2",
        "module_id": "v2_invalid_module",
        "module_type": "ecology",
        "display_name": "Invalid V2 Module",
        "unknown_top_level_field": "some_value"
    }
    with pytest.raises(ValidationError):
        WorldModuleSpec(**v2_invalid_data)


def test_unsupported_module_type_registration():
    """Verify that unsupported module type fails unless explicitly registered."""
    from pydantic import ValidationError

    unsupported_data = {
        "schema_version": "worldmodule.v2",
        "module_id": "unsupported_module",
        "module_type": "custom_adventure",
        "display_name": "Unsupported Type Module"
    }

    # Should fail initially
    with pytest.raises(ValidationError) as exc_info:
        WorldModuleSpec(**unsupported_data)
    assert "module_type 'custom_adventure' is invalid" in str(exc_info.value)

    # Register the type
    WorldModuleSpec.register_module_type("custom_adventure")

    # Should succeed now
    spec = WorldModuleSpec(**unsupported_data)
    assert spec.module_type == "custom_adventure"


def test_list_resources_normalize_to_count_one():
    """Verify that a list of resources normalizes to a count of 1 for each."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_list_res",
        module_type="settlement",
        display_name="Test List Res",
        resources=["wood_node", "iron_vein"]
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)
    assert normalized.resources == {"wood_node": 1, "iron_vein": 1}


def test_dict_resources_preserve_counts():
    """Verify that a dict of resources preserves counts."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_dict_res",
        module_type="settlement",
        display_name="Test Dict Res",
        resources={"wood_node": 5, "iron_vein": 2}
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)
    assert normalized.resources == {"wood_node": 5, "iron_vein": 2}


def test_dict_buildings_preserve_counts():
    """Verify that a dict of buildings preserves counts."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_dict_bld",
        module_type="settlement",
        display_name="Test Dict Bld",
        buildings={"shop": 3, "tavern": 1}
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)
    assert normalized.buildings == {"shop": 3, "tavern": 1}


def test_dict_services_preserve_counts():
    """Verify that a dict of services preserves counts."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_dict_svc",
        module_type="settlement",
        display_name="Test Dict Svc",
        services={"healing": 2, "training": 1}
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)
    assert normalized.services == {"healing": 2, "training": 1}


def test_negative_count_fails():
    """Verify that a negative count in resources, buildings, or services fails normalization."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_neg",
        module_type="settlement",
        display_name="Test Neg",
        resources={"wood_node": -1}
    )
    with pytest.raises(ValueError) as exc_info:
        WorldModuleAuthoringNormalizer.normalize(spec)
    assert "Non-positive count" in str(exc_info.value)


def test_zero_count_fails():
    """Verify that a zero count in resources, buildings, or services fails normalization."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_zero",
        module_type="settlement",
        display_name="Test Zero",
        buildings={"shop": 0}
    )
    with pytest.raises(ValueError) as exc_info:
        WorldModuleAuthoringNormalizer.normalize(spec)
    assert "Non-positive count" in str(exc_info.value)


def test_duplicate_list_refs_fail():
    """Verify that duplicate items in a list shorthand fail normalization."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_dup",
        module_type="settlement",
        display_name="Test Dup",
        services=["healing", "healing"]
    )
    with pytest.raises(ValueError) as exc_info:
        WorldModuleAuthoringNormalizer.normalize(spec)
    assert "Duplicate list value" in str(exc_info.value)


# --- Typed ref collection tests ---

def test_string_biomes_normalize_to_tuple():
    """biomes field normalizes to Tuple[str, ...] when given list of strings."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer, NormalizedWorldModule
    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_biome_tuple",
        module_type="terrain",
        display_name="Biome Tuple Test",
        biomes=["forest", "plains"],
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)
    assert isinstance(normalized.biomes, tuple)
    assert normalized.biomes == ("forest", "plains")


def test_string_ecologies_normalize_to_tuple():
    """ecologies field normalizes to Tuple[str, ...] when given list of strings."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_ecology_tuple",
        module_type="ecology",
        display_name="Ecology Tuple Test",
        ecologies=["temperate", "arid"],
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)
    assert isinstance(normalized.ecologies, tuple)
    assert normalized.ecologies == ("temperate", "arid")


def test_string_populations_normalize_to_tuple():
    """populations field normalizes to Tuple[str, ...] when given list of strings."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_pop_tuple",
        module_type="population",
        display_name="Population Tuple Test",
        populations=["human_village", "orc_camp"],
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)
    assert isinstance(normalized.populations, tuple)
    assert normalized.populations == ("human_village", "orc_camp")


def test_string_relationships_normalize_to_tuple():
    """relationships field normalizes to Tuple[str, ...] when given list of strings."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_rel_tuple",
        module_type="ecology",
        display_name="Relationship Tuple Test",
        relationships=["allies", "enemies"],
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)
    assert isinstance(normalized.relationships, tuple)
    assert normalized.relationships == ("allies", "enemies")


def test_empty_ref_fields_normalize_to_empty_tuple():
    """All four ref fields produce empty tuples when the spec has no values."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_empty_refs",
        module_type="terrain",
        display_name="Empty Refs Test",
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)
    assert normalized.biomes == ()
    assert normalized.ecologies == ()
    assert normalized.populations == ()
    assert normalized.relationships == ()
    assert isinstance(normalized.biomes, tuple)
    assert isinstance(normalized.ecologies, tuple)
    assert isinstance(normalized.populations, tuple)
    assert isinstance(normalized.relationships, tuple)


def test_dict_with_id_biome_normalizes_to_id_string():
    """_normalize_ref_list converts a dict-with-id to its string ID."""
    from src.worldmodules.normalizer import _normalize_ref_list
    result = _normalize_ref_list([{"id": "forest_biome", "extra": "ignored"}], field_name="biomes")
    assert result == ("forest_biome",)
    assert isinstance(result, tuple)


def test_dict_without_id_biome_raises_normalization_error():
    """_normalize_ref_list raises NormalizationError for dict without 'id' key."""
    from src.worldmodules.normalizer import _normalize_ref_list, NormalizationError
    with pytest.raises(NormalizationError) as exc_info:
        _normalize_ref_list([{"name": "forest_biome"}], field_name="biomes")
    assert "biomes" in str(exc_info.value)
    assert "no valid 'id' key" in str(exc_info.value)


def test_duplicate_biome_ref_fails():
    """_normalize_ref_list raises NormalizationError for duplicate string IDs."""
    from src.worldmodules.normalizer import _normalize_ref_list, NormalizationError
    with pytest.raises(NormalizationError) as exc_info:
        _normalize_ref_list(["forest", "plains", "forest"], field_name="biomes")
    assert "forest" in str(exc_info.value)
    assert "biomes" in str(exc_info.value)


def test_normalizer_v1_and_v2_biomes_are_tuple():
    """Existing v1/v2 normalizer test extended: biomes/ecologies fields must be tuples."""
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer, NormalizedWorldModule
    v2_data = {
        "schema_version": "worldmodule.v2",
        "module_id": "v2_tuple_check",
        "module_type": "ecology",
        "display_name": "V2 Tuple Check",
        "biomes": ["biome_v2"],
        "ecologies": ["ecology_v2"],
    }
    v2_spec = WorldModuleSpec(**v2_data)
    normalized_v2 = WorldModuleAuthoringNormalizer.normalize(v2_spec)
    assert isinstance(normalized_v2.biomes, tuple)
    assert isinstance(normalized_v2.ecologies, tuple)
    assert normalized_v2.biomes[0] == "biome_v2"
    assert normalized_v2.ecologies[0] == "ecology_v2"

