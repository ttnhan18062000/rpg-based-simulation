---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260824-TOWN-CENTER-POINTER-FIX
phase: done
date: 2026-08-24
tags: [world, determinism]
---

# TCK-20260824-TOWN-CENTER-POINTER-FIX

## Title
Fix the town_center Pointer Bug and Its Related Consumers

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
The original town_center pointer bug is confirmed, and deeper investigation found it worse than reported: two more broken consumers (FlowFieldService, a second parallel town_center field on the worker-protocol dataclass), plus a subtler bug where fallback consumers pick an arbitrary tile across every town in the world, not the nearest one. The author wants all of this fixed.

## Scope
- Fix WorldCompiler.compile() so it sets AuthoritativeState.town_center to a real value derived from the compiled town-type region(s), instead of leaving it at default (0,0) for every real generated world
- Fix FlowFieldService.get_flow_direction(target_kind='TOWN',...) to return direction toward the real town location instead of hardcoded ANCHORS waypoints
- Resolve WorkerPacket.town_center's dead-duplicate-state status -- give it a real consumer or remove it
- Fix StrategicRedirectionSystem.enforce() and StrategicIntelligenceSystem's routine-blocker pass to compute the tile nearest to the requesting entity, instead of an arbitrary sorted/iter pick
- Decide, and document, whether town_center should be deprecated in favor of a proper nearest-town lookup (given world composition supports multiple town-type regions) or kept single-value for worlds that today only generate one town

## Out of Scope
- Idea 56 (Drifting Loyalty)'s City-to-capital political distance measure -- confirmed no shared code path, would not consume this fix
- Hardening intelligence.py's next(iter(state.town_tiles)) determinism concern beyond what's needed for the nearest-tile fix, unless it's found to be part of the same fallback bug

## Acceptance Criteria
- [x] WorldCompiler.compile() sets AuthoritativeState.town_center to a real value derived from the compiled town-type region(s), not left at default (0,0)
- [x] FlowFieldService.get_flow_direction(target_kind='TOWN',...) returns direction toward the real town location, not hardcoded ANCHORS waypoints
- [x] WorkerPacket.town_center gains a real consumer or is removed as dead duplicate state
- [x] StrategicRedirectionSystem.enforce() and StrategicIntelligenceSystem's routine-blocker pass compute the tile nearest to the requesting entity, not an arbitrary sorted/iter pick

## Related Tickets
- TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/core/worker_protocol.py
- src/engine/executor.py
- src/engine/apply.py
- src/engine/checkpoint.py
- src/engine/scheduler.py
- src/worldbuilding/compiler.py
- src/worldassembly/resolver.py
- src/worldgeneration/generator.py
- src/systems/world_systems/navigation.py
- src/systems/strategic_systems/redirection.py
- src/systems/strategic_systems/intelligence.py
- src/town/town_navigation.py
- src/town/home_storage.py
- src/ai/goals/scorers.py
- src/ai/goals/adventure_scorer.py
- src/engine/tactical.py

## Assumptions / Open Questions
- Whether to deprecate town_center for a proper nearest-town lookup or keep it single-value (since worlds today only generate one town) is a real design decision this ticket must make explicit
- Fixing the WorldCompiler root cause may transitively fix every other direct consumer (town_navigation.py, home_storage.py, scheduler.py, scorers.py, adventure_scorer.py, tactical.py's TOWN_RETURN path), not just the 3 consumers named in the original concern -- investigate and confirm during implementation
- **RESOLVED, design decision confirmed during Implement**: plan.md's Design Decision (keep `town_center` single-valued, computed as the first town-type region's own bounds centroid) was implemented as specified — no deprecation, no new lookup registry.
- **NEW, blocking finding surfaced during Implement (see Implementation Notes)**: the Step 1 + Step 2 fix (real `town_center` + `FlowFieldService` actually navigating to it) causes 13 real, reproducible test failures in `tests/unit/worldassembly/test_corpus_diversity.py` (population-stability and simulation-quality-grade-stability tests spanning most of the world-composition corpus, not just `urban_political`). Confirmed via git-stash bisection to be caused by this ticket's own code change, not environment flakiness. This needs an explicit decision (accept as an intended behavior change requiring baseline/threshold updates in a follow-up step, vs. reconsider the fix) before this ticket can be verified/finalized — flagged for the next phase (Architecture-Review / Parity / Verify), not resolved by the Implementer.

