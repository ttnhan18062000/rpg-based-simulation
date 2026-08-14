---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-CUTOVER-PHASE2
phase: done
date: 2026-08-06
tags: [observability, engine, simulation-quality]
---

# TCK-20260806-PUSH-CUTOVER-PHASE2

## Title
Cut over Phase 2's remaining domains from diffing to live apply-layer shaper emission

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 8 (final) of `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`. The irreversible
step for Phase 2, mirroring Phase 1's `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION` exactly:
flip Phase 2's shapers from SHADOW (construct-but-don't-deliver) to live delivery, flag-gating
(not deleting) the old diffing branches as a real, verified rollback.

**Hard precondition: `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2` must be DONE with an
explicit GO verdict before this ticket's Implement phase begins.**

Phase 1's cutover already established the deployment-mechanism pattern this ticket reuses
verbatim, not redesigns: `ENABLE_PUSH_EVENT_SHAPERS` already defaults `ON` (flipped by Phase 1),
so no new flag or default change is needed here — Phase 2's shapers register into the *same*
`SHAPER_REGISTRY` and respect the *same* flag. The work is narrower than Phase 1's cutover:
removing/narrowing the now-redundant diffing branches in `event_extractor.py` for Phase 2's ~50
events, following the exact same "narrow the condition, don't delete the branch" pattern Phase 1
used for `entity_killed`/`hero_death_unrecorded` wherever a Phase 2 event has a broader
non-shaper-owned cause than its shaper covers (confirm case-by-case during Implement — do not
assume every Phase 2 event is a clean removal just because most of Phase 1's were).

## Scope
1. Confirm child 7's GO verdict directly (read its Completion Summary) before starting.
2. For each of Phase 2's ~50 migrated events, flag-gate (not delete) the old
   `event_extractor.py` branch — reusing the `_push_shapers_active` flag check already
   established in Phase 1's cutover.
3. Check each event individually for a Phase-1-style "broader old-branch scope" complication
   (like `entity_killed`'s any-cause-vs-same-tick-KILL narrowing) before assuming wholesale
   flag-gating is safe — this is exactly the kind of check that caught a real coverage gap in
   Phase 1 and must not be skipped here just because Phase 2's shapers were more directly
   push-ready than Phase 1's.
4. Run the full calibration corpus post-cutover, compare against child 7's validated baseline.
5. Recalibrate `grade_anchors.json` only if a genuine, understood difference is found — same
   discipline Phase 1 held (do not recalibrate reflexively; if a full-corpus run surfaces
   `INFRA-273`-pattern symptoms again, root-cause via the same differential-repro method before
   touching any anchor).
6. Update all touched parity ledger files (`strategic_cognition.yaml`, `progression.yaml`,
   `world_dynamics.yaml`, `social_narrative.yaml`, `town_resource.yaml`, `faction.yaml`,
   `infrastructure.yaml` as applicable).
7. Update `docs/audits/D20_simq_quality_status_review.md` with this epic's completion.

## Out of Scope
- Any shaper logic changes — this ticket delivers what child 7 already validated.
- `quest_system`'s emission architecture — out of this epic entirely (see epic's Out of Scope).
- Removing `EventExtractor` — it remains the rollback path for both Phase 1 and Phase 2's
  migrated domains.

## Acceptance Criteria
- [x] Child 7's GO verdict confirmed before starting
- [x] Every Phase 2 event's old branch flag-gated (or narrowed, matching its own specific
      coverage-scope check), not wholesale-deleted
- [x] Any broader-scope complications (Phase-1-style) found and handled individually, not assumed
      away — the `world_emergence_event`/`narrative_milestone` co-location with Phase 1's own
      guard in the same `world_events_add` loop
