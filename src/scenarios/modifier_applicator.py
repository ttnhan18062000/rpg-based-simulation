from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.scenarios.resolver import StateSetupModifier
from src.scenarios.schema import ALLOWED_INITIAL_CONDITION_CATEGORIES


class UnsupportedModifierError(ValueError):
    """Raised when a StateSetupModifier has a modifier_type not in the supported set."""


class ScenarioSetupContext(BaseModel):
    """
    Typed record of deterministic initial-state effects produced by applying
    StateSetupModifiers before the first simulation tick.

    Fields are overlays/hints that the runtime reads at initialization; no
    entity behavioral actions are embedded here.
    """

    model_config = ConfigDict(frozen=True)

    # region_pressure modifier: trauma/hazard pressure per region (or "global")
    region_pressure_overrides: Dict[str, float] = Field(default_factory=dict)

    # faction_activity modifier: alertness level per faction_id (or "all")
    faction_alertness_levels: Dict[str, str] = Field(default_factory=dict)

    # resource_scarcity modifier: scarcity factor per resource type (or "all")
    resource_scarcity_factors: Dict[str, float] = Field(default_factory=dict)

    # population_alertness modifier: readiness hint per role/faction (or "all")
    population_readiness_hints: Dict[str, float] = Field(default_factory=dict)

    # territorial_intrusion modifier: faction-in-region intrusion claims
    territorial_intrusion_claims: List[Dict[str, Any]] = Field(default_factory=list)

    # trade_route_risk modifier
    trade_route_risk_level: Optional[float] = None

    # danger_level_override modifier
    danger_level_override: Optional[float] = None

    # spawn_bias modifier
    spawn_bias_config: Optional[Any] = None


class ModifierApplicator:
    """
    Applies a list of StateSetupModifiers to produce a ScenarioSetupContext.

    Application is deterministic: same modifier list always produces the same
    context. Unsupported modifier_type values raise UnsupportedModifierError
    immediately — no silent skipping.
    """

    SUPPORTED_TYPES: frozenset = ALLOWED_INITIAL_CONDITION_CATEGORIES

    def apply(self, modifiers: List[StateSetupModifier]) -> ScenarioSetupContext:
        region_pressure: Dict[str, float] = {}
        faction_alertness: Dict[str, str] = {}
        resource_scarcity: Dict[str, float] = {}
        population_readiness: Dict[str, float] = {}
        intrusion_claims: List[Dict[str, Any]] = []
        trade_route_risk: Optional[float] = None
        danger_override: Optional[float] = None
        spawn_bias: Optional[Any] = None

        # Process in sorted order for determinism across Python dict orderings
        for mod in sorted(modifiers, key=lambda m: m.modifier_type):
            t = mod.modifier_type
            v = mod.parameters.get("value")

            if t not in self.SUPPORTED_TYPES:
                raise UnsupportedModifierError(
                    f"Modifier type {t!r} is not supported. "
                    f"Supported types: {sorted(self.SUPPORTED_TYPES)}"
                )

            if t == "region_pressure":
                region_pressure["global"] = float(v)

            elif t == "faction_activity":
                faction_alertness["all"] = str(v)

            elif t == "resource_scarcity":
                resource_scarcity["all"] = float(v)

            elif t == "population_alertness":
                population_readiness["all"] = float(v)

            elif t == "territorial_intrusion":
                intrusion_claims.append({"claim": v})

            elif t == "trade_route_risk":
                trade_route_risk = float(v)

            elif t == "danger_level_override":
                danger_override = float(v)

            elif t == "spawn_bias":
                spawn_bias = v

        return ScenarioSetupContext(
            region_pressure_overrides=region_pressure,
            faction_alertness_levels=faction_alertness,
            resource_scarcity_factors=resource_scarcity,
            population_readiness_hints=population_readiness,
            territorial_intrusion_claims=intrusion_claims,
            trade_route_risk_level=trade_route_risk,
            danger_level_override=danger_override,
            spawn_bias_config=spawn_bias,
        )
