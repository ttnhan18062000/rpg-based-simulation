---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING
phase: open
date: 2026-08-08
tags: [feature-flags, determinism]
---

# TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING

## Title
Enabling `ENABLE_ADVENTURE_ROUTING` on `frontier_marches` silently collapses tick-1 FACTION
(`diplomatic_transition`, S→C) and INFORMATION (`belief_assimilated`, B→C) pillar activity,
identically across all 3 calibration seeds — an apparent RNG-consumption side effect unrelated to
adventure routing itself, root cause not yet found

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
While investigating `TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF` (HERO entities'
underperformance on lifecycle metrics, traced to most worlds correctly not being
"routing-capable" per a ratified `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` design ruling — not a bug),
`frontier_marches` was identified as the one real, well-evidenced candidate for per-world
`ENABLE_ADVENTURE_ROUTING` opt-in (its own authored description names "a hero guild" as a
first-class world element; it composes the `hero_adventurers` population module with 3 real HERO
entities).

Enabling the flag and recalibrating via `tools/calibrate_simq.py` (all 3 seeds, 200 ticks,
`dropped_count=0`) confirmed AGENCY activates correctly (`C`/`0.0` → `A`/~0.71-0.94 on all 3
seeds, no stuck-hero failure mode — 72 real `route_selected`/`action_executed` events per hero in
an 800-tick live probe). **But the same calibration also showed, identically across all 3 seeds:
FACTION collapsing from `S`/`2.9` to `C`/`0.0`, and INFORMATION from `B`/`0.2` to `C`/`0.0`.**

**Isolated with a direct, controlled before/after comparison** (same world, same seed 42, only
the flag toggled): without routing, 29 real `diplomatic_transition` (FACTION, `delta=5.0` each)
events and 1 `belief_assimilated` (INFORMATION) event fire — **all at tick 1**, all either
`entity_id: None` (world-level diplomatic-state seeding) or attributed to a non-hero entity (id 9,
not one of the 3 `hero_adventurers` heroes, ids 31/32/33). With routing enabled, none of these
tick-1 events fire at all — not reduced, entirely absent.

Since these are tick-1, non-hero-attributed events, they should have **no logical dependency** on
`AdventureDecisionPhase` (which only runs for `EntityRole.HERO` entities). The most likely
explanation, not yet confirmed: enabling the flag changes which pipeline phases run at/around
tick 1 in a way that shifts the deterministic RNG draw sequence (`DeterministicRNG`), causing
whatever random rolls the diplomatic-transition/belief-assimilation seeding logic depends on to
draw different values (or be skipped/gated differently) than before — a real determinism-coupling
bug between unrelated subsystems sharing one RNG stream, not a logical interaction between
routing and faction/information mechanics.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm the exact mechanism: trace whether `diplomatic_transition`/`belief_assimilated`'s own
     tick-1 emission logic reads `state.rng`/`DeterministicRNG` calls whose consumption order is
     perturbed by `AdventureDecisionPhase` being present in the pipeline (even if it does nothing
     for a specific entity that tick), vs. some other coupling (e.g. a shared counter, a
     tick-ordering change, a cadence/phase-list length change affecting an unrelated index).
   - Reproduce on a second world (not just `frontier_marches`) if any other world also composes
     both `hero_adventurers`/routing-eligible content and FACTION/INFORMATION-seeding content, to
     confirm this isn't `frontier_marches`-specific.
   - Determine whether this same coupling affects `simq_routing_test`/`hero_guild_routing` (the 2
     worlds that already run with routing ON) — if so, their own FACTION/INFORMATION anchors may
     already be silently affected and warrant their own re-check.
2. **Plan**: design the fix — likely either (a) giving `AdventureDecisionPhase` its own isolated
   RNG stream/substream so its presence cannot perturb unrelated phases' draws, or (b) a
   phase-ordering/consumption fix specific to whatever the trace in step 1 finds.
3. **Implement**: the fix, verified by re-running the exact before/after comparison this ticket's
   own investigation already established (with routing ON, `diplomatic_transition`/
   `belief_assimilated` must fire at tick 1 exactly as they do with routing OFF).
4. Once fixed: revisit enabling `ENABLE_ADVENTURE_ROUTING` for `frontier_marches` (the original
   goal of the parent ticket) with real evidence the regression no longer occurs.

## Out of Scope
- Re-attempting the `frontier_marches` flag flip itself before this root cause is fixed — that is
  the explicit condition for revisiting it, not parallel work.
- Any other HERO/AGENCY finding from the parent ticket — this is narrowly the FACTION/INFORMATION
  regression mechanism.

## Acceptance Criteria
- [ ] investigation.md identifies the exact real mechanism causing the tick-1 event suppression
- [ ] investigation.md confirms or rules out the same coupling on `simq_routing_test`/
      `hero_guild_routing`'s own existing anchors
- [ ] A real fix lands, verified by the before/after `diplomatic_transition`/`belief_assimilated`
      comparison firing identically with routing ON as with it OFF
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF (the parent ticket this regression was found
  during; the `frontier_marches` flag flip itself is blocked on this ticket)
- TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA (the ratified DA ruling establishing routing as a per-world
  archetype opt-in — the mechanism this ticket's fix must remain compatible with)

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` — "AGENCY — Cross-World Design Note"

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF/investigation.md` — the real
  before/after data (event counts, entity attribution) this ticket's own investigation is grounded
  in

## Related Code Areas
- `src/domains/adventure/phase.py` (`AdventureDecisionPhase`)
- `src/platform/rng.py` (`DeterministicRNG`)
- `src/engine/faction_decision.py` (diplomatic transition emission)
- `src/domains/information/` (belief assimilation emission)
- `src/engine/pipeline.py` (phase ordering/registration)

## Assumptions / Open Questions
- Whether this is genuinely an RNG-consumption coupling or a different mechanism entirely — not
  assumed; Investigate must trace the real call sequence, not guess from the symptom alone.

## Implementation Notes
Subagent spawning unavailable this session (200/200 cap) — self-performed throughout.

The ticket's own RNG-consumption-order hypothesis was **rejected** after real, controlled tracing:
a monkey-patched `frontier_marches` seed-42 probe confirmed `diplomatic_state_machine
.compute_transitions()` is a pure function of `state.factions` (zero RNG calls) and produced the
identical 58 `FactionUpdate` objects regardless of the routing flag. Further monkey-patching
`AuthoritativeApplyPipeline.refine()` itself isolated the real defect: `refine()`'s own returned
`StateUpdate.faction_updates` was 58 with routing OFF and 0 with routing ON — the discard happened
strictly inside `refine()`, after the merge, before return.

Root cause: `src/engine/pipeline.py`'s `adventure_decision` phase call site was the one phase in
the file whose `run_phase()` lambda did not wrap its result in `u.merge(...)` (every sibling phase
does). `AdventureDecisionPhase.apply()` is correctly self-contained (fresh `StateUpdate()`, no `u`
parameter at all) — the bug was entirely at the call site, silently discarding every phase's output
that ran earlier in the same tick whenever `ENABLE_ADVENTURE_ROUTING=ON`, every tick, not just
tick 1. One-line fix: add `u.merge(...)`.

Checked (not assumed) the 2 existing routing-enabled worlds' own already-committed anchors:
SOCIAL/FACTION/INFORMATION are unaffected (flag OFF or no content authored for either world), but
AGENCY/COGNITION/PROGRESSION/COMBAT/ECONOMY/WORLD/NARRATIVE showed real, material drift across all
8 anchored run_keys once actually recalibrated (some letter-grade shifts, e.g. COGNITION S->A
twice) — broader impact than originally hypothesized (not just FACTION/INFORMATION). Re-verified
via real `tools/calibrate_simq.py` runs (not assumed) and updated `grade_anchors.json` with
attribution, matching `corpus_tier_taxonomy.md`'s own Regression/baseline-tier drift-handling
precedent. Also found and fixed an unrelated hardcoded test-count sentinel
(`test_grade_anchors_entry_count_unchanged`, 80->81) that TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD
had left stale (separate commit, attributed to that ticket).

Deferred (per this ticket's own Out of Scope): re-attempting the `frontier_marches` flag flip
itself — the fix is landed and verified, but that flip is its own future ticket's job.

## Test Summary
New regression test:
`tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py::
test_adventure_decision_does_not_discard_earlier_phase_updates` — real `refine()` run with routing
ON, asserts `faction_updates` survives. `pytest tests/unit/movement/ tests/unit/combat/
tests/integration/domains/adventure/ tests/unit/strategic/ tests/simulation_quality/
test_grade_regression.py -q -m "not slow"` — 396+70 passed, 3 pre-existing unrelated failures
(confirmed via `git stash` against this ticket's own change: `test_normal_move_triggers_oa`,
`test_crafting_project_produces_item_crafted_event_through_full_pipeline`,
`test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline`, all fail
identically without this ticket's fix).

## Files Changed
- `src/engine/pipeline.py` — `u.merge()` fix for the `adventure_decision` phase call site
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` — new regression test
- `docs/guidelines/intentional_divergences.md` — new §2.35 entry
- `docs/parity_ledger/strategic_cognition.yaml` — new STRAT-250 entry
- `tests/simulation_quality/fixtures/grade_anchors.json` — 8 run_keys recalibrated with real
  post-fix data (`hero_guild_routing`/`simq_routing_test`, all seeds, 500t+1000t)

## Completion Summary
Real root cause found via direct, controlled tracing — rejecting the ticket's own original
RNG-consumption-order hypothesis with evidence rather than assuming it. Fix is a 1-line change
matching an established sibling pattern, verified via a real before/after probe and a new
regression test. Anchor drift on the 2 existing routing-enabled worlds was checked (not assumed)
and found real, broader than the ticket's own FACTION/INFORMATION framing (AGENCY/COGNITION/
PROGRESSION also affected) — re-verified and re-committed with attribution rather than left
inconsistent with the now-fixed engine behavior. All Acceptance Criteria satisfied with real
evidence.
