---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260903-ECONOMIC-VACANCY-SIGNAL
phase: open
date: 2026-09-03
tags: [economy, lifecycle]
---

# TCK-20260903-ECONOMIC-VACANCY-SIGNAL

## Title
The Empty Chair — economic-vacancy signal on sole-occupant production role death

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Idea 64 — "The Empty Chair": emit a readable economic-vacancy signal when the sole occupant of a production-relevant role dies, so consuming economy systems can detect the gap. This is the real remaining half of idea 64 after heir-assignment split cleanly to TCK-20260824-DEFAULT-HEIR-ASSIGNMENT (idea 10, confirmed DONE, entirely resource/inheritance, no production overlap). Investigation found EntityRole (src/core/enums.py) has no unique/singular production role concept — production today is entity-agnostic (BlacksmithSystem: proximity+materials/gold only; TownResolutionSystem: BuildingState.functional driven by faction-level maintenance solvency, never entity occupancy) — so this ticket must first define what "occupies" a production role before a vacancy signal is meaningful, then emit and wire a typed EconomicVacancyEvent-equivalent through the authoritative apply path.

## Scope
- Define what constitutes a "sole occupant/holder of a defined production-relevant role" (Plan-phase design decision, not pre-decided).
- On that occupant's death (PP-33, lifecycle.py), commit a typed vacancy signal (EconomicVacancyEvent-equivalent, following EconomyHealthMonitor's SimulationEvent-based alert pattern) through the authoritative apply path, carrying vacated_role and a location identifier.
- Use region_id as the location identifier (interim substitute for the schema doc's location_place_id, which depends on unbuilt idea 66).
- Wire the signal to be readable by at least one consumer (PP-07 BlacksmithSystem or PP-20 TownResolutionSystem).
- Vacancy remains detectable (not auto-resolved) across ticks if unfilled.
- Regression test: single-production-entity town, entity killed, N ticks advanced, measurable production-throughput delta vs. same-seed control.

## Out of Scope
- Any apprenticeship/recovery/auto-refill mechanism (explicitly flagged as scope creep in docs/brainstorm/codex/2026-08-27-core-rpg-new-idea-portfolio.md Candidate J) — vacancy SIGNAL only.
- filled_by_entity_id resolution logic (apprentice promotion vs import vs stays-vacant) — explicitly open in the schema doc, not decided here.
- Personal resource/inheritance handling — already covered by TCK-20260824-DEFAULT-HEIR-ASSIGNMENT (confirmed DONE).
- location_place_id / idea 66 Place-model integration — use region_id instead.
- A new headcount-gap detector duplicating OccupationChangeGoalScorer (TCK-20260824-OCCUPATION-CHANGE-TRIGGER) — review during design, do not fork a second parallel detector.

## Acceptance Criteria
- [ ] The death (PP-33) of the sole occupant/holder of a defined production-relevant role commits a typed EconomicVacancyEvent-equivalent through the authoritative apply path, carrying vacated_role and the vacating entity/region_id.
- [ ] The emitted signal is actually readable by at least one consuming system (PP-07 or PP-20), proven by a test that reads it from state/events, not just constructs it in isolation.
- [ ] The vacancy remains detectable (not auto-resolved) if left unfilled across a subsequent tick.
- [ ] A regression scenario (single-production-entity town, entity killed, N ticks advanced) shows a measurable production-throughput delta vs. a same-seed control run.
- [ ] Plan phase produces an explicit, documented definition of what "occupies" a production-relevant role (EntityRole has none today) before implementation begins, recorded in plan.md.

## Related Tickets
- TCK-20260824-DEFAULT-HEIR-ASSIGNMENT
- TCK-20260824-OCCUPATION-CHANGE-TRIGGER

## Related Docs
- docs/audits/D19_domain_phase_inventory.md
- docs/brainstorm/rpg_expected_schemas.html
- docs/brainstorm/codex/2026-08-27-core-rpg-new-idea-portfolio.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/lifecycle_systems/lifecycle.py
- src/engine/blacksmith.py
- src/engine/town_resolution.py
- src/ai/goals/occupation_change_scorer.py
- src/economy/health_monitor.py
- src/core/enums.py
- tests/unit/economy/test_economy_health_monitor.py
- tests/unit/economy/test_economy_alerts.py
- tests/unit/strategic/test_occupation_change_scorer.py
- tests/integration/strategic/test_occupation_change_reachability.py
- tests/unit/progression/test_lifecycle.py

## Assumptions / Open Questions
- What counts as an "occupied production role" is undefined in the current codebase (no unique/singular production role on EntityRole) — a real Plan-phase design decision, bigger than "add one event class"; must not be silently resolved.
- location_place_id depends on unbuilt idea 66's Place model — confirm idea 66's landing status, or proceed with region_id as the recommended interim substitute.
- filled_by_entity_id resolution strategy is an explicitly open design question in docs/brainstorm/rpg_expected_schemas.html, not decided by this ticket.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
