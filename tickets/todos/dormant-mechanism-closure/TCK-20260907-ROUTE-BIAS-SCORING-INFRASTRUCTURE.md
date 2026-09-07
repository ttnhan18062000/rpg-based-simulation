---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE
phase: open
date: 2026-09-07
tags: [architecture, simulation-quality]
---

# TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE

## Title
Build the real prerequisite infrastructure for route-bias scoring — wires DoctrineResolver, adds a tags field to AdventureRouteOption, adds a bias term to AdventureRouteScorer

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Split out of `TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL` on 2026-09-07 (itself split out
of `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`, Dormant Mechanism Closure epic child 1). That
ticket's own investigation found idea 57's (Living Legend) real revival scope is a **4-component
dead chain plus a missing data model**, not the 2-component gap originally assumed:

1. **`DoctrineResolver.resolve()`** (`src/domains/motivation/resolver.py`) has zero real (non-test)
   callers anywhere in `src/` — confirmed via grep. `motivation.doctrine` on every real entity is
   always the bare default `IdentityDoctrine(class_id=...)` with **empty**
   `preferred_route_tags`/`avoided_route_tags`.
2. **`MotivationBiasService.compute_bias_multiplier()`** (`src/domains/motivation/service.py`) has
   zero real callers anywhere in `src/`. Even if wired, it would compute a no-op multiplier (1.0)
   for every real entity today, since nothing populates the doctrine it reads from (item 1).
3. **`AdventureRouteOption` has no `tags` field of any kind** (`src/domains/adventure/schema.py`) —
   only `family: RouteFamily`. `compute_bias_multiplier()`'s expected tag vocabulary (`"melee"`,
   `"ranged"`, `"heavy_armor"`, `"spells"`, `"flee"`, `"scouting"`, `"stealth"`, `"intel"`,
   `"mana"` — confirmed via `DoctrineResolver.resolve()`'s own real per-class data) does not overlap
   with `RouteFamily`'s vocabulary (`"recover"`, `"gather_resource"`, `"buy_upgrade"`,
   `"scout_location"`, etc. — only a near-miss: `"scout_location"` vs. `"scouting"`).
