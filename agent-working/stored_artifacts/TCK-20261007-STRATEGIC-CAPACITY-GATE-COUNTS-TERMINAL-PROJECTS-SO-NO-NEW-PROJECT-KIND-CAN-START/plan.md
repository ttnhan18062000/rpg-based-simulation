---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START
artifact_type: plan
tags: [strategy, cognition, bug]
---

# Plan

1. Add one predicate for which projects count against `max_active_projects` (`is_live_project`, `live_projects`, `has_project_capacity` in `src/core/strategic.py`): ACTIVE and SUSPENDED.
2. Make every capacity check and trim read it: the gate (`intelligence.py`), `DetourSuggestionSystem.enforce_bandwidth`, `CapacityEnforcementPhase` (otherwise it would drop a new project for finished records with higher scores), `GuildNeedScorer` and `GuildAction.visit`. No trim touches a finished record.
3. Tests with a disabling control per site; measure before and after on one tree; divergence 2.77, Bible 04 section 4, parity STRAT-278.
4. Out of scope: hunger's target (designer, SURV-06), the downstream survival breaks (umbrella ticket), pruning finished records.
