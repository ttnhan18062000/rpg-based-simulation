"""
Scenario authoring templates — reusable structural constraints for common simulation setups.

Templates define allowed structure (required world features, perspective types,
initial condition keys, focus modules). They do not contain scripted behavior.

A scenario may declare a `template_id` to opt into template-based validation.
Without a template, the base SimulationScenarioDefinition schema applies.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ScenarioTemplateDefinition(BaseModel):
    """Structural constraints for a category of simulation scenario."""

    model_config = ConfigDict(frozen=True)

    id: str
    required_world_features: List[str] = Field(default_factory=list)
    required_perspective_types: List[str] = Field(default_factory=list)
    allowed_initial_conditions: FrozenSet[str] = Field(default_factory=frozenset)
    allowed_focus_modules: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Built-in templates
# ---------------------------------------------------------------------------

_TEMPLATES: Dict[str, ScenarioTemplateDefinition] = {}


def _register(t: ScenarioTemplateDefinition) -> None:
    _TEMPLATES[t.id] = t


_register(ScenarioTemplateDefinition(
    id="territorial_pressure",
    required_world_features=["faction_territory", "ecology_module"],
    required_perspective_types=["territorial"],
    allowed_initial_conditions=frozenset({
        "region_pressure", "faction_activity", "population_alertness", "territorial_intrusion",
    }),
    allowed_focus_modules=["territory_control", "faction_influence"],
))

_register(ScenarioTemplateDefinition(
    id="raider_conflict",
    required_world_features=["faction_territory", "combat_module"],
    required_perspective_types=["militant", "defensive"],
    allowed_initial_conditions=frozenset({
        "region_pressure", "faction_activity", "danger_level_override", "spawn_bias",
    }),
    allowed_focus_modules=["combat_resolution", "faction_influence", "raid_response"],
))

_register(ScenarioTemplateDefinition(
    id="trade_route_risk",
    required_world_features=["trade_route", "faction_territory"],
    required_perspective_types=["merchant", "defensive"],
    allowed_initial_conditions=frozenset({
        "trade_route_risk", "faction_activity", "danger_level_override",
    }),
    allowed_focus_modules=["trade_economics", "faction_influence", "route_security"],
))

_register(ScenarioTemplateDefinition(
    id="resource_recovery",
    required_world_features=["resource_node", "ecology_module"],
    required_perspective_types=["resource_seeker", "territorial"],
    allowed_initial_conditions=frozenset({
        "resource_scarcity", "region_pressure", "population_alertness",
    }),
    allowed_focus_modules=["resource_ecology", "harvesting_economics"],
))

_register(ScenarioTemplateDefinition(
    id="settlement_defense",
    required_world_features=["settlement", "faction_territory", "combat_module"],
    required_perspective_types=["defensive", "militant"],
    allowed_initial_conditions=frozenset({
        "region_pressure", "faction_activity", "danger_level_override",
        "population_alertness", "spawn_bias",
    }),
    allowed_focus_modules=["settlement_protection", "faction_influence", "combat_resolution"],
))

_register(ScenarioTemplateDefinition(
    id="cult_ritual_pressure",
    required_world_features=["ruins_ecology", "cult_faction"],
    required_perspective_types=["investigative", "defensive"],
    allowed_initial_conditions=frozenset({
        "region_pressure", "faction_activity", "danger_level_override",
    }),
    allowed_focus_modules=["cult_activity", "faction_influence"],
))

_register(ScenarioTemplateDefinition(
    id="undead_containment",
    required_world_features=["undead_ecology", "battlefield_terrain"],
    required_perspective_types=["defensive", "militant"],
    allowed_initial_conditions=frozenset({
        "region_pressure", "danger_level_override", "spawn_bias", "population_alertness",
    }),
    allowed_focus_modules=["undead_lifecycle", "combat_resolution", "faction_influence"],
))

_register(ScenarioTemplateDefinition(
    id="wildlife_intrusion",
    required_world_features=["wildlife_ecology", "ecology_module"],
    required_perspective_types=["territorial", "defensive"],
    allowed_initial_conditions=frozenset({
        "territorial_intrusion", "region_pressure", "population_alertness",
    }),
    allowed_focus_modules=["wildlife_behavior", "territory_control"],
))

_register(ScenarioTemplateDefinition(
    id="caravan_escort",
    required_world_features=["trade_route", "faction_territory"],
    required_perspective_types=["merchant", "defensive", "militant"],
    allowed_initial_conditions=frozenset({
        "trade_route_risk", "faction_activity", "danger_level_override", "spawn_bias",
    }),
    allowed_focus_modules=["trade_economics", "route_security", "combat_resolution"],
))

_register(ScenarioTemplateDefinition(
    id="mine_reopening",
    required_world_features=["resource_node", "faction_territory"],
    required_perspective_types=["resource_seeker", "defensive"],
    allowed_initial_conditions=frozenset({
        "resource_scarcity", "region_pressure", "faction_activity",
        "danger_level_override", "spawn_bias",
    }),
    allowed_focus_modules=["resource_ecology", "faction_influence", "territory_control"],
))


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class ScenarioTemplateRegistry:
    """Read-only access to built-in scenario templates."""

    def get(self, template_id: str) -> Optional[ScenarioTemplateDefinition]:
        return _TEMPLATES.get(template_id)

    def all_ids(self) -> List[str]:
        return list(_TEMPLATES.keys())

    def validate_scenario(
        self,
        template_id: str,
        initial_condition_keys: FrozenSet[str],
    ) -> Optional[str]:
        """Return an error string if the scenario violates the template, else None."""
        tmpl = self.get(template_id)
        if tmpl is None:
            return f"Template {template_id!r} not found in registry."
        illegal = initial_condition_keys - tmpl.allowed_initial_conditions
        if illegal:
            return (
                f"Template {template_id!r} does not allow initial_condition key(s): "
                f"{sorted(illegal)}. Allowed: {sorted(tmpl.allowed_initial_conditions)}"
            )
        return None


_default_registry: Optional[ScenarioTemplateRegistry] = None


def get_scenario_template_registry() -> ScenarioTemplateRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = ScenarioTemplateRegistry()
    return _default_registry