4. **`AdventureRouteScorer.score()`**'s real, live, already-certified formula (`src/domains/
   adventure/scoring.py:333`: `final_score = urgency + benefit + personality_bias +
   plan_advance_bonus + memory_adjustment + confidence_bonus - risk_penalty - blocker_penalty`) has
   **no existing bias/multiplier term at all** — confirmed via direct read.

This ticket builds the real, shared prerequisite infrastructure that benefits **both** idea 57
(Living Legend) and the already-built Culture Drift bias overlay (`CulturalBiasApplicator.
compute_culture_delta()`, `src/domains/culture/applicator.py`, E62C) — neither can ever produce a
real effect without this infrastructure existing first, regardless of which specific signal
eventually flows through it.

## Scope
- Wire `DoctrineResolver.resolve()` to a real, live call site — confirm during Investigate whether
  this should happen once at entity construction (keyed by `class_id`) or be re-resolved
  dynamically; ground the decision in how `IdentityDoctrine`'s own fields are meant to be used
  (read `DoctrineResolver`'s own docstring/tests for its original design intent).
- Add a `tags` field to `AdventureRouteOption` (or an equivalent real mechanism) that can carry a
  real, populated set of tags per route option. Decide the real vocabulary: reuse
  `IdentityDoctrine`'s combat-style vocabulary, introduce a new route-specific vocabulary, or
  support both — ground this decision in what `AdventureRouteGenerator`'s real route-construction
  call sites can actually populate today, not an invented ideal.
- Add a real bias/multiplier term to `AdventureRouteScorer.score()`'s existing formula, sourced from
  `MotivationBiasService.compute_bias_multiplier()` fed by the new `tags` field and the entity's
  (now-real) `IdentityDoctrine`. This is a change to a live, already-certified scoring formula —
  treat it with the same care as any Mechanics Bible formula change (update
  `docs/mechanics/`/parity ledger if this formula is documented there; confirm during Investigate).
- Confirm the Culture Drift bias overlay's own live-reachability once this infrastructure exists —
  `compute_bias_multiplier(entity, tags, culture_values)` already accepts a `culture_values`
  parameter designed for `CulturalBiasApplicator`'s output; wiring the real call site should make
  this reachable as a side effect, but verify directly, don't assume.
- Add real tests proving `DoctrineResolver` output reaches a real scored route, and that a non-empty
  `tags`/doctrine combination produces a measurably different `final_score` than the empty-doctrine
  baseline (a real regression-catching assertion, not a tautology).
- Given this touches a live, already-certified scoring formula and multiple subsystem boundaries
  (motivation → adventure route generation → scoring), this ticket likely warrants an
  `architecture-reviewer` pass on the Plan before Implementation.

## Out of Scope
- Wiring `LegendFact` specifically into this infrastructure — that is
  `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`'s own scope, sequenced after this ticket.
  This ticket only builds the shared prerequisite; it does not need to produce a Living-Legend
  specific test.
- Reviving `PerceptionUpdatePhase` or wiring any `PerceptionModel` consumer — the investigation that
  split this ticket out found no real code anywhere reads `PerceptionModel` fields for route
  generation/scoring, and `compute_bias_multiplier()` does not require `PerceptionUpdatePhase`'s
  output at all (it takes `culture_values`/`tags` directly, not a perception snapshot) — confirm
  this finding still holds during Investigate, but do not assume `PerceptionUpdatePhase` needs
  reviving as part of this ticket unless Investigate finds real evidence otherwise.
- Rebuilding `CulturalBiasApplicator`/`IdentityDoctrine`/`AdventureRouteScorer` themselves — all
  confirmed correct and already shipped; this ticket only builds the missing connective wiring.

## Acceptance Criteria
- [ ] `DoctrineResolver.resolve()` has a real, live, non-test caller.
- [ ] `AdventureRouteOption` (or an equivalent real mechanism) carries a real, populated tag/doctrine
      signal for at least one real route-generation call site.
- [ ] `MotivationBiasService.compute_bias_multiplier()` has a real, live, non-test caller feeding
      `AdventureRouteScorer.score()`'s formula, confirmed via a test showing a non-default doctrine
      value producing a different `final_score` than the empty-doctrine baseline.
- [ ] The Culture Drift bias overlay's own live-reachability is confirmed (or explicitly disclosed
      as still gapped, with a real reason) once this infrastructure exists.
- [ ] Determinism confirmed: no unsorted iteration over any new per-tick aggregation feeds a durable
      structure's key/iteration order.
- [ ] If `AdventureRouteScorer.score()`'s formula is documented in `docs/mechanics/` or the parity
      ledger, both are updated to reflect the new bias term, per the Authoritative Mechanics Rule.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL` (`tickets/done/` — the investigation this
  was split out of; DONE with its own real deliverable being the investigation itself)
- `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING` (the sibling ticket that depends on this one landing
  first)
- `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` (`tickets/done/` — idea 56's own, structurally
  unrelated bridge; no code overlap expected)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/world/culture_drift_contract.md` (the Culture Drift bias overlay's own contract)

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/domains/motivation/resolver.py` (`DoctrineResolver`)
- `src/domains/motivation/service.py` (`MotivationBiasService.compute_bias_multiplier()`)
- `src/domains/adventure/schema.py` (`AdventureRouteOption`)
- `src/domains/adventure/scoring.py` (`AdventureRouteScorer.score()`)
- `src/domains/culture/applicator.py` (`CulturalBiasApplicator`, E62C)

## Assumptions / Open Questions
- The exact real vocabulary for the new `tags` field (reuse `IdentityDoctrine`'s combat-style
  vocabulary, a new route-specific one, or both) is not decided here — real design work for this
  ticket's own Investigate/Plan phases.
- Whether `DoctrineResolver.resolve()` should run once at construction or dynamically is not decided
  here.
- Whether this new formula term has any real performance-budget implications is not assessed here —
  confirm during Investigate against `docs/engine/performance_contract.md`.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
