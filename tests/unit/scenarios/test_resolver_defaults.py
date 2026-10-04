"""`ScenarioSetupResolver`'s default `compositions_dir` is the authoritative world root.

See `docs/architecture/world_repository_layout.md` §1. The module-count oracle below is what
makes a regression here detectable at all: none of the existing scenario tests assert a module
count, so a silent fallback to a 6-module copy of `frontier_living_world` would leave them green.
"""
from pathlib import Path

import yaml

from src.content.repository import CatalogRepository
from src.scenarios.resolver import ScenarioSetupResolver
from src.scenarios.schema import SimulationScenarioDefinition
from src.worldmodules.repository import WorldModuleRepository

FRONTIER_SOURCE = Path("data/worlds/frontier_living_world/world.yaml")


def _resolver() -> ScenarioSetupResolver:
    catalog = CatalogRepository("data/content")
    catalog.load_all()
    module_repo = WorldModuleRepository()
    module_repo.load_all()
    return ScenarioSetupResolver(catalog, module_repo)


def _authored_module_count() -> int:
    raw = yaml.safe_load(FRONTIER_SOURCE.read_text(encoding="utf-8"))
    return len(raw.get("module_refs") or raw.get("modules") or [])


def test_scenario_setup_resolver_default_compositions_dir_is_data_worlds():
    assert ScenarioSetupResolver._DEFAULT_COMPOSITIONS_DIR == Path("data/worlds")

    scenario = SimulationScenarioDefinition(
        id="default_dir_probe",
        world_composition="frontier_living_world",
        perspective="hero_guild_perspective",
    )
    composition = _resolver()._load_composition(scenario)

    expected = _authored_module_count()
    # `module_refs` is Field(default_factory=list), so an empty module list is schema-valid and a
    # parsed-count-vs-spec-count comparison can degrade to 0 == 0 — passing while testing nothing.
    assert expected > 0, f"{FRONTIER_SOURCE} declares no modules; the oracle would be vacuous."
    assert len(composition.module_refs) == expected
