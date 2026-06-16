# Compliance IDs: TCK-20260614-WORLDMOD-UNIFY anti-drift guards
# Verifies that count-map resources and buildings are assembled into WorldSpec
# via the unified unconditional path (no schema_version branching).
import ast
import inspect

import pytest

import src.worldassembly.resolver as resolver_module
from src.content.repository import CatalogRepository
from src.worldassembly.resolver import WorldAssemblyResolver
from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
from src.worldmodules.repository import WorldModuleRepository

pytestmark = pytest.mark.worldassembly


@pytest.fixture(scope="module")
def repos():
    cat = CatalogRepository("data/content")
    cat.load_all()
    mod = WorldModuleRepository()
    mod.load_all()
    return cat, mod


def test_modules_with_count_map_resources_assemble_into_contribution(repos):
    """NT-5: forest_warden_grove count-map resources appear in the resolved contribution."""
    cat, mod = repos
    resolver = WorldAssemblyResolver(cat, mod)
    spec = mod.get_module("forest_warden_grove")
    assert spec is not None
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)

    contribution = resolver.resolve_module_contribution(normalized)

    assert "healing_flower_patch" in contribution.resource_refs
    assert "spirit_wisp" in contribution.resource_refs
    assert contribution.resource_refs["healing_flower_patch"] == 5
    assert contribution.resource_refs["spirit_wisp"] == 2


def test_modules_with_count_map_buildings_assemble_into_contribution(repos):
    """NT-6: frontier_village_core buildings appear in the resolved contribution."""
    cat, mod = repos
    resolver = WorldAssemblyResolver(cat, mod)
    spec = mod.get_module("frontier_village_core")
    assert spec is not None
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)

    contribution = resolver.resolve_module_contribution(normalized)

    assert "town_hall" in contribution.building_refs
    assert "shop" in contribution.building_refs
    assert "blacksmith" in contribution.building_refs
    assert "inn" in contribution.building_refs
    assert "healer_hut" in contribution.building_refs


def test_heuristic_region_methods_are_removed():
    """NT-7 / Guard 5: Both heuristic placement methods must be absent from WorldAssemblyResolver."""
    assert not hasattr(WorldAssemblyResolver, "_find_best_region_for_resource"), (
        "_find_best_region_for_resource must be removed (replaced by spawn_region='')"
    )
    assert not hasattr(WorldAssemblyResolver, "_find_best_region_for_building"), (
        "_find_best_region_for_building must be removed (replaced by spawn_region='')"
    )


def test_resolver_has_no_schema_version_branching():
    """Guard 1: AST walk of resolver source confirms no 'worldmodule.v' string in Compare nodes."""
    source = inspect.getsource(resolver_module)
    tree = ast.parse(source)

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.startswith("worldmodule.v"):
                violations.append(node.value)

    assert not violations, (
        f"Found schema_version branch constants in resolver.py: {violations!r}. "
        "All worldmodule.v* branching must be removed."
    )
