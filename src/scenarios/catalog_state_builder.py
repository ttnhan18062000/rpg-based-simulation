from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.certification.models import ScenarioExpectations
from src.content.repository import CatalogRepository
from src.core.state import AuthoritativeState
from src.scenarios.resolver import ResolvedScenarioSetup, ScenarioSetupResolver
from src.scenarios.schema import SimulationScenarioDefinition
from src.worldassembly.entity_spawner import WorldEntitySpawner
from src.worldmodules.repository import WorldModuleRepository


@dataclass(frozen=True)
class CatalogScenarioBuildResult:
    """Result of CatalogScenarioStateBuilder.build()."""

    state: AuthoritativeState
    setup: ResolvedScenarioSetup
    expectations: ScenarioExpectations


class CatalogScenarioStateBuilder:
    """
    Builds AuthoritativeState from catalog archetypes and population recipes.

    Pipeline:
        SimulationScenarioDefinition
        → ScenarioSetupResolver (composition → module contributions → world bundle)
        → WorldEntitySpawner (CompileContext → Dict[int, EntityState] via ArchetypeEntityFactory)
        → AuthoritativeState(tick=0, seed=seed, entities=...)

    This is the catalog-native construction path. It does not replace the legacy
    build_scenario_state() / ArenaInjector path — it exists beside it.
    """

    def __init__(
        self,
        catalog: CatalogRepository,
        module_repo: WorldModuleRepository,
        compositions_dir: Optional[Path] = None,
    ) -> None:
        self._catalog = catalog
        self._resolver = ScenarioSetupResolver(catalog, module_repo, compositions_dir)
        self._spawner = WorldEntitySpawner()

    def build(
        self,
        scenario: SimulationScenarioDefinition,
        *,
        seed: int = 42,
    ) -> CatalogScenarioBuildResult:
        """
        Build an AuthoritativeState from the given scenario definition.

        Returns CatalogScenarioBuildResult with:
          - state: AuthoritativeState at tick=0
          - setup: ResolvedScenarioSetup (world_bundle, perspective_id, modifiers)
          - expectations: ScenarioExpectations (default, suitable for smoke tests)
        """
        setup = self._resolver.resolve(scenario)
        entities = self._spawner.spawn_from_context(
            setup.world_bundle.compile_context,
            self._catalog,
            seed=seed,
        )
        state = AuthoritativeState(tick=0, seed=seed, entities=entities)
        return CatalogScenarioBuildResult(
            state=state,
            setup=setup,
            expectations=ScenarioExpectations(),
        )
