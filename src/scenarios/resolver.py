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
        comp_path = self._compositions_dir / f"{scenario.world_composition}.yaml"
        if not comp_path.is_file():
            raise ValueError(
                f"[scenario={scenario.id!r}] World composition {scenario.world_composition!r} "
                f"not found at {comp_path}"
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
