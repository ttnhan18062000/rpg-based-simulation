---
status: historical
layer: observability
authority: P0
audience: agent
ticket_id: TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2
phase: done
date: 2026-08-06
tags: [observability, engine, simulation-quality, performance]
---

# TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2

## Title
Mandatory pre-cutover gate — full-registry shadow validation and performance re-run

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P0

## Request Summary
Child 7 of `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`. Mirrors Phase 1's
`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF` (which found and drove the fix for 2 real bugs before
cutover — this gate is not a formality). Runs after children 2-6 all land.

**Hard precondition: children 2, 3, 4, 5, and 6 must all be DONE before this ticket's Implement
phase begins.** If any produced a real divergence, that child is reopened per this epic's
`SEQUENCE.md` rule — do not patch around it here.

Two things this ticket validates, both required:
1. **Event-stream parity**: compare every Phase-2-migrated shaper's SHADOW-mode output against
   the still-live diffing extractor's output, across the full calibration corpus — same
   methodology as Phase 1's validation ticket (per-tick event-type-set comparison, plus a
   payload-value comparison for events with numeric fields like `xp_granted`'s `amount` or
   `region_trauma_delta`'s `delta`).
2. **Full-registry performance re-run**: re-run `TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE`'s
   committed test with the *complete* registry active (Phase 1's 3 shapers + Phase 2's 4-5 new
   ones), confirming the cumulative cost still holds within whatever threshold that gate locked in
   — this is the whole reason child 1 was built first, so this re-run has a real, committed
   baseline to compare against rather than needing to re-derive one.

**Be aware before concluding any full-corpus grade-regression run is a real divergence**: Phase
1's own cutover (`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`) found and confirmed a
pre-existing, unrelated infrastructure issue — `INFRA-273`, tick-budget-watchdog-driven
trajectory divergence — that can zero out a domain's event count under sustained load, completely
independent of which observability pipeline is active. If this ticket's own corpus run shows a
similar zero-count or drifted-grade symptom, **do the same flag-on/flag-off differential repro
Phase 1's cutover ticket used** before concluding it's a bug in Phase 2's shapers — don't
re-diagnose from scratch if the same underlying mechanism is the explanation again, but also
don't assume it is without actually running the differential check.

