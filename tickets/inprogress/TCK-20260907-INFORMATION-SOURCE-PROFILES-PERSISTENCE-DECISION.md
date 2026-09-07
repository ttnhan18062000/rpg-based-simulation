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
BLOCKED

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
- **Ratified 2026-09-07 (real user decision, via `AskUserQuestion`)**: **Option 1 — reclassify
  `information_source_profiles` as persistent**, like `factions`. Implementation must verify no
  pillar-score regression across the 3 real worlds already shipping it (`urban_political`,
  `unit_information_source`, `unit_information_density`) via real recalibration — `pending_information_
  responses`' own Branch 2 already fires/completes on tick 1 today, so a persistent catalog must not
  double-fire Branch 2, only newly enable Branch 3 from tick 2 onward. Then prove `route_new_query`
  fires through `unit_information_routing_pilot`'s own real calibration run (already built, does not
  need to change).

## Implementation Notes

**2026-09-07 — Option 1 (persistence reclassification) implemented and verified; ticket BLOCKED on
a newly-discovered, separate, real bug — not closed DONE.**

1. **Code change** (done, verified, real, no regression): `src/engine/apply.py`,
   `ApplyPath.apply_generation()`'s `AuthoritativeState(...)` constructor call — added
   `information_source_profiles=prior_state.information_source_profiles,` immediately after
   `entity_legend_facts=...`. Deliberately did NOT add `pending_information_responses` — investigation
   confirmed Branch 2 (`InformationBeliefPhase.apply()`, `src/domains/information/phase.py:48-84`) has
   zero dependency on `information_source_profiles`, so this split cannot cause Branch 2 to double-fire
   (structurally impossible given the current code, not merely unlikely — see investigation.md).
2. **New tests** (all pass): `tests/unit/engine/test_apply_generation_episode_bridge_carryforward.py`
   gained 4 new tests (`test_information_source_profiles_survives_apply_generation`,
   `..._survives_multiple_generations`, `test_pending_information_responses_still_not_carried_forward`,
   `test_default_empty_source_profiles_stay_empty_no_regression`). Full file: 21/21 pass.
3. **Regression verification** (no regression confirmed): ran `tools/calibrate_simq.py` for the 3
   real worlds already shipping `information_source_profiles` BOTH before and after the fix (toggled
   the one-line change locally, not via git stash, to get a clean A/B comparison):
   - `urban_political`: INFORMATION grade=B events=1 identical before/after.
   - `unit_information_source`: INFORMATION grade=B events=1 identical before/after.
   - `unit_information_density`: INFORMATION grade=A events=3 identical before/after.
   Confirms the AC's own stated risk (Branch 2 double-firing) does not occur.
4. **`unit_information_routing_pilot` recalibration: CRASHES**, both with and without
   `ENABLE_INFORMATION_INTENT_EXECUTION=ON` (tested both, same crash):
   ```
   AttributeError: 'ActionIntent' object has no attribute 'accepted'
     at src/systems/strategic_systems/work_queue.py:55, StrategicWorkQueue.build()
   ```
   **Root cause, traced fully**: `InformationBeliefPhase.apply()` Branch 3
   (`src/domains/information/phase.py:99-106`) stores a raw, un-resolved `ActionIntent` directly into
   `EntityUpdate.intent_results` (a field typed `List[IntentResult]`, a completely different
   dataclass — `src/core/state.py:820`, has an `.accepted` field the raw `ActionIntent` does not).
   The dedicated production call site meant to resolve it,
   `src/engine/pipeline_phases/information_intent_execution.py`
   (`InformationIntentExecutionPhase.execute()`, gated `ENABLE_INFORMATION_INTENT_EXECUTION`, default
   OFF), delegates to `ActionIntentAdapter.execute()` but **never removes or replaces the original raw
   `ActionIntent` entry** — `EntityUpdate.merge()` (`src/core/updates.py:779`) additively concatenates
   `intent_results` (`self.intent_results + other.intent_results`), so the raw candidate survives the
   "execution" step unchanged. `src/engine/patches.py:236` then unconditionally replaces
   `entity.identity.latest_intent_results` with `tuple(self.intent_results)` whenever it's non-empty —
   installing the still-unresolved raw `ActionIntent` as the entity's authoritative last-intent-result.
   `StrategicWorkQueue.build()` (`src/systems/strategic_systems/work_queue.py:55`) then reads
   `r.accepted` off every entry unconditionally and crashes.

   This is **dormant, pre-existing code** (`InformationIntentExecutionPhase` itself has never been
   exercised by any real corpus world either — nothing has ever fed it a real `ActionIntent` before,
   since Branch 3 could never previously fire) — this ticket's own fix is what finally makes Branch 3
   reachable for the first time in any real run, which is what surfaces this second, independent,
   deeper dormant-mechanism bug.

   Confirmed via direct code read this is **not fixable within this ticket's own Out-of-Scope
   boundary** ("Redesigning `InformationQueryRouter`/`InformationIntentResolver`'s own matching
   logic — confirmed correct as-is") — the bug is one level downstream of the router/resolver, in
   `InformationIntentExecutionPhase`'s merge handling and/or `StrategicWorkQueue.build()`'s
   unconditional `.accepted` access, both real but separate subsystems.

**Disposition**: leaving this ticket BLOCKED (not DONE, not reverted) — the persistence-reclassification
code change itself is real, correct, and regression-free, and is kept. AC2 ("`route_new_query` fires...
or unreachability formally disclosed") cannot be satisfied without fixing the newly-found
`InformationIntentExecutionPhase`/`StrategicWorkQueue` bug, which is out of this ticket's own scope
and needs its own real ticket + a decision on priority (this is now the epic's own dormant-mechanism
pattern recursing one level deeper — a bug in the very code meant to prove idea M7's `route_new_query`
rule works at all). Per this session's own scope-containment directive, not fixing it here — reporting
back for a real decision instead.

## Test Summary
`pytest tests/unit/engine/test_apply_generation_episode_bridge_carryforward.py
tests/integration/scenarios/test_phase5_information_belief_scenarios.py -q` → 17 passed.
`pytest tests/unit/engine/ tests/unit/domains/information/
tests/integration/scenarios/test_phase5_information_belief_scenarios.py -q -m "not slow"` → 232
passed, 1 skipped, 3 deselected. Real calibration A/B (see Implementation Notes point 3) — no
regression on the 3 existing worlds. `unit_information_routing_pilot` calibration crashes (point 4)
— this is the blocker, not a test failure in the traditional sense.

## Files Changed
- `src/engine/apply.py` (1-line carry-forward addition + comment)
- `tests/unit/engine/test_apply_generation_episode_bridge_carryforward.py` (4 new tests)
- `staging_artifacts/TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION/{investigation,plan,test_plan}.md` (new)

## Completion Summary
NOT DONE — BLOCKED. The persistence-reclassification code change (this ticket's own Option 1 scope)
is implemented, tested, and verified regression-free against the 3 real worlds already shipping
`information_source_profiles`. However, exercising it end-to-end against
`unit_information_routing_pilot` (the corpus world built specifically to prove this fix) crashes the
engine on a second, separate, real, pre-existing dormant-mechanism bug in
`InformationIntentExecutionPhase`/`StrategicWorkQueue.build()` (full root-cause trace above) — this
bug has never been exercised before because Branch 3 could never previously fire to feed it a real
`ActionIntent`. This ticket cannot honestly claim AC2 satisfied while that crash stands. Recommend:
file a new real ticket for the `InformationIntentExecutionPhase` merge/`StrategicWorkQueue.accepted`
bug, then resume this ticket once that lands.