- [x] Full corpus re-run matches child 7's validated baseline — 37/69 `test_grade_regression.py`
      failures (up from Phase 1's 32/69), root-caused via decisive differential-repro as the same
      pre-existing `INFRA-273` mechanism now visible on more pillars, not a correctness regression
- [x] `grade_anchors.json` unchanged unless a genuine, documented difference was found — left
      unrecalibrated, no genuine non-`INFRA-273` difference found
- [x] All applicable parity ledger entries updated
- [x] `D20_simq_quality_status_review.md` updated with the full epic's (Phase 1 + Phase 2)
      completion (Finding 13)
- [x] Full scoped pytest run passes

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC (parent epic — closes once this
  lands)
- TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2 (**hard blocker**)
- TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION (DONE — the exact pattern this ticket repeats,
  including the flag-gated-mutual-exclusion deployment decision and the `INFRA-273` awareness)

## Related Docs
- `docs/parity_ledger/` (all applicable files)
- `docs/simulation_quality/quality_scoring_contract.md`
- `docs/audits/D20_simq_quality_status_review.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION/` (deployment-mechanism
  pattern and `INFRA-273` repro methodology, reused not redesigned)
- None yet for this ticket — will be created at `staging_artifacts/TCK-20260806-PUSH-CUTOVER-PHASE2/`
  during implementation.

## Related Code Areas
- `src/observability/event_extractor.py` (branches flag-gated/narrowed)
- `src/observability/event_shapers.py`

## Assumptions / Open Questions
- None expected to be genuinely open at this stage — this ticket executes what child 7 already
  validated. If something unexpected surfaces during Implement, treat it as a real finding to stop
  and report, not to work around silently.

## Implementation Notes
Deviated from this ticket's own stale premise (recorded explicitly, not silently substituted):
the Request Summary assumed Phase 2 reuses Phase 1's already-`ON` `ENABLE_PUSH_EVENT_SHAPERS` flag
— written before `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` existed (added later, during
`TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY`, specifically to avoid double-firing against Phase
1's already-live default). Actual mechanism: flipped `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`'s own
default `OFF`->`ON`.

Added `_push_shapers_phase2_active` to `event_extractor.py` (mirroring `_push_shapers_active`'s
exact pattern) and individually flag-gated every one of Phase 2's ~50 event constructions,
checking each for a Phase-1-style broader-scope complication before wholesale-gating — one found:
`world_emergence_event`/`narrative_milestone` co-located with Phase 1's own already-guarded
`war_declared`/`military_conflict_resolved` if/elif in the same `world_events_add` loop; the two
guards now coexist, each gating a disjoint construct set on its own flag.

Found and fixed a real bug via real-kernel verification: `event_shapers.py`'s
`run_shadow_shapers()` read the same flag via its own separate, stale `"OFF"` default, causing a
total blackout (0 events from either path) under the real post-cutover default state. Fixed by
flipping that default to `"ON"` too, with explicit lockstep-warning comments in both files. See
`docs/parity_ledger/infrastructure.yaml` `INFRA-326` for the full account.

Full-corpus re-run found 37/69 `test_grade_regression.py` failures (up from Phase 1's 32/69),
root-caused via a decisive differential-repro (flag forced OFF vs ON, kernel driven directly for
`urban_political_selfmodel_probe_seed42_200t`): COMBAT/PROGRESSION byte-identical between the two
pipelines, SOCIAL varying only ~1.5% with the same grade, `WatchdogTrip` alerts firing in both —
confirmed as the same pre-existing `INFRA-273` mechanism, not a Phase 2 regression.
`grade_anchors.json` left unrecalibrated. 2 pre-existing, unrelated test failures found and
disclosed via a filed ticket (`TCK-20260807-SCALE-VALIDATION-ENTITY-COLLISION-BUG`), not silently
absorbed. One now-stale test from Child 2 renamed/extended to match the new default.

## Test Summary
- `tests/unit/observability/` + `tests/perf/test_simq_isolation_overhead.py`: 908 passed, 7
  skipped.
- Full `tests/perf/` suite: 1046 passed, 6 skipped, 3 deselected, excluding 2 disclosed
  pre-existing unrelated failures.
- Real, non-mocked 5-world kernel runs: default state (post-fix) delivers correctly
  (event_extractor=0 no leak, event_shapers=43-845 real delivery); explicit
  `ENABLE_PUSH_EVENT_SHAPERS_PHASE2=OFF` rollback restores old-path delivery
  (event_extractor=911 on `hero_guild_routing`).
- Full calibration corpus (`make simq-full-audit-full`, 79 scenarios): 37/69
  `test_grade_regression.py` failures, root-caused as pre-existing `INFRA-273`, not a Phase 2
  regression — see Implementation Notes and `stored_artifacts/TCK-20260806-PUSH-CUTOVER-PHASE2/
  investigation.md`.
- Doc-staleness gate: PASS. Architecture-Verify: `kernel.py`'s pre-existing FAIL lines confirmed
  untouched by this ticket's diff via `git diff --unified=1`. Parity cross-reference gate: PASS
  (all 4 changed `src/` files' expected subsystem candidates touched). Verify static precheck: all
  7 conditions PASS.

## Files Changed
- `src/observability/event_extractor.py` — every Phase 2 branch individually flag-gated
- `src/observability/event_shapers.py` — `run_shadow_shapers()`'s default-lockstep fix
- `docs/parity_ledger/strategic_cognition.yaml`, `progression.yaml`, `world_dynamics.yaml`,
  `social_narrative.yaml`, `town_resource.yaml`, `faction.yaml` — cutover update notes
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-326` entry, `INFRA-273` updated in place
- `docs/audits/D20_simq_quality_status_review.md` — Finding 13, pillar table updates
- `tests/unit/observability/test_event_shapers_strategy.py` — 1 test renamed, 1 test added

## Completion Summary
Phase 2's remaining ~50 events (AGENCY/COGNITION/INFORMATION/PROGRESSION/WORLD/SOCIAL) are now
live apply-layer emission by default, with a real, verified, flag-gated rollback to the old
diffing `event_extractor.py` path — mirroring Phase 1's cutover mechanism exactly. Found and fixed
one real, previously-undetected bug (the `run_shadow_shapers()` default-lockstep total blackout)
via real-kernel verification the unit-test suite alone could not have caught. Root-caused the
full-corpus grade-regression delta (37 vs Phase 1's 32 failures) as the same pre-existing
`INFRA-273` mechanism now visible on more pillars, via a decisive differential-repro, not assumed
either way. This closes the final child of
`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`.
