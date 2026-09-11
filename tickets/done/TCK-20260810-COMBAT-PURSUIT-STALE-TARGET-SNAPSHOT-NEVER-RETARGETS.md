---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS
phase: done
date: 2026-08-10
tags: [combat, engine]
---

# TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS

## Title
Two real, independent gaps in `TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE`'s own live-retargeting
fix — `MovementCandidateSelector.select()`'s own separate staleness check, and both real
`ENTITY_MOVE` work-item dispatchers re-affirming a stale snapshot every tick — silently defeated
that fix entirely for genuinely stuck pursuits, confirmed via a 990+-tick frozen mutual-pursuit
pair even with the prior fix already merged

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Follow-up from `TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION`: the user asked what
`PURSUIT_ABANDONED` (100% of real `combat_engagement_ended` outcomes in that investigation's own
`dungeon_crawl_seed42_2000t` run) means, then asked to continue investigating why it dominates.
`search_docs`/`graphify` surfaced a chain of 6 same-day, already-DONE tickets on this exact
combat-resolution-rate thread: `TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE` (identity-resolver
fix enabling real hostile-pair detection), `TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-
RANGE` (investigation-only, found 2 plausible contributing factors, too sparse to confirm),
`TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE` (COMB-304 — fixed `route_movement_intent()` to
live-retarget from `task.payload["target_id"]`'s current position instead of a stale snapshot;
verified `is_attack_legal` rate improved 0%→44%), `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-
FALSE-INVESTIGATION`, `TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE` (pushed real
attack-legal rate to 28.5%/36.6%), and `TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY`.
All 6 already merged into this branch.

Given COMB-304's own already-merged live-retargeting fix, `PURSUIT_ABANDONED` sitting at 100% was
unexplained — that fix should have prevented exactly this symptom. Direct pipeline instrumentation
(a monkeypatched `AuthoritativeApplyPipeline.refine()` wrapper, real non-mocked
`Kernel.tick_once()` loop) traced two mutually-pursuing entities (`dungeon_crawl_seed42_2000t`,
IDs 25 and 12) frozen at exactly Manhattan distance 2.0 (diagonally adjacent) for 990+ consecutive
ticks — `readiness=100.0` throughout, ruling out a readiness-starvation explanation, and confirmed
this was happening **even with COMB-304's own fix already active**.

**The real, decisive finding — two separate, independent gaps in COMB-304's own fix, neither
touched by that ticket's own scope**:
1. `MovementCandidateSelector.select()` (`src/engine/candidate_selector.py`) — the movement-
   candidacy gate that runs BEFORE `route_movement_intent()`'s own per-entity loop even gets a
   chance to execute — has its own, separate, un-refreshed "already at target, skip" check.
   Direct instrumentation confirmed entity 25 was excluded from `selected_ids` (`25 in
   selected=False`) from tick 10 onward, permanently — meaning `route_movement_intent`'s own
   already-correct live-retarget logic never got a chance to run for it at all.
2. Both real `ENTITY_MOVE` work-item dispatchers — `src/engine/executor.py`'s
   `LocalSequentialExecutor` (used when `profile.max_worker_count==0`) and
   `src/engine/worker_logic.py`'s `default_simulation_worker` (dispatched via
   `ConcurrentExecutionAdapter`, the REAL path for `PROD_SMALL`/`HardwareClass.CLASS_C`,
   `max_worker_count=2`) — re-emit `NavigationUpdate(target_set=payload["target_position"])`
   every tick a pursuit task is scheduled, reading the SAME static payload snapshot every time.
   `route_movement_intent()`'s own `has_fresh_decision` check
   (`ent_upd.navigation.target_set is not None`) cannot distinguish this routine reaffirmation
   from a genuine new tactical decision — `target_set` is always non-None, so
   `has_fresh_decision` is always spuriously `True`, and COMB-304's own live-retarget fallback
   branch (guarded `if not has_fresh_decision:`) never executes.

