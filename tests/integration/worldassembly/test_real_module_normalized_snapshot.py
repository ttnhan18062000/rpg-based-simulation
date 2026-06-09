import pytest
from src.worldmodules.repository import WorldModuleRepository
from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer

pytestmark = pytest.mark.worldassembly


@pytest.fixture(scope="module")
def normalized_frontier():
    repo = WorldModuleRepository()
    repo.load_all()
    spec = repo.get_module("frontier_village_core")
    assert spec is not None, "frontier_village_core not found in data/content/world_modules"
    return WorldModuleAuthoringNormalizer.normalize(spec)


def test_snapshot_module_identity(normalized_frontier):
    assert normalized_frontier.module_id == "frontier_village_core"
    assert normalized_frontier.module_type == "settlement"


def test_snapshot_biome_refs_are_nonempty_strings(normalized_frontier):
    refs = normalized_frontier.biome_refs
    assert isinstance(refs, tuple)
    assert len(refs) > 0
    for r in refs:
        assert isinstance(r, str) and r, f"biome_refs element not a non-empty string: {r!r}"
        assert not isinstance(r, dict), f"raw dict in biome_refs: {r!r}"


def test_snapshot_ecology_refs_are_strings(normalized_frontier):
    refs = normalized_frontier.ecology_refs
    assert isinstance(refs, tuple)
    assert len(refs) > 0
    for r in refs:
        assert isinstance(r, str) and r
        assert not isinstance(r, dict)


def test_snapshot_population_refs_are_strings(normalized_frontier):
    refs = normalized_frontier.population_refs
    assert isinstance(refs, tuple)
    assert len(refs) > 0
    for r in refs:
        assert isinstance(r, str) and r
        assert not isinstance(r, dict)


def test_snapshot_relationship_refs_are_strings(normalized_frontier):
    refs = normalized_frontier.relationship_refs
    assert isinstance(refs, tuple)
    for r in refs:
        assert isinstance(r, str) and r
        assert not isinstance(r, dict)


def test_snapshot_resources_is_str_int_dict(normalized_frontier):
    resources = normalized_frontier.resources
    assert isinstance(resources, dict)
    for k, v in resources.items():
        assert isinstance(k, str)
        assert isinstance(v, int)


def test_snapshot_buildings_is_str_int_dict(normalized_frontier):
    buildings = normalized_frontier.buildings
    assert isinstance(buildings, dict)
    assert len(buildings) > 0
    for k, v in buildings.items():
        assert isinstance(k, str)
        assert isinstance(v, int)
        assert v > 0


def test_snapshot_services_is_str_int_dict(normalized_frontier):
    services = normalized_frontier.services
    assert isinstance(services, dict)
    for k, v in services.items():
        assert isinstance(k, str)
        assert isinstance(v, int)


def test_snapshot_no_dict_in_any_refs_field(normalized_frontier):
    for field_name in ("biome_refs", "ecology_refs", "population_refs", "relationship_refs"):
        for element in getattr(normalized_frontier, field_name):
            assert not isinstance(element, dict), (
                f"Raw dict found in {field_name}: {element!r}"
            )


def test_snapshot_loaded_from_repository_not_synthetic(normalized_frontier):
    # Verify module_id matches exactly — proves data was loaded from real YAML, not constructed
    assert normalized_frontier.module_id == "frontier_village_core"
    assert normalized_frontier.schema_version is not None
    assert normalized_frontier.display_name != ""
