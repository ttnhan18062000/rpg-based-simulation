---
status: active
layer: compliance
authority: P1
audience: developer
---

# Logic Gap Analysis (V2 Engine)

This document tracks technical debt where the documented "Authoritative Laws" or "Compliance Checklist" diverge from the current `src/` implementation.

## [RESOLVED] 1. Actor Validity Loopholes
- **Implemented**: `status_sleeping` check and explicit `CombatUpdate` rejection for incapacitated actors.
- **Impact**: Actors in non-operable states (Dead, Sleeping, Stunned, Frozen) are now correctly stripped of all proposed intents (Movement, Task, Interaction, Combat).
- **Location**: `src/engine/pipeline_phases/actor_validity.py`

## [RESOLVED] 2. Strategic Hardcoding
- **Implemented**: Refactored the hardcoded "Interruption Resistance" multiplier into a `CognitionProfile` parameter.
- **Impact**: Strategic tenacity can now be tuned per-actor or per-class via the `resistance_multiplier` field.
- **Location**: `src/systems/strategic_systems/intelligence.py`

## [RESOLVED] 3. World Evolution Gaps
- **Implemented**: Regional Sovereignty transitions. Death events now shift regional influence between factions.
- **Impact**: Regions can now be "claimed" by the Hero Guild or Monster Horde when influence thresholds (+100/-100) are met.
- **Location**: `src/engine/world_dynamics.py`