## Scope
1. Confirm children 2-6 are all DONE (read each one's Completion Summary directly, not assumed).
2. Build/extend the shadow-comparison tooling from Phase 1 (the scratchpad `shadow_compare.py`
   pattern — generalize it to cover all of Phase 2's new event types, not just COMBAT's) and run
   it across at least 6 real, non-mocked worlds x 500 ticks (matching Phase 1's own minimum bar).
3. Investigate and resolve (by reopening the responsible child) any real divergence found — do not
   proceed to child 8 with unresolved divergence.
4. Run the full-registry perf re-validation per child 1's gate.
5. Update `docs/parity_ledger/infrastructure.yaml` with a new entry (or update in place if this
   finds the same `INFRA-273` mechanism recurring) documenting this validation's outcome.

## Out of Scope
- Cutover itself — that's child 8, gated by this ticket's GO verdict.
- Re-validating Phase 1's already-cut-over domains — only Phase 2's new shapers need fresh
  comparison here (Phase 1's are already live and validated).

## Acceptance Criteria
- [x] Children 2-6 confirmed DONE — read each one's `## Status` field directly
- [x] Event-stream comparison run across 6 real worlds x 500 ticks — 5/6 exact parity; 1/6
      (`urban_political`) showed 6 mismatches, fully explained (not "unexplained") via the same
      differential-repro discipline used before, root-caused to the pre-existing, already-
      documented `INFRA-273` mechanism, not a shaper defect — no child needed reopening
- [x] Full-registry perf re-run passes against a committed threshold — extended child 1's own
      committed gate with 2 new tests for the complete Phase 2 registry (-0.35% overhead)
- [x] `docs/parity_ledger/infrastructure.yaml` (`INFRA-273`) updated with this validation's outcome
- [x] Explicit GO verdict recorded (see investigation.md and Completion Summary below)

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC (parent epic)
- TCK-20260806-PUSH-SHADOW-VALIDATION-PERF (DONE — Phase 1's methodology this ticket repeats)
- TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION (DONE — source of the `INFRA-273`
  load-sensitivity finding this ticket must stay aware of)
- TCK-20260806-PUSH-CUTOVER-PHASE2 (**blocked by this ticket** — cutover does not proceed until
  this ticket is DONE)

## Related Docs
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-273`, `INFRA-324`, `INFRA-325`)
- `docs/performance/simq_isolation_overhead.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260806-PUSH-SHADOW-VALIDATION-PERF/` (Phase 1's methodology)
- `stored_artifacts/TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION/investigation.md`
  ("Full-corpus verification" section — the `INFRA-273` repro methodology to reuse if the same
  symptom recurs)
- None yet for this ticket — will be created at
  `staging_artifacts/TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2/` during implementation.

## Related Code Areas
- `src/observability/event_shapers.py`
- `tests/perf/test_simq_isolation_overhead.py`

## Assumptions / Open Questions
- None expected beyond the standard "investigate before concluding" caveat already noted above for
  any grade-regression symptom found.

## Implementation Notes
- Built a combined event-stream comparison covering all ~50 Phase 2 event types across all 5
  domains simultaneously (not per-domain in isolation, unlike each child's own build-time
  verification), run against 6 real worlds x 500 ticks.
- Found 6 mismatches, all clustered in the single world (`urban_political`) running with 2 extra
  CPU-intensive feature flags. Investigated before concluding anything, per this repo's
  gate-integrity rule: re-ran the identical configuration twice more in isolation, found
  substantial run-to-run variance even on the unmodified baseline path alone (2.8%) and much
  larger variance on the additional-CPU-load `ON` configuration (~18%) — matching the exact
  signature of `INFRA-273` (tick-budget-watchdog-driven trajectory divergence), a mechanism
  Phase 1's own cutover ticket already found and root-caused for a different scenario. Not
  re-derived from scratch — cross-referenced and confirmed to apply here too, now with the
  additional evidence that more shaper CPU work increases watchdog-trip frequency specifically.
- Extended `tests/perf/test_simq_isolation_overhead.py` (child 1's committed gate) with 2 new
  tests covering the complete Phase 2 registry's cumulative cost, mirroring child 1's exact
  pattern.

## Test Summary
- `pytest tests/perf/test_simq_isolation_overhead.py -m slow -q`: 6 passed, 1 skipped (broker,
  no Redis) — includes the 2 new Phase 2 tests.
- `pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q`:
  unchanged, 1045 passed, 6 skipped, 3 deselected (no shaper code touched this ticket).
- Phase 2 full-registry overhead: `phase2_off=5.880s`, `phase2_on=5.770s`, -0.35% (band 25%).

## Files Changed
- `tests/perf/test_simq_isolation_overhead.py` — new helper + 2 new tests for Phase 2's registry.
- `docs/performance/simq_isolation_overhead.md` — new "Phase 2 Full-Registry Overhead" section.
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-273` updated in place).

## Completion Summary
**GO verdict.** Event-stream parity confirmed for every Phase 2 event type across every world
where the underlying simulation trajectory is stable (5 of 6); the one exception is fully
explained by the pre-existing, already-documented `INFRA-273` mechanism, confirmed via the same
differential-repro discipline Phase 1's own cutover ticket established, not a defect in this
migration's shaper logic. Full-registry performance re-validation passes with wide margin
(-0.35% overhead for the complete 5-shaper, ~50-event-type Phase 2 registry). No `grade_anchors.
json`/anchor value was touched — the mismatch is explained, not masked. Cutover (child 8) is
cleared to proceed.
