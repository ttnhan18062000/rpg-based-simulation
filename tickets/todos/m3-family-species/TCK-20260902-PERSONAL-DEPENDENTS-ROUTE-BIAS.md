---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS
phase: open
date: 2026-09-02
tags: [lifecycle, adventure]
---

# TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS

## Title
Personal Dependents — new route-scoring bias term so entities with dependents avoid unnecessary risk

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Covers idea 31 (Personal Dependents & Responsibility) from `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md`. Investigation found the concern's own framing partly stale: `heir_entity_id`'s write-path already fires live today — `LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/lifecycle.py:21-111`) assigns a default heir automatically on death, landed by `TCK-20260824-DEFAULT-HEIR-ASSIGNMENT` (parity entry `SOC-245`, verified). The real unbuilt piece is the route-scoring half: a new bias term in `AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py:39-381`) so an entity with an active dependent measurably avoids inherently risky routes. The closest existing precedent is the escort-scoring block (§9, `SOC-230`, lines 357-368) which already biases `PROTECT_TARGET`/`OWN_SURVIVAL` scores based on `group.escort_target_id`. This ticket's full scope (birth-triggered parental dependents) is partially blocked on the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION) — only the non-parental dependent case (e.g. elder/veteran) is buildable standalone today; scope this ticket to that case and treat parental auto-registration as a follow-up once the Reproduction epic's birth-record schema lands.

## Scope
- A durable "dependent" concept on entity state: reuse or extend `heir_entity_id` (`src/core/state.py`, `LifecycleComponent`), or add a new typed field if Plan decides reuse conflates "dependent" with the distinct heir-inheritance concept too much — this is an explicit architecture decision for Plan, not assumed here. Cover at minimum the non-relative/non-parental case (e.g. elder/veteran dependent).
- A new bias term in `AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py`) such that an entity with an active dependent scores measurably lower on inherently risky route families (e.g. `HUNT_WEAK_ENEMY`) and/or higher on return/recovery-oriented routes than an otherwise-identical entity without a dependent — follow the escort-scoring block's (§9, lines 357-368) additive-bias shape as the closest precedent.
- A dedicated unit test asserting the score delta directly, following `tests/unit/domains/adventure/test_scoring_plan_bonus.py`'s pattern.
- Confirm `tests/architecture/test_adventure_route_score_max_unchanged.py` (which pins `_ADVENTURE_ROUTE_SCORE_MAX = 2.9`, a separate normalization constant in `intelligence.py`) still passes unmodified after the new bias term is added.

## Out of Scope
- Birth-triggered automatic dependent registration (a newborn child auto-registers as a dependent) — deferred until the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION) lands a birth record to register against. Document this explicitly as a known follow-up, not silently dropped.
- Marriage's spousal-protection hook (idea 33) — explicitly kept distinct per the atlas card; do not conflate with this ticket.
- Any change to the shared trust/escort-scoring logic (`SOC-230`) itself beyond adding a new, independent bias term alongside it.

## Acceptance Criteria
- [ ] A durable "dependent" concept exists on entity state (reused `heir_entity_id` or a new typed field, per Plan's decision), covering at minimum the non-parental case, with a defined write-path through `StateUpdate`/`EntityUpdate`.
- [ ] `AdventureRouteScorer.score()` gains a new bias term: an entity with an active dependent scores measurably lower on inherently risky route families and/or higher on return/recovery-oriented routes than an otherwise-identical entity without a dependent, all else equal.
- [ ] A dedicated unit test in `tests/unit/domains/adventure/` asserts the score delta directly, and `tests/architecture/test_adventure_route_score_max_unchanged.py` still passes unmodified.
- [ ] `docs/mechanics/05_world_evolution.md` and/or `docs/mechanics/04_strategic_cognition.md` documents the new mechanic; a new `docs/parity_ledger/social_narrative.yaml` entry (SOC-2xx) references it.
- [ ] Birth-triggered parental dependent auto-registration is explicitly documented as deferred/follow-up (not silently omitted), pending the Reproduction epic's birth-record schema.

## Related Tickets
- TCK-20260824-DEFAULT-HEIR-ASSIGNMENT (DONE — already gives `heir_entity_id_set` its live consumer; the atlas card's "never called by anything live" premise is stale relative to this)
- TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY (SOC-230 escort scoring — direct architectural precedent to reuse)
- TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5 (architecture guard relevant if scoring.py's formula changes)
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION (future dependency for the parental-dependent follow-up, not a blocker for this ticket's own scope)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 31 card)
- docs/mechanics/05_world_evolution.md (Succession — Default Heir Assignment section)
- docs/parity_ledger/social_narrative.yaml (SOC-245, SOC-230)
- CLAUDE.md (Durable State Rule)

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/core/updates.py
- src/systems/lifecycle_systems/lifecycle.py
- src/domains/adventure/scoring.py
- src/core/models/social.py

## Assumptions / Open Questions
- Whether to reuse `heir_entity_id` loosely for "dependent" or add a genuinely new field is an open architecture decision for Plan — `heir_entity_id` is a single `Optional[int]`, while "dependent" per the atlas is plural/general (children, wards); reusing `SocialBond` as-is risks conflating dependents with any strong relationship.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
