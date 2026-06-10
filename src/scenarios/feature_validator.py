"""
ScenarioWorldFeatureValidator — validates a scenario's feature requirements against
the features declared by its world composition.

Checks performed:
  1. Each required_world_feature in the scenario template is present in
     composition.provided_features (if composition declares any features).
  2. Each scenario.focus_modules entry corresponds to an enabled module in
     composition.module_refs.
  3. scenario.perspective is in composition.default_perspectives
     (when the composition declares perspectives).

All checks are deterministic for the same inputs.
Validation never modifies the composition or scenario.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from src.scenarios.schema import SimulationScenarioDefinition
from src.worldassembly.schema import WorldCompositionSpec


class ValidationResult(BaseModel):
    """Result of a world-feature validation pass."""

    model_config = ConfigDict(frozen=True)

    ok: bool
    errors: List[str]
    scenario_id: str


class ScenarioWorldFeatureValidator:
    """Read-only validator: checks scenario requirements against composition outputs."""

    def validate(
        self,
        scenario: SimulationScenarioDefinition,
        composition: WorldCompositionSpec,
    ) -> ValidationResult:
        errors: List[str] = []

        # Collect enabled module IDs from the composition
        enabled_module_ids = {
            ref.module_id
            for ref in composition.module_refs
            if ref.enabled
        }

        # 1. Required world features (from template)
        if scenario.template_id is not None:
            from src.scenarios.templates import get_scenario_template_registry
            tmpl = get_scenario_template_registry().get(scenario.template_id)
            if tmpl is not None and composition.provided_features:
                missing_features = [
                    f for f in tmpl.required_world_features
                    if f not in composition.provided_features
                ]
                for f in missing_features:
                    errors.append(
                        f"[scenario={scenario.id!r}] Required world feature {f!r} "
                        f"is not provided by composition {composition.world_id!r}. "
                        f"Available: {sorted(composition.provided_features)}"
                    )

        # 2. Focus modules present in composition
        for mod in scenario.focus_modules:
            if enabled_module_ids and mod not in enabled_module_ids:
                errors.append(
                    f"[scenario={scenario.id!r}] Focus module {mod!r} is not an enabled "
                    f"module in composition {composition.world_id!r}. "
                    f"Enabled modules: {sorted(enabled_module_ids)}"
                )

        # 3. Perspective present in composition
        if composition.default_perspectives and scenario.perspective not in composition.default_perspectives:
            errors.append(
                f"[scenario={scenario.id!r}] Perspective {scenario.perspective!r} is not in "
                f"composition {composition.world_id!r} default_perspectives. "
                f"Available: {composition.default_perspectives}"
            )

        return ValidationResult(ok=len(errors) == 0, errors=errors, scenario_id=scenario.id)