Both gaps independently and completely defeat COMB-304's own fix for any entity that reaches
"arrived at stale snapshot" state — which is exactly the state a `PURSUIT_ABANDONED`-bound chase
reaches before its leash/stalemate timeout eventually fires. This is the complete, previously-
unidentified mechanism producing the 100% `PURSUIT_ABANDONED` rate `TCK-20260809-COMBAT-KILL-
LIFECYCLE-CREDIT-GAP-INVESTIGATION` traced the COMBAT pillar's own unreachable positive-scoring
surface to.

## Scope
1. Fix both gaps with a single shared helper (avoid a third future drift point — this is the
   second time near-identical live-retargeting logic needed duplicating across call sites).
2. Re-verify the specific frozen pair no longer stays frozen forever.
3. Re-verify at the real, corpus-wide, decisive level: does `combat_resolved`/`entity_killed`/
   `combat_damage` now fire non-zero where it was exactly zero before (post-COMB-309 baseline)?
4. Full regression sweep given the changed files are core, shared engine dispatch paths.

## Out of Scope
- `NavigationSystem.get_next_step()`'s single-axis-priority stepping algorithm (never moves
  diagonally) — a real, disclosed, SEPARATE issue found during Verify (the specific traced pair
  still doesn't converge post-fix; it now oscillates in a stable mutual-orbit instead of freezing
  outright, a different bug in a different function). Not fixed here — left as a disclosed,
  candidate follow-up.
- Any further tuning of readiness/movement-cost values (already covered by prior same-day
  tickets).

## Acceptance Criteria
- [x] Root cause confirmed with direct evidence at both real gap sites (not assumed)
- [x] Cross-checked that the fix doesn't regress COMB-304's own already-passing test suite
- [x] Real fix lands: shared live-retargeting helper applied at all 4 real call sites
- [x] Re-verification: the specific frozen pair no longer freezes forever (moves, though a
      separate, disclosed oscillation issue remains for that specific geometry)
- [x] Real corpus-wide re-verification: `combat_resolved`/`entity_killed`/`combat_damage` move
      from exactly 0 to non-zero in both `dungeon_crawl` and `urban_political`
- [x] Scoped pytest passes (only the pre-existing, unrelated `test_normal_move_triggers_oa`
      failure remains, confirmed via bisection)
