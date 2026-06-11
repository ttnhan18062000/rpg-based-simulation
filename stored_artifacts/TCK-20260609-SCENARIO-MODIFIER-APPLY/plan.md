---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260609-SCENARIO-MODIFIER-APPLY
artifact_type: plan
tags: [scenario, modifier, apply]
---


# Plan

## New files
- `src/scenarios/modifier_applicator.py`
- `tests/unit/scenarios/test_scenario_modifier_apply.py`

## `ScenarioSetupContext` (frozen Pydantic)
Fields: region_pressure_overrides, faction_alertness_levels, resource_scarcity_factors,
population_readiness_hints, territorial_intrusion_claims, trade_route_risk_level,
danger_level_override, spawn_bias_config.

## `ModifierApplicator`
- `SUPPORTED_TYPES = ALLOWED_INITIAL_CONDITION_CATEGORIES`
- `apply(modifiers)`: sorts by modifier_type for determinism, dispatches each type,
  raises `UnsupportedModifierError` for unknown types, returns `ScenarioSetupContext`

## Tests
One test per modifier type + empty list + unsupported type (error, not skip) + determinism +
frozen check + no catalog/repo imports.
