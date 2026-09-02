---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE
phase: open
date: 2026-09-02
tags: [lifecycle, strategy]
---

# TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE

## Title
Coming of Age — weighted archetype-choice roll at CHILD to ADULT transition, with a required convergence-guard metamorphic test

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Covers idea 34 (Coming of Age) from `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md`. Both M1 prerequisites are DONE: `TCK-20260824-LIFE-STAGE-TRANSITIONS` (idea 20) gives the CHILD→ADULT transition trigger inside `LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/lifecycle.py`), and `TCK-20260824-OCCUPATION-CHANGE-TRIGGER` (idea 21) gives the first live `role_set` producer (`src/ai/goals/occupation_change_scorer.py`). The remaining unbuilt piece is a genuinely new weighted archetype-choice mechanism (personality + parental occupation + regional-need weighting) with zero existing numeric precedent — the closest analog, `PersonalityService.get_goal_modifiers()` (`src/ai/personality.py`), governs goal-utility, not occupation selection. CRITICAL RISK: today's only real occupation-selection precedent, `OccupationChangeGoalScorer` (`src/ai/goals/occupation_change_scorer.py`), is fully deterministic and zero-variance by construction (fixed-priority first-fit: `_CANDIDATE_ROLES = (SHOPKEEPER, WORKER, GUARD)`, first role passing an open-slot check plus a flat `attribute >= 5` threshold wins, no weighting or randomness). If this ticket naively reuses that pattern, it will reproduce the exact convergence bug the design proposal itself names — a metamorphic test proving that increasing the regional-need weight increases (not collapses) outcome variance is a required acceptance gate, not optional coverage. Has a hard dependency on the Reproduction epic's birth-record schema (TCK-20260902-EPIC-RPG-M3-REPRODUCTION / TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA) for one acceptance criterion (the no-birth-record hard exclusion) — that criterion is BLOCKED until the epic's schema child ticket lands; do not silently skip it, mark it explicitly deferred.

## Scope
- When an entity's `identity.life_stage` transitions CHILD→ADULT inside `LifecycleSystem.resolve_lifecycle()` (the same call site/tick-phase as the existing `life_stage_set` trigger, per the atlas's cross-reference note that idea 34 must fire in the same phase window as idea 20's transition), fire a Coming of Age archetype-choice roll exactly once for that entity.
- The roll produces exactly one `IdentityUpdate` (via the authoritative `IdentityPatch`/`role_set` path, not direct state mutation) assigning an occupation/archetype.
- Design a genuinely weighted (not fixed-priority, not deterministic) selection mechanism combining personality traits, parental occupation, and regional-need signals — the exact weighting formula (e.g. softmax over weighted scores vs. weighted-random draw) is a fresh Plan-phase design decision; do not copy `OccupationChangeGoalScorer`'s fixed-priority-first-fit pattern, since doing so would collapse variance to zero by construction.
- A required metamorphic test: holding personality and parental-occupation weight terms fixed, increasing the regional-need weight coefficient must strictly increase the variance/entropy of the resulting occupation distribution across a same-tick batch of same-region children reaching adulthood — never collapse it to a single occupation.
- A regression guard: a batch of N children in the same region under the same regional shortage, all transitioning CHILD→ADULT in the same tick, must not all resolve to the identical occupation role when regional-need weight is nonzero.
- The no-birth-record hard boolean exclusion (Coming of Age does not fire for an entity with no birth record) is explicitly BLOCKED pending the Reproduction epic's birth-record schema landing — implement the eligibility check as a stub/TODO with this dependency documented, or defer this specific AC to a fast-follow ticket once the schema exists; do not silently omit it from the ticket's tracking.

## Out of Scope
- Any change to `OccupationChangeGoalScorer`'s existing deterministic regional-need/target_count logic — this ticket may read its `BASE_OCCUPATION_DENSITY`/target_count constants (`src/world/occupation_config.py`) for regional-need signal input, but must not modify that scorer's own selection behavior.
- The Reproduction epic itself (idea 32) — a separate epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION); this ticket only consumes its birth-record schema once available.
- Long-run corpus-tier population-pressure convergence (idea 38's separate claim) — the metamorphic AC here is scoped to a bounded single-tick synthetic batch, not the long-run corpus property.

## Acceptance Criteria
- [ ] When `identity.life_stage` transitions CHILD→ADULT inside `LifecycleSystem.resolve_lifecycle()`, a Coming of Age roll fires exactly once and commits exactly one `IdentityUpdate` through the authoritative `IdentityPatch`/`role_set` path.
- [ ] A metamorphic test asserts: holding personality and parental-occupation weight terms fixed, increasing the regional-need weight coefficient strictly increases the variance/entropy of the resulting occupation distribution across a same-tick batch of same-region children reaching adulthood.
- [ ] A batch of N children in the same region under the same regional shortage, transitioning CHILD→ADULT in the same tick, do not all resolve to the identical occupation role when regional-need weight is nonzero (direct regression guard).
- [ ] The no-birth-record hard exclusion is explicitly tracked as BLOCKED pending TCK-20260902-EPIC-RPG-M3-REPRODUCTION, not silently omitted from this ticket's Acceptance Criteria or Completion Summary.
- [ ] New unit tests added following `tests/unit/strategic/test_occupation_change_scorer.py` and `tests/unit/strategic/test_life_stage_transitions.py`'s conventions; the metamorphic/convergence test is a genuinely new test class (none exists today for weighted/stochastic archetype selection).
- [ ] `docs/mechanics/04_strategic_cognition.md` documents the weighting mechanism and the convergence-risk guard; a `docs/parity_ledger/` entry references it.

## Related Tickets
- TCK-20260824-LIFE-STAGE-TRANSITIONS (DONE — idea 20, the life-stage write path this concern co-locates with)
- TCK-20260824-OCCUPATION-CHANGE-TRIGGER (DONE — idea 21, the first live `role_set` producer this extends)
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION / TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA (hard dependency for the no-birth-record exclusion AC — BLOCKED until this lands)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md (build-order item 4 of 5, explicit metamorphic-check acceptance gate)
- docs/brainstorm/rpg_feature_atlas.html (idea 34 card)
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/lifecycle_systems/lifecycle.py
- src/ai/life_stage.py
- src/ai/goals/occupation_change_scorer.py
- src/world/occupation_config.py
- src/ai/personality.py
- src/core/state.py
- src/core/updates.py

## Assumptions / Open Questions
- The weighting-mechanism design (softmax vs. weighted-random draw, etc.) has no existing precedent and is a fresh Plan-phase decision.
- Whether to call `OccupationChangeGoalScorer`'s regional-count logic directly or duplicate/extend `BASE_OCCUPATION_DENSITY` is an open design question — duplicating risks drift between the two systems.
- The no-birth-record exclusion AC is untestable until the Reproduction epic's schema lands; Plan should decide whether to stub it now or split it into a fast-follow ticket once that schema exists.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
