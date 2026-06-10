from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


ALLOWED_INITIAL_CONDITION_CATEGORIES = frozenset({
    "region_pressure",
    "faction_activity",
    "resource_scarcity",
    "population_alertness",
    "territorial_intrusion",
    "trade_route_risk",
    "danger_level_override",
    "spawn_bias",
})


class SimulationScenarioDefinition(BaseModel):
    """
    Schema for simulation scenario setup.

    Scenarios select world composition, perspective, focus modules, and initial
    conditions. They do not define diagnostics, metrics, scorecards, telemetry,
    or post-run analysis.

    Optionally, a scenario may declare a `template_id` to opt into template-based
    structural validation (allowed initial conditions, required features, etc.).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., min_length=1)
    display_name: Optional[str] = None
    world_composition: str = Field(..., min_length=1)
    perspective: str = Field(..., min_length=1)
    focus_modules: List[str] = Field(default_factory=list)
    initial_conditions: Dict[str, Any] = Field(default_factory=dict)
    setup_tags: List[str] = Field(default_factory=list)
    template_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_initial_condition_keys(self) -> SimulationScenarioDefinition:
        unknown = set(self.initial_conditions) - ALLOWED_INITIAL_CONDITION_CATEGORIES
        if unknown:
            raise ValueError(
                f"Unknown initial_condition categories: {sorted(unknown)}. "
                f"Allowed: {sorted(ALLOWED_INITIAL_CONDITION_CATEGORIES)}"
            )
        return self

    @model_validator(mode="after")
    def validate_template_constraints(self) -> SimulationScenarioDefinition:
        if self.template_id is None:
            return self
        from src.scenarios.templates import get_scenario_template_registry
        registry = get_scenario_template_registry()
        error = registry.validate_scenario(
            self.template_id, frozenset(self.initial_conditions.keys())
        )
        if error:
            raise ValueError(f"[scenario={self.id!r}] Template validation failed: {error}")
        return self
