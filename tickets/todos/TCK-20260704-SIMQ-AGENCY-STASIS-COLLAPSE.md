---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE
phase: open
date: 2026-07-04
tags: [simulation_quality, agency, cognition, stasis, calibration, bug]
---

# TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE

## Title
Investigate AGENCY=F collapse in simq_routing_test seed456: entity 23 enters a sustained defer/stasis streak from tick 176

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP` fixed a `ResourceRegistry` crash that had, since
2026-05-18, silently prevented `simq_routing_test` (`ENABLE_ADVENTURE_ROUTING=ON`) from ever
completing a full calibration run for any seed. With the crash fixed, `seed456`'s 500-tick
calibration now completes — and reveals a real, previously-invisible defect: `AGENCY` grades `F`
(`normalized_score=-172541.0` raw / `-345.08` normalized), far below the D20 audit's AC6 gate
("AGENCY ≥ B confirmed for all three `simq_routing_test` seeds"). `seed42`/`seed123` are unaffected
(A/A).

Root cause was traced (not just observed) during the STONE-GAP ticket: in
`quality_scores.jsonl` for `run_1783171252_1673`, entity 23 enters a sustained
`defer_with_reason`/`stasis_N`-tagged event streak starting at **tick 176** — provably before
`ResourceEcologyService`'s first seed check (tick 200) can write any node into state, so this is
**not** caused by the STONE-GAP fix, the new `stone_outcrop` resource, or any other content change
in that ticket. It is a pre-existing property of this world's 2026-07-01-recompiled state plus
`AgencyScorer`'s stasis-penalty formula (`config/simulation_quality/scoring_weights.yaml:20`,
`stasis_per_tick = -3.0`, applied per subsequent defer event once a population-wide idle streak
crosses `stasis_gate_ticks`), only now observable because the STONE crash no longer blocks this
world from running to completion.

Because `tests/simulation_quality/fixtures/grade_anchors.json`'s consumer
(`GRADE_ORDER = ["D","C","B","A","S"]`) has no representable slot for `F`, `seed456`'s AGENCY anchor
was recorded as `"D"` (the schema floor, not the true grade) by the STONE-GAP ticket, specifically
so `test_grade_within_anchor_band[simq_routing_test_seed456_500t]` keeps correctly failing on any
future local re-run until this ticket's fix lands and the anchor is re-set to the true, fixed grade.
This test only fails when `data/calibration/simq_routing_test_seed456_500t/` exists locally
(gitignored, not committed) — it skips cleanly in a fresh checkout/CI absent that data, so this is
not currently blocking the wider test suite.

## Scope
1. Re-verify the finding against current `src/` (this ticket may be picked up after other changes
   land) — re-run `ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 456
   --name simq_routing_test` and confirm AGENCY still grades `F`.
2. Investigate why entity 23 (and, per the ticket's own finding, only in `seed456` — not `seed42`
   or `seed123`) enters a sustained `defer_with_reason`/`stasis_N` streak starting at tick 176.
   Trace the actual decision-making path that leads to this entity repeatedly deferring rather than
   selecting a route — this likely touches `AdventureDecisionPhase`/`AdventureRouteGenerator`
   (routing is ON in this world) and whatever blocker/precondition is causing routes to be
   perpetually rejected or deferred for this specific entity+seed combination.
3. Determine whether the fix belongs in (a) the entity's decision logic (something is stuck that
   shouldn't be), (b) `AgencyScorer`'s stasis-penalty formula (the penalty escalates without bound
   — `-3.0` per subsequent defer event compounding to `-172541.0` over 693 events seems
   disproportionate even for a genuinely stuck entity; consider whether the formula needs a floor,
   cap, or different scaling), or (c) both. Read `docs/mechanics/04_strategic_cognition.md` and the
   `AgencyScorer` source to determine which is architecturally correct before deciding — do not
   guess.
4. Once fixed, re-run `simq_routing_test` seed456 calibration and update
   `tests/simulation_quality/fixtures/grade_anchors.json`'s `simq_routing_test_seed456_500t` AGENCY
   anchor from the placeholder `"D"` to the true, now-fixed grade.
5. Re-confirm AC6 ("AGENCY ≥ B for all three `simq_routing_test` seeds") is fully satisfied across
   all 3 seeds, not just seed42/123.
6. Add a regression test proving this specific stasis-collapse scenario doesn't recur (if the fix is
   in decision logic) or that the stasis penalty formula behaves reasonably at scale (if the fix is
   in scoring).

## Out of Scope
- Any other `simq_routing_test` content changes (this ticket is scoped to the AGENCY/stasis
  finding only)
- Re-litigating `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`'s already-completed work (that
  ticket's fix is confirmed unrelated to this finding — the stasis streak begins before ecology's
  first seed check can even fire)
- Changing `ENABLE_ADVENTURE_ROUTING`'s default or scope

## Acceptance Criteria
- [ ] Root cause of entity 23's sustained defer/stasis streak (seed456, tick 176 onward) confirmed
      with file:line evidence
- [ ] Explanation for why this occurs in seed456 but not seed42/seed123 (seed-specific RNG draw,
      a specific route-generation edge case, or something else)
- [ ] Fix applied (decision logic, scoring formula, or both — per Scope item 3's investigation)
- [ ] `simq_routing_test` seed456's AGENCY grade no longer F; AC6 fully re-confirmed for all 3 seeds
- [ ] `grade_anchors.json`'s `simq_routing_test_seed456_500t` AGENCY anchor updated from the `"D"`
      placeholder to the true fixed grade
- [ ] New regression test prevents recurrence
- [ ] `make evaluate --dry-run` exits 0

## Related Tickets
- TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP (done) — fixed the crash that was blocking this
  world from completing calibration, which is what surfaced this finding; confirmed this finding is
  causally unrelated to that ticket's fix
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS (done) — the 2026-07-01 hazard-kind recompile that changed
  this world's dynamics is cited as context for when this stasis property may have been introduced
  or become observable

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` — STONE-GAP's dated NOTE documents this finding
  in full, including the exact `quality_scores.jsonl` run key (`run_1783171252_1673`) and event
  counts (693 AGENCY events, 491 `defer_idle`/`stasis_N`-tagged)
- `docs/mechanics/04_strategic_cognition.md` — goal/route decision logic, relevant if the fix is in
  decision-making rather than scoring
- `config/simulation_quality/scoring_weights.yaml` — `stasis_per_tick` and related AGENCY scoring
  constants

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP/` — investigation/plan documenting
  the original discovery and root-cause tracing of this finding

## Related Code Areas
- `src/domains/adventure/` — `AdventureDecisionPhase`, `AdventureRouteGenerator`
- Wherever `AgencyScorer` is defined (likely `src/simulation_quality/pillars.py` or similar) — the
  stasis-penalty formula
- `data/worlds/simq_routing_test/` — the world whose seed456 run exhibits this behavior

## Assumptions / Open Questions
- UQ-1: Is this a genuine entity-decision bug (something that should not get stuck, does), or a
  scoring-formula issue (the entity is correctly and intentionally idle for valid reasons — e.g. no
  legal route exists — but the penalty formula scales unreasonably)? These require different fixes
  and this ticket's own Scope item 3 defers the decision to investigation with evidence, not a
  guess made here.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
