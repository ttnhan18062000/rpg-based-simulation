from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field

from src.content.repository import CatalogRepository
from src.worldassembly.resolver import ResolvedWorldBundle, WorldAssemblyResolver
from src.worldassembly.schema import WorldCompositionSpec
from src.worldmodules.repository import WorldModuleRepository
from src.scenarios.schema import SimulationScenarioDefinition


class StateSetupModifier(BaseModel):
    model_config = ConfigDict(frozen=True)

    modifier_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ResolvedScenarioSetup(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    scenario_id: str
    world_bundle: ResolvedWorldBundle
    perspective_id: str
    initial_relation_context: Dict[str, Any] = Field(default_factory=dict)
    initial_state_modifiers: List[StateSetupModifier] = Field(default_factory=list)


class ScenarioSetupResolver:
    _DEFAULT_COMPOSITIONS_DIR = Path("data/content/world_compositions")

    def __init__(
        self,
        catalog: CatalogRepository,
        module_repo: WorldModuleRepository,
        compositions_dir: Optional[Path] = None,
    ) -> None:
        self._assembly_resolver = WorldAssemblyResolver(catalog, module_repo)
        self._compositions_dir = compositions_dir or self._DEFAULT_COMPOSITIONS_DIR

    def resolve(self, scenario: SimulationScenarioDefinition) -> ResolvedScenarioSetup:
        composition = self._load_composition(scenario)
        self._validate_perspective(scenario, composition)
        world_bundle = self._assembly_resolver.assemble(composition)
        modifiers = self._build_modifiers(scenario.initial_conditions)
        return ResolvedScenarioSetup(
            scenario_id=scenario.id,
            world_bundle=world_bundle,
            perspective_id=scenario.perspective,
            initial_relation_context={},
            initial_state_modifiers=modifiers,
        )

    def _load_composition(self, scenario: SimulationScenarioDefinition) -> WorldCompositionSpec:
        # TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING: two accepted layouts, tried in this
        # order. (1) The unified, ADR-correct per-world directory layout
        # (docs/architecture/world_repository_layout.md: "the existing unified world repository
        # root at data/worlds/... The root source file inside a world folder is always
        # world.yaml") -- `<compositions_dir>/<world_id>/world.yaml`. Tried first since it's the
        # canonical layout going forward. (2) The flat, single-file layout
        # `<compositions_dir>/<world_id>.yaml` -- this repo's existing default
        # `compositions_dir` (`data/content/world_compositions/`) only has this shape, so this
        # remains the fallback for every caller that hasn't opted into the per-world layout (i.e.
        # everyone except CampaignOrchestrator, which points compositions_dir at data/worlds/).
        # Nested-first is safe for existing callers: `data/content/world_compositions/<id>/`
        # never exists, so the check falls through to the flat file exactly as before.
        nested_path = self._compositions_dir / scenario.world_composition / "world.yaml"
        flat_path = self._compositions_dir / f"{scenario.world_composition}.yaml"
        if nested_path.is_file():
            comp_path = nested_path
        elif flat_path.is_file():
            comp_path = flat_path
        else:
            raise ValueError(
                f"[scenario={scenario.id!r}] World composition {scenario.world_composition!r} "
                f"not found at {nested_path} or {flat_path}"
            )
        with open(comp_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        try:
            return WorldCompositionSpec.model_validate(raw)
        except Exception as exc:
            raise ValueError(
                f"[scenario={scenario.id!r}] Failed to parse world composition "
                f"{scenario.world_composition!r}: {exc}"
            ) from exc

    def _validate_perspective(
        self,
        scenario: SimulationScenarioDefinition,
        composition: WorldCompositionSpec,
    ) -> None:
        allowed = composition.default_perspectives
        if allowed and scenario.perspective not in allowed:
            raise ValueError(
                f"[scenario={scenario.id!r}] Perspective {scenario.perspective!r} is not valid "
                f"for composition {scenario.world_composition!r}. Allowed: {allowed}"
            )

    def _build_modifiers(self, initial_conditions: Dict[str, Any]) -> List[StateSetupModifier]:
        return [
            StateSetupModifier(modifier_type=key, parameters={"value": value})
            for key, value in initial_conditions.items()
        ]
