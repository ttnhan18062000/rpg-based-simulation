---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO
phase: done
date: 2026-09-07
tags: [testing, simulation-quality, corpus]
---

# TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO

## Title
Author a real corpus scenario exercising route_new_query's Branch 3 information-routing trigger

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) child 3 of 6.
`route_new_query`'s SimQ signal rule (added during M7's pillar-integration pass,
`src/simulation_quality/scorers/information.py`) has never fired in any shipped calibration corpus,
confirmed still true 2026-09-07 (M9's own `route_new_query_isolated_calibration.py` proved the rule
correctly produces a 0.0→10.0 score delta via an isolated `QualityHub` replay, but no real corpus
world exercises it end-to-end). The real trigger (`src/domains/information/phase.py:86-104`, "Branch
3" of `InformationPhase.apply()`) fires when an entity has unresolved informational "unknowns" with
no higher-priority branch (1/2) already satisfied — this rule postdates M9's own scoping pass, so
it's a genuinely new gap M9 could not have caught, not something it missed.

## Scope
- Confirm the exact real conditions for Branch 1/2 to NOT already satisfy an entity (so Branch 3
  genuinely fires) during Investigate — read `InformationPhase.apply()`'s full branch logic, not just
  the Branch 3 comment.
- Author or extend a real corpus world/profile with at least one entity carrying a genuine unresolved
  "unknown" and no competing higher-priority route active, so `route_new_query` fires naturally during
  a real calibration run (not an isolated replay).
- Confirm the INFORMATION pillar produces a real, non-flat, attributable score change from this real
  corpus run, following the same evidentiary bar M9's own isolated-replay proof already established.

## Out of Scope
- Redesigning `InformationPhase`'s branch logic — confirm it's correct as-is, this ticket only proves
  a real scenario can reach Branch 3.
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [ ] A real corpus world/profile exercises `route_new_query` naturally during a normal calibration
      run (not an isolated replay).
- [ ] The INFORMATION pillar shows a real, non-flat score contribution from this run, confirmed and
      recorded.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES` (the ticket that added this rule)
- `TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS` (the ticket that proved it via isolated replay)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/simulation_quality/event_type_coverage.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/domains/information/phase.py`
- `src/observability/event_shapers.py`
- `config/simulation_quality/corpus_registry.yaml`

## Assumptions / Open Questions
- **Resolved**: a new, dedicated world was needed (see Implementation Notes) — none of the 3
  pre-existing unit-tier INFORMATION/COGNITION worlds combine both compile-time-seeded halves
  Branch 3 needs.
- **New finding, not anticipated by this ticket's own original text**: even with the right corpus
  content authored, Branch 3 still cannot fire — a structural, cross-phase timing gap, not a
  content gap. Split into `TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION` (real
  decision required, not this ticket's own job to make unilaterally).

## Implementation Notes

Investigated per Scope, then escalated once the real blocker turned out to be structural rather
than content-authoring:

1. **Confirmed the real Branch 3 preconditions** (`src/domains/information/phase.py:86-104`):
   `actor.self_model.knowledge.unknowns` non-empty AND a real `InformationQueryRouter.route()`
   candidate for `InformationQuery(kind="material_source")`. Neither Branch 1 nor Branch 2 needs to
   be literally absent — Branch 3 only requires `actor.id not in entity_updates` after Branch 2 ran
   (i.e. no pending-response assimilation happened for this actor this tick).
2. **Confirmed via direct code read** (`InformationQueryRouter.route()`,
   `src/domains/information/router.py`) that scope-matching is keyed on `query.kind` (hardcoded
   `"material_source"` by Branch 3) against `"common_resource_sources" in
   profile.knowledge_scopes` — not on the unknown's own subject string. A `town_notice_board`-style
   profile (byte-for-byte the same shape already shipped in `urban_political`/
   `unit_information_source`/`unit_information_density`) is a real, working candidate.
3. **Authored a new unit-tier corpus world**, `data/worlds/unit_information_routing_pilot/`
   (+ `config/simulation_quality/profiles/unit_information_routing_pilot.yaml`,
   `ENABLE_SELF_MODEL_COGNITION`+`ENABLE_BELIEF_ASSIMILATION` both ON), combining one
   `pending_self_model_information_events` entry (unknown about `material.wood.source`, targeting
   `pop_1`) with one `information_source_profiles` entry (`town_notice_board`,
   `knowledge_scopes=["common_resource_sources"]`) — the exact combination none of
   `unit_selfmodel_pilot` (seeds the unknown, deliberately omits profiles — its own explicit scope
   guard from `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`), `unit_information_source`, or
   `unit_information_density` (both seed profiles + `pending_information_responses`, but leave
   `pending_self_model_information_events` empty) provide. Resolved/validated cleanly via
   `python3 -m src.worldbuilding.cli resolve/validate`.
4. **Ran real calibration** (`tools/calibrate_simq.py --name unit_information_routing_pilot --seed
   42 --ticks 200`) — INFORMATION stayed flat `grade=C events=0`, same as the pre-existing baseline.
   Not a content gap: direct debugging (a standalone script driving a real
   `WorldCompiler.compile()` + `Kernel.tick_once()` loop) confirmed the entity's unknown *is*
   correctly materialized from tick 1 onward, and `state.information_source_profiles` *is* present
   in the compiled state — but never simultaneously with the entity's own unknowns being visible to
   `InformationBeliefPhase.apply()` within the same tick.
5. **Root-caused the real structural gap**: `information_source_profiles` is intentionally,
   verifiably Bounded/single-fire (`docs/guidelines/design_patterns.md` Pattern 6's own "known
   pitfall" section — only present during the tick-1 `apply_generation()` call), while
   `self_model.knowledge.unknowns` only becomes visible to `InformationBeliefPhase.apply()`
   starting tick 2 (same-tick phase outputs aren't visible to later same-tick phases in this
   engine's `refine()` sequence — a general, correct pipeline convention, not specific to this
   case). The two conditions Branch 3 needs are therefore **never simultaneously true**, for any
   corpus content whatsoever — a structural gap between two independently-correct design decisions,
   not something a `world.yaml` can ever bridge.
6. **This investigation also directly led to `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-
   CARRYFORWARD`**: while tracing `apply_generation()`'s own field-carry-forward behavior to
   understand point 5 above, found (and, per the orchestrating session's ratified decision, fixed
   as a separate hotfix) that 3 *other* fields — `region_loyalty_pressure`/`region_culture_states`/
   `entity_legend_facts`, all added by tickets closed earlier in this same session — were *missing*
   from that same carry-forward logic with no Bounded rationale, silently breaking Culture Drift and
   Living Legend route-bias beyond tick 1. That fix landed as its own ticket; `information_source_
   profiles` itself was deliberately left untouched (see point 5's Bounded finding).
7. Split the real remaining question (should `information_source_profiles` be reclassified
   persistent given its own conceptual shape as a static catalog, vs. a bigger phase-ordering
   change, vs. formally accepting Branch 3 as unreachable) into
   `TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION` — a genuine architecture
   decision with real blast-radius tradeoffs across every corpus world shipping
   `information_source_profiles`, not this ticket's own job to make unilaterally.

## Test Summary
No behavior-changing code was written by this ticket (the new world/profile YAML files are
content, not code, and produce zero observable effect until
`TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION` resolves the real blocker) — the
real deliverable is the investigation itself plus the ready-to-use corpus world. Verified:
`python3 -m src.worldbuilding.cli resolve unit_information_routing_pilot` and `... validate
unit_information_routing_pilot` both succeed (2 pre-existing harmless `WORLD-UNEXPECTED-SECTION`
warnings for `generation_seed`/`modules`, confirmed identical for the pre-existing
`unit_selfmodel_pilot` sibling world — not caused by this ticket). `tools/calibrate_simq.py --name
unit_information_routing_pilot --seed 42 --ticks 200` runs cleanly (`overall_grade=A`), with
INFORMATION at the same `grade=C events=0` baseline as before this ticket — expected, given the
real blocker documented above, not a regression.

## Files Changed
- `data/worlds/unit_information_routing_pilot/world.yaml` (new)
- `data/worlds/unit_information_routing_pilot/resolved/` (new, generated by `world-resolve`)
- `config/simulation_quality/profiles/unit_information_routing_pilot.yaml` (new)
- `tickets/todos/dormant-mechanism-closure/TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION.md`
  (new, split ticket)

## Completion Summary
The real blocker for idea M7's `route_new_query` SimQ rule turned out to be a structural,
cross-phase timing gap between two independently-correct, already-verified design decisions
(`information_source_profiles`'s Bounded/single-fire semantics, and same-tick phase-output
visibility) — not a missing-content gap as originally scoped. A real, minimal, dedicated corpus
world combining both compile-time-seeded halves Branch 3 needs was built and is ready to prove
whichever fix the split ticket ratifies. This investigation also directly surfaced and led to
fixing a real, separate regression affecting 2 other tickets closed earlier today
(`TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD`). Not pushed — left as local commits
on `dormant-mechanism-closure` per this session's own fork-execution constraints.