- [x] A real, independent regression surfaced during Test (a conflict between an earlier same-
      session fix's own reset behavior and 2 integration tests) is investigated and correctly
      resolved, not just patched around

## Related Tickets
- TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION (this session, immediately prior —
  the ticket whose own disclosed `PURSUIT_ABANDONED`-dominance finding motivated this investigation)
- TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE (COMB-304, same-day, prior — the fix this ticket
  found 2 real gaps in; NOT reverted or contradicted, only extended to the 2 places its own scope
  didn't reach)
- TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE (same-day, prior — the original
  investigation that led to COMB-304)
- TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION,
  TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE (same-day, prior — pushed the real
  attack-legal rate from 0% to 28.5%/36.6%; this ticket explains why that improvement alone still
  didn't unblock real combat resolution for pursuits that reach "arrived at stale snapshot")
- TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET (earlier this session — the ticket whose own
  reset-to-idle fix's real conflict with 2 integration tests was found and correctly resolved
  during this ticket's own Test phase)

## Related Docs
- `docs/engine/contracts/tactical_contract.md` §3 (Engagement & Pursuit Rules — updated)
- `docs/engine/candidate_selection.md` Tier 3 (Movement Candidate Selection — updated)
- `docs/guidelines/intentional_divergences.md` §2.36-2.38 (the prior same-day findings this
  ticket builds directly on)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS/`

## Related Code Areas
- `src/engine/candidate_selector.py` (`MovementCandidateSelector.select()`, new shared
  `resolve_live_tracking_target()` helper)
- `src/engine/pipeline_phases/movement.py` (`MovementPhase.route_movement_intent()`, now calling
  the shared helper instead of its own duplicate inline logic)
- `src/engine/executor.py` (`LocalSequentialExecutor.execute()`'s `ENTITY_MOVE` branch)
- `src/engine/worker_logic.py` (`default_simulation_worker`'s `ENTITY_MOVE` branch)
- `src/engine/pipeline_phases/actions.py` (`ActionRoutingPhase.route()` — the real regression fix,
  reverted to the original, corpus-verified `payload_set={}` behavior)
- `src/systems/world_systems/navigation.py` (`NavigationSystem.get_next_step()` — the disclosed,
  out-of-scope single-axis-stepping issue found during Verify)

## Assumptions / Open Questions
- Whether the mutual-orbit oscillation found during Verify (a separate issue from this ticket's
  own fix) is common enough in the real corpus to be worth its own follow-up investigation — not
  measured at corpus scale here; disclosed as a real, confirmed-to-exist, unscoped lead.

## Implementation Notes
Root cause confirmed via 3 layers of direct instrumentation (see Request Summary for the full
trace). Fix: extracted the live-retargeting logic (originally only in `route_movement_intent`,
per COMB-304) into `MovementCandidateSelector.resolve_live_tracking_target(entity, entities,
fallback_target)` — a static helper taking a plain `{entity_id: EntityState}` mapping (not a full
state/packet object), so it works identically against `AuthoritativeState.entities`,
`WorkerPacket.all_entities`, and `readonly_state.entities` without threading a wider dependency
through the bounded, read-only `WorkerPacket` context. Applied at all 4 real call sites:
`MovementCandidateSelector.select()`'s own nav_target fallback, `route_movement_intent()` (now
calling the shared helper instead of its own inline duplicate), `LocalSequentialExecutor.execute()`,
and `default_simulation_worker`.

While verifying, discovered a real, independent regression: `ActionRoutingPhase.route()`'s
`is_unrecoverable_attack_failure` reset (`payload_set={}}`, added by this session's earlier
`TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET`) conflicts with 2 pre-existing integration
tests (`test_pipeline_simultaneous_attack_atomicity`, `test_aoe_sliding_state_awareness`) that
expected `outcome`/`reason` to survive in the same tick's own returned payload for atomic-ordering
visibility — a real gap that ticket's own test scope (only `tests/unit/actions/`) never caught.
First attempted preserving `outcome`/`reason` in the reset payload; live corpus re-verification
showed this reintroduces a partial version of the ORIGINAL stuck-retry bug (one entity hit
`TARGET_INCAPACITATED` 73 times in a 2000-tick run — `scheduler.py`'s own `is_idle_act` check
requires a genuinely falsy/empty payload, not merely an action/target_id-less one). Reverted to
the original, corpus-verified `payload_set={}` behavior (0 repeats, confirmed) and updated the 2
stale integration tests instead, since no real production code (confirmed via grep) reads
`task.payload.get("outcome")` — only these 2 tests' own assertions did.

**Verify — a real, disclosed, separate remaining issue found**: post-fix, the specific traced
pair (entities 25/12) no longer freezes, but enters a stable mutual-orbit oscillation — both
entities swap which diagonal corner they occupy each tick, recomputing a fresh "step toward the
other's live position" every time, but never closing the gap. Traced to
`NavigationSystem.get_next_step()`'s own single-axis-priority stepping (moves only one axis per
tick, never diagonally) — a separate, real bug in a different function, not something this
ticket's own retargeting fix touches. Disclosed, not chased (out of scope).

## Test Summary
4 new tests in `tests/unit/optimization/test_movement_candidate_selector.py`, all confirmed via
git-stash bisection to genuinely fail pre-fix (3 with `AttributeError` since the shared helper
doesn't exist pre-fix, 1 — the exact candidacy-exclusion scenario — with the real confirmed bug).
2 pre-existing integration tests updated to match the correct, already-established, corpus-
verified reset behavior (not the fix's own new behavior — see Implementation Notes). Full scoped
re-run: `tests/unit/optimization/`, `tests/unit/movement/`, `tests/unit/combat/`,
`tests/unit/tactical/`, `tests/unit/kernel/`, `tests/unit/core/`, `tests/unit/engine/`,
`tests/unit/actions/`, `tests/unit/strategic/`, `tests/unit/observability/`,
`tests/unit/entities/`, `tests/integration/combat/`, `tests/integration/pipeline/` — 2047 passed,
only the 1 pre-existing, already-confirmed-unrelated failure
(`test_normal_move_triggers_oa`, re-confirmed via bisection on this ticket's own diff too).
`tests/integration/kernel/test_determinism_suite.py`, `test_seed_stability.py`,
`test_authoritative_outcome_truth.py` — 9 passed, no determinism regressions.
`test_long_run_determinism.py::test_1000_tick_determinism` hit a pre-existing, unrelated 60s CI
resource-timeout (confirmed identical on pristine pre-fix code via bisection), matching the
already-disclosed chronic tick-budget-exceeded finding from COMB-308.

Real corpus re-verification (`tools.calibrate_simq`-equivalent direct `Kernel.tick_once()` loop,
2000 ticks, corpus-default flags): `dungeon_crawl` combat event counts moved from
`{combat_engagement_ended: 10}` only (post-COMB-309 baseline, 100% PURSUIT_ABANDONED) to
`{combat_engagement_ended: 11, combat_initiated: 1, combat_engagement_started: 1, combat_damage:
1, entity_killed: 1, combat_resolved: 1}`; `urban_political` moved from `{combat_engagement_ended:
15}` only to `{combat_engagement_ended: 15, combat_resolved: 5}`. COMBAT pillar norm on
`dungeon_crawl_seed42_2000t` moved from exactly 0.0 (COMB-309's own post-fix baseline) to
-0.0096 with 6 real events — grade stayed C (a small, real, honest change at this corpus's own
low combat-volume scale).

## Files Changed
- `src/engine/candidate_selector.py` — new shared `resolve_live_tracking_target()` helper;
  `select()`'s own nav_target fallback now uses it
- `src/engine/pipeline_phases/movement.py` — `route_movement_intent()` now calls the shared
  helper instead of its own duplicate inline logic
- `src/engine/executor.py` — `ENTITY_MOVE` branch live-retargets via the shared helper
- `src/engine/worker_logic.py` — `ENTITY_MOVE` branch live-retargets via the shared helper
- `src/engine/pipeline_phases/actions.py` — reverted an attempted mid-fix change back to the
  original, corpus-verified `payload_set={}` reset behavior (see Implementation Notes)
- `tests/unit/optimization/test_movement_candidate_selector.py` — 4 new tests
- `tests/integration/pipeline/test_combat_legality_matrix.py` — 2 tests updated to match the
  correct, already-established reset behavior
- `docs/engine/contracts/tactical_contract.md` §3 — updated Pursuit rule description
- `docs/engine/candidate_selection.md` Tier 3 — documented the live-retarget refresh
- `docs/parity_ledger/combat_movement.yaml` — COMB-310 (full fix + regression investigation)
- `docs/parity_ledger/substrate.yaml` — SUB-383 (executor.py's own real parity subsystem)

## Completion Summary
Continued the user's own "why does combat rarely resolve" investigation thread past 6 same-day
tickets that had already made real, substantial progress (readiness regen, movement/readiness
decouple, live per-tick pursuit retargeting) but left `PURSUIT_ABANDONED` at 100% unexplained.
Found the real, complete, previously-unidentified cause: the most recent prior fix
(`TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE`) was itself correct but incomplete — 2 other real,
independent places computed their own separate, un-refreshed "is this stale" logic, both of which
silently prevented that fix from ever engaging for a genuinely stuck pursuit. Fixed both by
extracting the live-retargeting logic into one shared helper applied at all 4 real call sites,
closing a class of bug (duplicate staleness logic drifting out of sync) that had already caused
one real regression (COMB-304's own incomplete coverage) before this ticket even started.

Along the way, found and correctly resolved a real, independent regression in an earlier
same-session fix (traced why a "quick" preservation attempt reintroduced a partial version of the
original bug, verified via live corpus data, then chose the architecturally correct resolution —
updating 2 stale tests rather than compromising the already-verified-correct production behavior).

Real, corpus-wide, decisive verification: combat events that were exactly zero (`combat_resolved`,
`entity_killed`, `combat_damage`) in a fresh, correctly-measured baseline now fire non-zero in
both worlds — the first real movement past "zero credited combat activity" this session's own
COMBAT-pillar investigation chain achieved. Honestly disclosed, not chased: a real, separate,
different-mechanism issue (single-axis-priority stepping causing a mutual-orbit oscillation for
some pursuit geometries) remains as a candidate follow-up for the user's next direction.