## Implementation Notes

**Steps 1-4 implemented exactly per `staging_artifacts/TCK-20260824-TOWN-CENTER-POINTER-FIX/plan.md`:**

- **Step 1** (`src/worldbuilding/compiler.py`): after the existing region-compilation loop, added a
  new block ("2a") that scans `spec.regions` in declaration order for the first `r_spec.type ==
  "town"` and computes `town_center` as that region's own bounds centroid
  (`((min_x+max_x)/2.0, (min_y+max_y)/2.0)`). Passed into the `AuthoritativeState(...)` constructor
  call as `town_center=town_center if town_center is not None else (0.0, 0.0)`. No RNG draw
  introduced; pure arithmetic on already-deterministic `bounds`.
- **Step 2** (`src/systems/world_systems/navigation.py`): `FlowFieldService.get_flow_direction()`
  now special-cases `target_kind == "TOWN"` at the top to set `anchors = [state.town_center]`
  unconditionally, bypassing the hardcoded `ANCHORS["TOWN"]` two-waypoint list entirely.
  `ANCHORS["WORLD_BOSS"]` and its dynamic-entity fallback path are untouched, exactly as scoped.
- **Step 3** (`src/core/worker_protocol.py`, `src/engine/executor.py`): removed the
  `WorkerPacket.town_center` field declaration and its sole producer keyword argument in
  `executor.py`'s `WorkerPacket(...)` construction. Confirmed (as the plan predicted) that none of
  the 9 test files constructing `WorkerPacket(...)` directly pass `town_center=` explicitly — no
  test fixture needed updating.
- **Step 4** (new `src/systems/strategic_systems/town_targeting.py`,
  `src/systems/strategic_systems/redirection.py`, `src/systems/strategic_systems/intelligence.py`):
  added the shared pure `nearest_town_tile(town_tiles, position)` helper exactly per plan's
  signature and tie-break (`(dist_sq, x, y)` via `min()`). `redirection.py`'s
  `StrategicRedirectionSystem.enforce()` now computes the nearest tile inside the per-entity loop at
  the "Case 3: Return to Town" fallback (`target_coords = nearest if nearest is not None else
  state.town_center`), replacing the old once-per-tick `sorted(list(state.town_tiles))[0]`
  precompute. `intelligence.py`'s `fused_strategic_pass()` — the real, hoisted, live entry point
  wired at `src/engine/pipeline.py:333` (confirmed by the pre-existing in-code comment "Hoisted logic
  from StrategicRedirectionSystem") — was updated at both of its structurally-identical
  "has-items, return to town" fallback blocks to compute `nearest_town_tile(state.town_tiles,
  entity.navigation.position) or state.town_center` per entity, replacing the old
  `next(iter(state.town_tiles))` once-per-tick precompute.

**Deviation from plan (documented per CLAUDE.md, not silent) — pre-existing latent bug fixed in
`redirection.py`**: while writing the required `test_redirection_enforce_targets_nearest_town_tile_not_arbitrary_sort`
test, discovered `StrategicRedirectionSystem.enforce()`'s default-parameter expression
(`cadence = cadence or SystemCadence()`) raised `NameError: name 'SystemCadence' is not defined` —
`SystemCadence` was referenced only in a lazily-evaluated (`from __future__ import annotations`)
type hint, never actually imported at module scope, only imported locally inside the function body
under a different name (`should_run`). This is a pre-existing bug independent of this ticket's own
logic change (confirmed via git-stash: the line was unmodified by my edits and the bug reproduces on
unmodified `enforce()` calls too). Also discovered via `grep -rn "StrategicRedirectionSystem"
src/engine/` that `enforce()` has **zero callers anywhere in `src/`** — its logic was fully
"hoisted" into `intelligence.py`'s `fused_strategic_pass()` (per that file's own comment at the
hoist site), so `enforce()` is dead in production but remains part of the public API surface
(re-exported via `src/systems/redirection.py`, asserted importable by
`tests/refactor/test_import_compatibility.py` and `tests/refactor/test_public_facades.py`). Since
this ticket's own approved plan explicitly requires `enforce()` to compute nearest-tile correctly
(named directly in the ticket's AC and Step 4's Verify section) and this bug otherwise makes it
impossible to call `enforce()` at all without an explicit `cadence=` argument, added the missing
top-level `from src.engine.cadence import SystemCadence` import to `redirection.py`. This is a
minimal, one-line, obviously-correct fix in a file Step 4 already touches; no other code or
behavior in this file changed beyond what Step 4's plan specifies.

