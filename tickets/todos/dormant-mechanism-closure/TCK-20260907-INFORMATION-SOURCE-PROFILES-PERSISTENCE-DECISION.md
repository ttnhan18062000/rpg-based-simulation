---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION
phase: open
date: 2026-09-07
tags: [architecture, simulation-quality]
---

# TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION

## Title
Decide whether InformationBeliefPhase Branch 3 (route_new_query) can ever fire given two independently-correct design choices that never overlap

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Split out of `TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO` (Dormant Mechanism Closure epic,
child 6) on 2026-09-07: that ticket's own goal ("author a real corpus scenario exercising Branch
3") turned out to be **structurally impossible under the current architecture**, not a missing-
content gap. A real, minimal, dedicated corpus world was authored
(`data/worlds/unit_information_routing_pilot/`, `config/simulation_quality/profiles/
unit_information_routing_pilot.yaml`) combining both compile-time-seeded halves Branch 3 needs
(`pending_self_model_information_events` targeting a real unresolved unknown +
`information_source_profiles` with a real matching `knowledge_scopes` entry) — the exact
combination none of the 3 pre-existing unit-tier INFORMATION/COGNITION worlds provide. It still
does not fire `route_new_query`, confirmed via direct calibration run and step-by-step debugging.

**Root cause, verified directly**: Branch 3
(`InformationBeliefPhase.apply()`, `src/domains/information/phase.py:86-104`) needs BOTH of these
true in the SAME `refine()` call:
1. `actor.self_model.knowledge.unknowns` non-empty — only becomes true starting **tick 2**, since
   `SelfModelUpdatePhase`'s tick-1 `EntityUpdate` (which materializes the unknown from
   `pending_self_model_information_events`) is not visible to `InformationBeliefPhase.apply()`
   within the same tick's `refine()` call (it reads the frozen `state` argument, not the
   accumulating `update.entity_updates` other same-tick phases have already written) — only
   visible from tick 2 onward, once `ApplyPath.apply_generation()` persists it into `state.entities`.
2. `state.information_source_profiles` non-empty — only true on **tick 1**.
   `docs/guidelines/design_patterns.md` Pattern 6's own "known pitfall" section explicitly
   documents this as **intentional, verified-correct Bounded/single-fire behavior**
   (`TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` confirmed this and deliberately
   left it untouched — do not revisit that specific finding without new evidence).

These two conditions are never simultaneously true for the same tick — a structural,
un-bridgeable-by-corpus-content gap, not a "no world exercises it yet" gap. Verified with a direct
debug script driving a real `WorldCompiler.compile()` + `Kernel.tick_once()` loop against
`unit_information_routing_pilot` (unknowns present from tick 1 onward; profiles empty from tick 2
onward; `InformationQueryRouter.route()` returns zero candidates on every tick checked).

## Scope
- Decide, with real evidence (not guessed), which of the following is the correct fix — this is a
  genuine architecture decision, not a unilateral implementer call:
  1. **Reclassify `information_source_profiles` as persistent** (like `factions`), on the grounds
     that it is conceptually a static world-level catalog (source availability), not a one-shot
     event queue like its sibling `pending_information_responses` — the two were bundled under one
     "Bounded" umbrella in Pattern 6's doc without individually re-examining whether a catalog and
     an event queue actually share the same correct semantic. Verify whether making it persistent
     changes any pillar score for the 3 real worlds that already ship it
     (`urban_political`, `unit_information_source`, `unit_information_density`) via real
     recalibration — if `pending_information_responses`' own Branch 2 already fires and completes
     on tick 1 (as it does today), a persistent catalog should not double-fire Branch 2, only newly
     enable Branch 3 from tick 2 onward.
  2. **Change phase-visibility ordering** so `InformationBeliefPhase.apply()` can see the current
     tick's own `SelfModelUpdatePhase` output (e.g. read from `update.entity_updates` for actors
     already updated this tick, falling back to `state.entities` otherwise) — a bigger, riskier,
     cross-cutting pipeline-ordering change affecting every phase after `self_model` in the
     `refine()` sequence, not just `information_belief`.
  3. **Conclude Branch 3 is currently unreachable by design** and document this as a disclosed,
     accepted gap (a new `intentional_divergences.md` entry) rather than force a fix — matching
     `docs/world/fame_legend_contract.md`'s own "No Live Consumer Yet" precedent shape.
- Whichever option is chosen, prove `route_new_query` fires (or is formally accepted as
  unreachable) through `unit_information_routing_pilot`'s own real calibration run — that world is
  already built and does not need to change.

## Out of Scope
- Reopening `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD`'s own decision to leave
  `information_source_profiles`/`pending_information_responses` untouched as a blanket carry-forward
  — that finding (Bounded is correct for the event-queue half) stands; this ticket's option 1 above
  is narrower (reclassify only the catalog field, not the event-queue field).
- Redesigning `InformationQueryRouter`/`InformationIntentResolver`'s own matching logic — confirmed
  correct as-is by this investigation.

## Acceptance Criteria
- [ ] A real decision is made and recorded (ratified, not guessed) among the 3 options above.
- [ ] `route_new_query` either fires through `unit_information_routing_pilot`'s real calibration run
      (options 1/2), or its unreachability is formally disclosed (option 3) — either way, the
      INFORMATION pillar's own C/events=0 baseline for this world is resolved one way or the other,
      not left silently unresolved.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO` (`tickets/done/` — the investigation this was
  split out of; DONE with its own real deliverable being the investigation + the new corpus world)
- `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` (`tickets/done/` — the sibling
  finding this ticket's own root-cause investigation grew out of)

## Related Docs
- `docs/guidelines/design_patterns.md` (Pattern 6)
- `docs/simulation_quality/event_type_coverage.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/domains/information/phase.py` (`InformationBeliefPhase.apply()`)
- `src/engine/pipeline.py` (phase ordering/visibility)
- `src/engine/apply.py` (`ApplyPath.apply_generation()`)
- `data/worlds/unit_information_routing_pilot/`, `config/simulation_quality/profiles/
  unit_information_routing_pilot.yaml` (already built, real, ready to prove whichever fix is chosen)

## Assumptions / Open Questions
- Which of the 3 options is correct is not decided here — real decision work for whoever picks
  this ticket up, likely warranting its own architecture-reviewer pass given option 2's blast
  radius.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
