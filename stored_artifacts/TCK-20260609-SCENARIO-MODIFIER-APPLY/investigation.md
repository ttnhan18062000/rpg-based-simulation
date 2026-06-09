---
ticket: TCK-20260609-SCENARIO-MODIFIER-APPLY
phase: investigation
---

# Investigation

## Domain context (Chapter 5: World Evolution)
- `region_pressure` → trauma score / hazard level overlay
- `population_alertness` → readiness hint (entities lose readiness under suppression)
- `faction_activity` → alertness level signal (no direct entity commands)
- `resource_scarcity` → scarcity factor on resource counts
- `territorial_intrusion` → faction-in-region sovereignty claim
- `trade_route_risk`, `danger_level_override`, `spawn_bias` → numeric/config overlays

## No live state object exists at setup time
The simulation runtime doesn't expose a pre-tick mutable world state object. The applicator
therefore produces a `ScenarioSetupContext` overlay — a typed record the runtime reads at init.
This is consistent with the ticket's constraint: "testable without running a full simulation tick."

## Allowed types come from ALLOWED_INITIAL_CONDITION_CATEGORIES
Reused directly as `SUPPORTED_TYPES` to avoid duplication.