**Step 6**: added the required integration test
(`test_town_return_navigates_to_real_compiled_town_center`, in
`tests/unit/strategic/test_expanded_goals.py` alongside the existing precedent test, per the plan's
either/or) — compiles a real `WorldSpec` via `WorldCompiler.compile()` (not a hand-built
`AuthoritativeState` with an explicit `town_center=(0.0,0.0)` fixture) and asserts the full chain
`WorldCompiler.compile()` -> `TownScorer`/`evaluate_strategic_intent()` ->
`TacticalDecisionSystem.evaluate_entity_intent()` produces a `NavigationUpdate` toward the real
compiled town location. Passes.

**Step 6 baseline spot-check results (ran, manually diffed — did not blindly re-run or touch any
baseline file, per the Anti-Drift Test Guards and Gate Integrity rule):**

- `tests/regression/test_behavioral_5k.py`: **inconclusive in this environment** — fails with
  `TimeoutError: Test execution exceeded the resource time limit.` (`tests/conftest.py:68`'s own
  resource-time-limit guard, not an assertion failure) both with my changes applied AND on
  unmodified baseline code (verified via `git stash` bisection) — this machine is CPU-constrained
  (4 cores, several concurrent Claude/Codex sessions running) and this specific 5000-tick-scale test
  cannot complete within the harness's time budget here regardless of code changes. Not a real
  signal either way; matches the project's documented environment-dependent-flake category.
- `tests/simulation_quality/test_grade_regression.py -m "not slow"`: 7 passed, 64 skipped (missing
  `data/calibration/*/quality_report.json` fixtures not present in this environment — generated by a
  separate, out-of-scope process), 18 deselected (slow marker). No failures among tests that
  actually ran.
