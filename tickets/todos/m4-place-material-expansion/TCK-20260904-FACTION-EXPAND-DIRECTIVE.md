---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260904-FACTION-EXPAND-DIRECTIVE
phase: open
date: 2026-09-04
tags: [faction, grand-strategy]
---

# TCK-20260904-FACTION-EXPAND-DIRECTIVE

## Title
National EXPAND_TERRITORY faction directive (ideas 51+52)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Ideas 51 (EXPAND directive) + 52 (population-pressure wiring), consolidated per the epic doc's own confirmation that idea 52 is pure wiring on top of idea 51's directive, not a separate mechanism. Adds a 4th directive kind, EXPAND_TERRITORY, to `FactionDecisionPhase.execute()` (`src/engine/faction_decision.py`), mirroring the existing DEFEND_BORDER/TRADE_ROUTE/COMMISSION_QUEST if/elif pattern, invoked inside `AuthoritativeApplyPipeline.refine()` right after 'blacksmith' and before 'faction_awareness'. Deliberately narrows target resolution to today's state model (faction-less regions via `RegionState.owner_faction_id`) rather than blocking on idea 35 (City ownership, still design-only) or Camp/Nest-as-conquest-target (not yet landed).

## Scope
- Add `EXPAND_TERRITORY` as a new directive-kind constant in `src/engine/faction_constants.py` (alongside DEFEND_BORDER, TRADE_ROUTE, COMMISSION_QUEST) and a new branch in `FactionDecisionPhase.execute()` (`src/engine/faction_decision.py`) that emits it as a transient `FactionDirective`, matching the existing if/elif directive-emission pattern.
- Target resolution for EXPAND_TERRITORY is scoped narrowly to today's state model: target any faction-less region via the existing `RegionState.owner_faction_id` field (Optional[int] = None) — do NOT attempt City-ownership-aware or Camp/Nest-as-conquest-target resolution; state this narrowing explicitly as a deliberate scope decision in `plan.md`, not an oversight.
- Wire the population-pressure/cohort signal (`src/domains/demographics/cohort.py` — `compute_population_density`/`compute_regional_scarcity`) as the real trigger condition feeding `FactionDecisionPhase`'s EXPAND_TERRITORY branch, per idea 52's population-cohort-signal framing.
- Wire the resulting directive through to `CampService` as its final consumption point (population-cohort/pressure signal -> FactionDecisionPhase -> CampService), scoped as real multi-file integration across 3 phases, not a one-line hookup.
- Directives remain transient scratch (FAC-003 parity rule) — EXPAND_TERRITORY must NOT be persisted in `AuthoritativeState`/`StateUpdate`, matching the existing DEFEND_BORDER/TRADE_ROUTE/COMMISSION_QUEST pattern.
- Update `docs/parity_ledger/faction.yaml`'s FAC-003 entry to include the 4th directive kind, and extend its test_path (`tests/unit/domains/faction/test_faction_decision_phase.py`) accordingly.

## Out of Scope
- Camp/Nest as a conquest target for EXPAND_TERRITORY — deferred until `TCK-20260904-CAMP-NEST-CLASSIFICATION` and `TCK-20260904-CAMPSTATE-PLACE-BRIDGE` land.
- City-ownership-aware target resolution (idea 35) — idea 35 remains design-only/not-in-code even after idea 66 landed (idea 66's own closing ticket says idea 35 "retains its own ticket for implementation," which does not yet exist); this ticket must not block on it and must not silently attempt a partial implementation of it.
- The material-possession predicate itself (`TCK-20260904-MATERIAL-POSSESSION-PREDICATE`) — this ticket may consume it if available but does not implement it.

## Acceptance Criteria
- EXPAND_TERRITORY is added as a 4th directive constant and a new branch in `FactionDecisionPhase.execute()`, matching the existing DEFEND_BORDER/TRADE_ROUTE/COMMISSION_QUEST if/elif structure, invoked in the same pipeline position (after 'blacksmith', before 'faction_awareness' in `AuthoritativeApplyPipeline.refine()`).
- Target resolution uses only `RegionState.owner_faction_id` (faction-less regions) — no Camp/Nest or City-ownership-aware logic is added.
- A population-pressure/cohort signal from `src/domains/demographics/cohort.py` gates when EXPAND_TERRITORY is emitted, tested for both trigger and no-trigger cases.
- The directive reaches `CampService` as a real, tested integration point (not a stub), covering the 3-phase path: cohort/pressure signal -> FactionDecisionPhase -> CampService.
- EXPAND_TERRITORY directives are proven NOT persisted in `AuthoritativeState`/`StateUpdate` (transient-scratch test, matching FAC-003's existing verification approach).
- `docs/parity_ledger/faction.yaml`'s FAC-003 entry text/v2_evidence/test_path are updated to include EXPAND_TERRITORY.

## Related Tickets
- TCK-20260904-MATERIAL-POSSESSION-PREDICATE
- TCK-20260904-CAMP-NEST-CLASSIFICATION
- TCK-20260904-CAMPSTATE-PLACE-BRIDGE
- TCK-20260619-E53Ab-DECISION-PHASE

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md
- docs/brainstorm/rpg_feature_atlas.html (ideas 51, 52)
- docs/parity_ledger/faction.yaml (FAC-003)

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/engine/faction_decision.py (FactionDecisionPhase.execute)
- src/engine/faction_constants.py (DEFEND_BORDER, TRADE_ROUTE, COMMISSION_QUEST)
- src/engine/pipeline.py (AuthoritativeApplyPipeline.refine, faction_decision inline block)
- src/domains/demographics/cohort.py (compute_population_density, compute_regional_scarcity)
- src/world/camp.py (CampService, final consumption point)
- src/core/state.py (RegionState.owner_faction_id)
- tests/unit/domains/faction/test_faction_decision_phase.py

## Assumptions / Open Questions
- Recommended sequencing (soft): idea 52's population-pressure-driven expansion should ideally be informed by material possession per idea 52's own card — recommend `TCK-20260904-MATERIAL-POSSESSION-PREDICATE` land before/alongside this ticket, but it is not a hard blocker; this ticket can proceed with population-pressure-only gating if the predicate isn't ready.
- Idea 35 (City ownership) remains design-only after idea 66 landed, and no implementation ticket exists for it yet — this ticket deliberately narrows EXPAND_TERRITORY's target resolution to avoid blocking on it, a scope decision that must be stated explicitly, not discovered as a gap later.
- Idea 52's "pure wiring" framing is confirmed accurate by the atlas's own audit but still spans 3 real phases/files (population signal, FactionDecisionPhase, CampService) — must be scoped and tested as real multi-file integration, not treated as a one-line hookup.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled on completion.)