- **`tests/unit/worldassembly/test_corpus_diversity.py` (part of test_plan.md's own required
  "Regression Surface", not one of the two named baseline files but exercises the same real-compiled
  multi-world corpus): 13 FAILED, 1 ERROR, 221 passed.** Bisected with `git stash` (isolating exactly
  which of my changes causes it): **Step 1 alone (compiler.py only) — test passes.** **Step 1 + Step
  2 together (compiler.py + navigation.py) — test fails, identically to the full changeset.**
  Confirmed via a fast, non-timeout, deterministic (seed=42) assertion failure — e.g.
  `test_population_stability[highland_traverse]`: passes on baseline in 5.47s, fails with Step
  1+2 in 3.40s at tick 150 with `alive=10/18 (55.6%)` vs a 60% floor. The failing test list spans
  most of the world-composition corpus (`highland_traverse`, `frontier_marches`,
  `generated_frontier_3_42`, `simq_routing_test`, `hero_guild_routing`, `unit_selfmodel_pilot`,
  `urban_political` x3, `frontier_living_world` x2), not only `urban_political`. Root mechanism:
  before this ticket, entities being routed to "return to town" were navigating toward either an
  arbitrary real town tile (`redirection.py`'s old `sorted()[0]` pick) or, via
  `FlowFieldService`, two hardcoded fake waypoints `(100,100)`/`(200,50)` — never the real compiled
  town location. Fixing the pointer (this ticket's entire purpose) means entities now travel to a
  different, correct destination, which changes their combat/hazard exposure along the way in
  several world compositions enough to trip the existing hardcoded 60%-alive population floor and
  simulation-quality grade-stability thresholds. This is very plausibly the *intended* consequence of
  fixing a real navigation bug (the old "passing" state was itself an artifact of the bug, not
  evidence of correct balance) — but it is a materially larger blast radius than plan.md's Step 6
  anticipated (which named only the two `urban_political`-tied baseline files), and per CLAUDE.md's
  Gate Integrity rule I have not touched these tests, their thresholds, or any baseline data to force
  them green. **This is reported here as a blocking finding for the next phase to make an explicit
  call on** (accept as intended and re-baseline these floor/threshold values with a documented
  rationale, vs. reconsider Step 2's FlowFieldService change) — not something I resolved unilaterally
  as Implementer.
- The 1 ERROR (`tests/unit/worldassembly/test_resolver.py::test_resolve_module_contribution_rejects_raw_spec`)
  passes cleanly in isolation — appears to be a pre-existing test-ordering/shared-state artifact of
  running the full `test_corpus_diversity.py` batch together, unrelated to `town_center`; not
  investigated further given it reproduces regardless of this ticket's changes.
- `tests/integration/kernel/test_long_run_determinism.py::test_1000_tick_determinism`: also fails
  with the same `TimeoutError` resource-limit signature (not an assertion failure) — matches a
  previously-known, already-documented, deliberately-deferred issue (kernel's wall-clock mid-tick
  throttle breaking under CPU contention), unrelated to this ticket.

**All other test_plan.md-scoped regression-surface commands passed cleanly**: `tests/unit/worldbuilding/`
(43 passed), `tests/unit/worldgeneration/` + `tests/unit/worldassembly/` minus the corpus-diversity
finding above (all structural/compilation/assembly tests pass, including the load-bearing
`tests/integration/worldassembly/test_real_content_world_compositions.py`, 13 passed, and the full
`tests/integration/worldassembly/`, 53 passed), `tests/unit/movement/` + `tests/perf/test_lod.py`
(53 passed), `tests/unit/strategic/` + `tests/unit/tactical/` + `tests/unit/ai/goals/` (327 passed,
includes the 5 new Step 4 tests), `tests/unit/world/test_home_storage.py` +
`tests/unit/world/test_town_building_contract.py` (6 passed, unaffected by the compiler fix exactly
as plan.md's Anti-Drift Notes predicted), `tests/unit/kernel/` + `tests/unit/core/test_engine_integrity.py`
(68 passed, includes the new Step 3 architecture guard), `tests/integration/kernel/` (94 passed, 1
environment-timeout failure noted above).

## Post-Implement Pipeline Resumption (2026-08-28, resumed session after prior session interruption)

Resumed from an interrupted hand-orchestration session. Verified via real diffs/artifacts (not
assumed) that the following phases were already genuinely complete: **Plan** (revised — SUB-014
gap fixed per the "RESOLVED" note above), **Review** (re-approved), **Implement** (Steps 1-4, diff
matches plan.md exactly), **Document-Update** (`docs/mechanics/06_worldbuilding_foundation.md`,
`docs/world/compiler_contract.md`, `docs/engine/contracts/tactical_contract.md` all real-diffed and
consistent with plan Step 5's Mechanics-Bible/compiler-contract portions). Catch-up monitoring
events were written for these phases (seq 5-8) since the crashed session never reached its own
`writeMonitoring` call.

Ran fresh, for real, in this session:
- **Doc-staleness gate**: PASS (3 docs/ paths present alongside the 7 flagged src/ paths).
- **Architecture-Verify**: APPROVED (architecture-reviewer agent, both the deterministic static
  checks — 14/14 PASS — and live judgment; diff matches plan.md Steps 1-4, `nearest_town_tile()`
  confirmed pure/read-only, deviations faithfully disclosed).
- **Test**: scoped pytest run across every domain named in test_plan.md's Scoped Pytest Commands
  (compiler/worldgen/worldassembly, movement/perf, strategic/tactical/ai-goals, world services,
  kernel/integration-kernel/core, integration/worldassembly) — **822 tests passed**, plus a real
  determinism suite (`test_bit_identical_determinism`, `test_determinism_same_seed_same_hash`,
  `test_reproducibility`, `test_compiler_terrain_variants_deterministic_same_seed`, and the full
  `test_phase2_determinism.py` RNG-boundary suite, all passing). `tests/unit/worldassembly/
  test_corpus_diversity.py` was independently re-run in isolation and **still shows the exact
  disclosed regression** (13 failed + 1 error — same test names as the Implementation Notes above),
  confirming this was not an artifact of the crashed session's own environment. The 1 error
  (`test_trading_company_hub_composed[swamp_border_world]`) is a session-scoped
  `QueueDrainWorker` thread-leak teardown check (`tests/conftest.py:213`) attributable to whichever
  test runs last in the batch — same disclosed "pre-existing test-ordering/shared-state artifact"
  category as before, just attached to a different final test name when run standalone.
  `tests/regression/test_behavioral_5k.py` and `test_1000_tick_determinism` were not re-attempted
  (previously confirmed environment-timeout, unrelated to this ticket's code).
- **Environment note**: mid-Test-phase, the shared host's root filesystem hit 100% full (0 bytes
  free), unrelated to this ticket. Resolved twice via the project's own sanctioned mtime-gated
  `clean_data_runs_early()` cleanup (never a blind `rm`), reclaiming leftover `data/runs/`
  simulation artifacts from concurrent test runs. Also found and surgically repaired one
  interleaved (non-newline-separated) corrupted line in `agent-monitoring/tools.jsonl` caused by a
  concurrent-write race between this session and a background sub-agent — split back into its two
  original valid JSON records, no data invented beyond closing the first record's already-complete
  fields; verified round-trip well-formed with `json.loads` afterward.

**Per CLAUDE.md's Gate Integrity rule, the Test gate's real result (13 failed + 1 error, real and
reproducible, not new) was reported as blocking rather than routed around.** This was the exact
disclosed, unresolved decision plan.md's own Deviations section flagged for "the next phase
(Architecture-Review / Parity / Verify) to decide: accept as intended and re-baseline the affected
floors/thresholds with a documented rationale, or reconsider the scope/sequencing of Step 2's
FlowFieldService change." **Pipeline halted at that point with status TESTS_FAILED.**

## Human Decision and Pipeline Resumption (2026-08-28, continuation session)

**The human decision has now been made: accept the `test_corpus_diversity.py` regression as this
ticket's intended, correct consequence.** Rationale: the pre-fix "passing" state of these 13 tests
was itself an artifact of the pointer bug this ticket exists to fix — entities either navigated to
an arbitrary real town tile (the old `sorted()[0]`/`next(iter())` picks) or to two hardcoded fake
waypoints, never the real compiled town center. That was never evidence of genuine population/
quality-grade balance under correct navigation; it was a stale threshold computed against buggy
behavior. Reconsidering/rolling back Step 2 to keep these floors green would mean shipping the fix
with entities still not actually navigating to town, defeating the ticket's purpose. Full rationale
recorded in `staging_artifacts/TCK-20260824-TOWN-CENTER-POINTER-FIX/plan.md`'s Deviations item 3.

Per `docs/testing/regression_policy.md`'s documented pattern for "a hardcoded test baseline that this
session's own legitimate change caused to drift" (a small hotfix ticket re-baselining with fresh
evidence, never a silent edit outside a ticket), this ticket closes with the regression genuinely
disclosed (not routed around) below, and a separate follow-up ticket,
`TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`, is filed at `tickets/todos/` (filed,
not implemented, in this same session) to re-baseline the affected floors using the now-correct
navigation behavior as fresh ground truth.

**Re-verification of the current test state (this session, not trusted blindly from the prior
session's numbers):** re-ran test_plan.md's own "World compilation / generation" scoped command
(`pytest tests/unit/worldbuilding/test_world_compiler.py tests/unit/worldgeneration/
tests/unit/worldassembly/ -q`, which bundles `test_corpus_diversity.py` with the rest of
`tests/unit/worldassembly/` — the actual defined scope, not an invented one) and confirmed **13
failed, 221 passed, 1 error** — an exact match to the previously disclosed count and (with one
immaterial exception) the same test names. The 1 ERROR landed on
`test_resolver.py::test_resolve_module_contribution_rejects_raw_spec` this run (vs.
`test_trading_company_hub_composed[swamp_border_world]` previously) — confirmed to be the same
"whichever test runs last in the batch" test-ordering/shared-state artifact already disclosed, not a
new failure mode (a standalone `test_corpus_diversity.py`-only run, done as an extra cross-check
outside test_plan.md's actual scope, showed additional order-dependent flakiness — 16F+1E — that is
informational only and does not change the Test gate determination, since test_plan.md's own scoped
command is the authoritative surface).

All other test_plan.md-scoped groups re-verified and matched the prior session's counts exactly:
navigation/movement 53 passed; strategic/tactical/ai-goals 327 passed; town/world services 6 passed;
worker-protocol/kernel/integration-kernel/core 162 passed + 1 failed (`test_1000_tick_determinism`,
same pre-existing documented `TimeoutError` resource-time-limit environment signature under CPU
contention — not a new regression); worldassembly integration 53 passed. Combined: **822 tests
passing** outside the one disclosed, accepted exception — identical total to the prior session.

Repo state confirmed clean: `agent-monitoring/{tools,events,runs}.jsonl` all parse as valid
newline-delimited JSON (the prior session's corrupted-line repair held); disk usage checked (2.6G
free at session start) and monitoring stayed well within bounds throughout this session's test runs.

**The Test gate is now treated as cleared**: the disclosed 13F+1E in `test_corpus_diversity.py` is an
accepted, documented exception per the human decision above, not a blocking failure. Proceeding to
Parity, Security-Review (conditional), Verify, and Finalize.

## Test Summary

New tests added (all passing): `test_compile_sets_real_town_center_from_town_region`,
`test_compile_town_center_derivation_with_multiple_town_regions`
(`tests/unit/worldbuilding/test_world_compiler.py`);
`test_get_flow_direction_town_uses_real_town_center_not_hardcoded_anchor`
(`tests/unit/movement/test_flow_field_navigation.py`);
`test_worker_packet_has_no_dead_town_center_field` (new file
`tests/unit/kernel/test_worker_protocol.py`);
`test_redirection_enforce_targets_nearest_town_tile_not_arbitrary_sort` (new file
`tests/unit/strategic/test_redirection.py`);
`test_routine_blocker_pass_targets_nearest_town_tile_not_arbitrary_iter`,
`test_redirection_and_routine_blocker_single_town_world_unaffected` (new file
`tests/unit/strategic/test_intelligence_routine_blockers.py`);
`test_town_return_navigates_to_real_compiled_town_center`
(`tests/unit/strategic/test_expanded_goals.py`). Regression-surface results and the
`test_corpus_diversity.py` finding are detailed in Implementation Notes above.

**Disclosed, accepted regression (not hidden)**: `tests/unit/worldassembly/test_corpus_diversity.py`
fails 13 tests + 1 error (population-stability and simulation-quality-grade-stability floors,
re-verified exactly reproducing in the "Human Decision and Pipeline Resumption" section above) as a
direct, git-bisected consequence of this ticket's own Step 1+2 fix — entities now correctly navigate
to the real compiled town center instead of an arbitrary tile or hardcoded fake waypoints, which
changes combat/hazard exposure enough to trip several corpus worlds' hardcoded floors. **Human
decision: accepted as the fix's intended, correct consequence** (the pre-fix "passing" state was
itself an artifact of the bug being fixed, not evidence of real balance) — not silently routed
around. A separate follow-up ticket,
`TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`, is filed at `tickets/todos/` to
re-baseline the affected floors using the now-correct navigation as fresh ground truth, per
`docs/testing/regression_policy.md`'s documented drift-baseline pattern. All other test_plan.md-scoped
groups pass cleanly (822 tests total), plus the real determinism suite named in the prior session's
notes. `test_1000_tick_determinism`'s 1 failure is the separately pre-existing, already-documented
environment-timeout issue (kernel wall-clock throttle under CPU contention), unrelated to this
ticket.

## Files Changed

- `src/worldbuilding/compiler.py` (Step 1)
- `src/systems/world_systems/navigation.py` (Step 2)
- `src/core/worker_protocol.py` (Step 3)
- `src/engine/executor.py` (Step 3)
- `src/systems/strategic_systems/town_targeting.py` (Step 4, new)
- `src/systems/strategic_systems/redirection.py` (Step 4 + pre-existing `SystemCadence` import bug
  fix, see Implementation Notes)
- `src/systems/strategic_systems/intelligence.py` (Step 4)
- `tests/unit/worldbuilding/test_world_compiler.py` (Step 1 tests)
- `tests/unit/movement/test_flow_field_navigation.py` (Step 2 test)
- `tests/unit/kernel/test_worker_protocol.py` (Step 3 test, new file)
- `tests/unit/strategic/test_redirection.py` (Step 4 test, new file)
- `tests/unit/strategic/test_intelligence_routine_blockers.py` (Step 4 tests, new file)
- `tests/unit/strategic/test_expanded_goals.py` (Step 6 integration test)
- `docs/mechanics/06_worldbuilding_foundation.md` (Step 5, derivation rule + design rationale)
- `docs/world/compiler_contract.md` (Step 5, new "2a" compilation-sequence step)
- `docs/engine/contracts/tactical_contract.md` (Step 5, Section 7 real-value note)
- `docs/parity_ledger/substrate.yaml` (Step 5/Parity phase: new SUB-387 entry, updated SUB-014)
- `docs/parity_ledger/strategic_cognition.yaml` (Step 5/Parity phase: new STRAT-260 entry)
- `staging_artifacts/TCK-20260824-TOWN-CENTER-POINTER-FIX/plan.md` (Deviations section, 3 items)
- `tickets/inprogress/TCK-20260824-TOWN-CENTER-POINTER-FIX.md` (this file)
- `tickets/todos/TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH.md` (new follow-up
  ticket, filed not implemented)

## Completion Summary

Implemented Steps 1-4 of the approved plan: `WorldCompiler.compile()` now derives a real
`town_center` from the first town-type region's bounds centroid; `FlowFieldService` now navigates
to that real value instead of hardcoded fake waypoints; the dead-duplicate `WorkerPacket.town_center`
field was removed; and `StrategicRedirectionSystem.enforce()` / `StrategicIntelligenceSystem`'s
routine-blocker pass now compute the town tile nearest to each requesting entity via a new shared
`nearest_town_tile()` helper, instead of an arbitrary world-wide sorted/iter pick. Added all Step
1-4 and Step 6 unit/integration tests named in test_plan.md (all pass), fixed one pre-existing
unrelated `SystemCadence` import bug discovered in `redirection.py` while testing, and ran the full
test_plan.md regression surface (822 tests passing). Step 5 (doc/parity updates) was completed in
the pipeline-resumption session: `docs/mechanics/06_worldbuilding_foundation.md`,
`docs/world/compiler_contract.md`, and `docs/engine/contracts/tactical_contract.md` were updated with
the derivation rule and design rationale; `docs/parity_ledger/substrate.yaml` gained a new SUB-387
entry and had its pre-existing P0 SUB-014 entry's `v2_evidence`/`test_path` filled in with real
citations (closing a pre-existing null-test_path gap this ticket's own fix directly touches); and
`docs/parity_ledger/strategic_cognition.yaml` gained a new STRAT-260 entry cross-referencing the
unaffected STRAT-249.

**Disclosed regression and its resolution**: this fix produces a real, reproducible, git-bisected
regression in `tests/unit/worldassembly/test_corpus_diversity.py` (13 tests + 1 test-ordering-related
error, population/quality-grade stability across most of the world corpus) caused directly by this
fix correctly changing entity navigation targets — entities now travel to the real compiled town
center instead of an arbitrary tile or hardcoded fake waypoints, changing combat/hazard exposure
enough to trip several corpus worlds' hardcoded floors. **Human decision (2026-08-28): accepted as
the fix's intended, correct consequence** — the pre-fix "passing" state was itself an artifact of the
bug being fixed, not evidence of genuine balance. Re-verified independently in the pipeline-resumption
session (exact same 13F+1E reproduced via test_plan.md's own scoped command). Not routed around: the
regression is disclosed here and in Test Summary, and a separate follow-up ticket,
`TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH` (filed at `tickets/todos/`), tracks
re-baselining the affected floors using the now-correct navigation as fresh ground truth, per
`docs/testing/regression_policy.md`'s documented drift-baseline pattern. Steps 2, 3, 4 and 6's tests
were also verified consistent with plan.md's Determinism notes (no new RNG draws; deterministic
`min()`-based tie-breaks).
