---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY
phase: done
date: 2026-07-10
tags: [simulation-quality, calibration, determinism, corpus, investigation]
---

# TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY

## Title
Verify long-run (1000t/2000t) SimQ calibration anchor reliability against wall-clock throttle timing variance (SimQ Roadmap Phase 0.1)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`docs/audits/D06_longrun_health.md` F6 (added 2026-07-09, via `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`'s investigation) found that `src/engine/kernel.py`'s tick-budget watchdog (`kernel.py:420-442`) and mid-tick emergency throttle (`kernel.py:574-601`) measure real wall-clock compute time, not simulated ticks, and silently drop resolution-queue work when a tick's measured compute time exceeds budget. Two identical-seed, identical-code, back-to-back runs of `generated_frontier_3_42` diverged by 100+ ticks in floor-violation onset and more than 2x in the tick-1000 population endpoint (Run 1: 12/44 alive; Run 2: 5/44 alive), driven entirely by wall-clock scheduling/system-load timing, not the deterministic RNG seed. Every one of the 18 `SLOW_ANCHOR_KEYS` entries in `tests/simulation_quality/fixtures/grade_anchors.json` was captured from a **single** calibration run. This ticket is Phase 0.1 of `docs/plans/simq_development_roadmap.md` — the roadmap's first, blocking phase, since every later corpus-depth phase assumes existing long-run measurements are trustworthy. It is also tracked as P2-P in `docs/plans/audit_fix_plan.md`.

This is a **measurement-verification ticket**: determine which anchors are throttle-timing artifacts, document or convert the unreliable ones, and record a reliability status for all 18 keys. It does **not** change engine behavior.

## Scope
- For each of the 18 `SLOW_ANCHOR_KEYS` entries (`tests/simulation_quality/test_grade_regression.py:106-131`), re-run calibration 2-3 times at the same seed via `tools/calibrate_simq.py`, reusing the exact methodology documented in `stored_artifacts/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE/investigation.md` ("Method: direct instrumented drive... run twice, back to back, same seed, same code, same machine") — extended here to 2-3 re-runs per key rather than 2, and to per-pillar grade comparison rather than population-checkpoint comparison, since the object under test is grade stability, not population trajectory.
- The 18 keys span 8 worlds: `dungeon_crawl` (6 keys: seed42/123/456 @1000t, seed42/123/456 @2000t), `urban_political` (4: seed42/123/456 @1000t, seed42 @2000t), `sandbox_world` (2: seed42 @1000t/2000t), `unit_faction_tension` (2: seed42 @1000t/2000t), `unit_selfmodel_pilot`, `hero_guild_routing`, `simq_routing_test`, `generated_frontier_3_42` (1 each @1000t).
- For each key, classify per-pillar grade stability across re-runs:
  - **Stable** (all re-runs produce the same grade, or grades within the existing ±1-letter band tolerance already enforced by `test_grade_within_anchor_band_long_run`): add a one-line "re-verified stable across N re-runs" note to `docs/simulation_quality/eval_matrix_results.md` for that key.
  - **Unstable** (re-runs produce grades outside the ±1-letter band, or population/behavioral divergence consistent with the F6 mechanism): either (a) convert the anchor's regression check to a tolerance-based multi-trial guard, following the exact pattern of `test_generated_frontier_3_42_extended_population_stability` (`tests/unit/worldassembly/test_corpus_diversity.py:289-374`) — averaged floors across N trials rather than a single-run point comparison — or (b) if a tolerance-guard conversion is not a clean fit for that key/pillar, explicitly flag it in `eval_matrix_results.md` as carrying unquantified throttle-variance risk pending a follow-up decision.
- Update `eval_matrix_results.md` so every one of the 18 `SLOW_ANCHOR_KEYS` entries has one of exactly three documented reliability statuses: stable, converted-to-tolerance, or flagged-unverified.
- Run `make evaluate-full` (or equivalent full regression sweep) after any test/fixture changes to confirm 0 regressions.

## Out of Scope
- Any change to `src/engine/kernel.py`'s tick-budget watchdog or mid-tick emergency throttle logic, anywhere — this is documented, intentional engine behavior (`docs/engine/kernel.md` §"Emergency Throttling", `docs/engine/performance_contract.md` §7 "Adaptive Phase Budget Governor"). Confirming the throttle exists and causes variance is in scope; changing how it behaves is not.
- Phase 0.2 (`quality_scoring_contract.md` §12 Acceptance Criteria checklist closeout) — separate ticket per the roadmap, can run in parallel or either order.
- Phase 1.1 (P2-O, `hazard_kind` corpus-wide completeness test) and Phase 1.2 (P2-Q, `town_council`/`bandit_road` DA ruling) — separate, already-scoped backlog items; an orphaned empty `staging_artifacts/TCK-20260710-HAZARD-KIND-CORPUS-WIDE/` directory exists but has no corresponding ticket file yet, so there is nothing in progress to conflict with.
- The `moon_cave` missing-`hazard_kind` bug and the `town_council`/`bandit_road` unmitigated hazard exposure (Root causes 1 and 2 in the referenced investigation) — both are separate, already-identified content gaps tracked by P2-O/P2-Q, not part of this throttle-variance measurement ticket.
- Any FAST_ANCHOR_KEYS (200t/500t) entries — F6's divergence mechanism was only observed to matter past ~tick 300-320 (per the investigation's Root cause 3, watchdog first fired at tick 321 in both runs); fast anchors are out of scope unless re-run evidence unexpectedly shows otherwise, in which case that finding must be reported, not silently acted on.
- Expanding the calibration corpus (new worlds, new seeds, new pillars) — that is Phases 2-4 of the roadmap, explicitly gated on this ticket landing first.

## Acceptance Criteria
- All 18 `SLOW_ANCHOR_KEYS` entries have been re-run 2-3 times each at their existing seed via `tools/calibrate_simq.py`, using the same-machine, back-to-back methodology from the referenced investigation.
- `docs/simulation_quality/eval_matrix_results.md` documents a reliability status (stable / converted-to-tolerance / flagged-unverified) for every one of the 18 keys, each with cited re-run evidence (grades observed per trial, not just a conclusion).
- Every key classified "unstable" is either converted to a tolerance-based guard in `tests/unit/worldassembly/test_corpus_diversity.py` (or a documented reason why that pattern does not apply) or explicitly flagged as carrying unquantified throttle-variance risk in `eval_matrix_results.md`.
- `src/engine/kernel.py` has zero diff lines in this ticket's changes.
- `pytest tests/simulation_quality/test_grade_regression.py -m slow` and any newly added/modified tolerance-guard tests in `tests/unit/worldassembly/test_corpus_diversity.py` pass.
- `make evaluate-full` (or the equivalent scoped regression sweep) reports 0 regressions after all fixture/test changes land.
- No `docs/parity_ledger/` entry requires a status change, since no scored behavior changes as a result of this ticket (measurement methodology only) — if re-run evidence unexpectedly surfaces a genuine behavior divergence unrelated to throttle timing, that must be reported and filed as a separate follow-up ticket, not folded into this one.

## Related Tickets
- `docs/plans/simq_development_roadmap.md` Phase 0.1 — this ticket's direct source and scope definition.
- `docs/plans/audit_fix_plan.md` P2-P — same finding, backlog-tracked.
- `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE` (done) — discovered F6 and established both the instrumented-drive re-run methodology and the tolerance-based-guard pattern this ticket reuses at scale.
- `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS` (done) — established most of the current `SLOW_ANCHOR_KEYS` entries (`unit_selfmodel_pilot`, `hero_guild_routing`, `simq_routing_test`, `unit_faction_tension` x2, `urban_political_seed42_2000t`) being re-verified here.
- `TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS` (done) — established `generated_frontier_3_42`'s 1000t anchor, the anchor whose instability originally triggered the F6 discovery.
- `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` (referenced, not directly read this session) — the sibling investigation that independently found the same `town_council`/`bandit_road` question (P2-Q) later re-confirmed by the generated_frontier_3_42 investigation.
- Adjacent, not overlapping: an orphaned empty `staging_artifacts/TCK-20260710-HAZARD-KIND-CORPUS-WIDE/` directory exists with no ticket file — likely Phase 1.1 (P2-O) staged but not yet started; flagged for visibility, not a blocker.

## Related Docs
- `docs/plans/simq_development_roadmap.md` §Phase 0 — Reliability Foundation, §0.1 (this ticket's exact scope and acceptance signal).
- `docs/plans/audit_fix_plan.md` P2-P (full finding detail, files, fix options).
- `docs/audits/D06_longrun_health.md` F6 — "Wall-Clock-Dependent Non-Determinism at Long Tick Counts (Tick-Budget Throttle)".
- `docs/engine/kernel.md` §"Emergency Throttling" (lines 66-70) — the documented, intentional engine behavior causing the variance; explicitly out of scope to change.
- `docs/engine/kernel.md` §"State Hashing in Phase 7" — DEGRADED mode is not a complete determinism-proof state (canonical hash SKIPPED); relevant context for why the throttle-driven divergence isn't caught by hash-based determinism checks.
- `docs/engine/performance_contract.md` §7 "Adaptive Phase Budget Governor" — the broader governor mechanism the tick-budget watchdog is part of.
- `docs/engine/known_limitations.md` — mode-by-mode table for replay/hash availability under DEGRADED mode.
- `docs/simulation_quality/eval_matrix_results.md` — target file for all reliability-status documentation produced by this ticket.
- `docs/simulation_quality/quality_scoring_contract.md` — governing SimQ contract (goals, non-goals) this roadmap phase serves.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE/investigation.md` — read in full this session. Contains the exact "direct instrumented drive, densified across the 700-1000 window, run twice" methodology (Method section, lines 15-24) this ticket reuses at scale across all 18 `SLOW_ANCHOR_KEYS`, plus the full Root cause 1/2/3 analysis and the two-run divergence data (Run 1 vs Run 2 checkpoint tables) that is this ticket's evidentiary basis.
- `stored_artifacts/TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS/` — prior long-run anchor methodology and rationale for the anchors it added.
- `stored_artifacts/TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS/` — prior baseline/1000t anchor methodology for `generated_frontier_3_42`.

## Related Code Areas
- `tests/simulation_quality/test_grade_regression.py` — `SLOW_ANCHOR_KEYS` (lines 106-131), `test_grade_within_anchor_band_long_run` (lines 219-248); the existing ±1-letter band tolerance this ticket's "stable" classification relies on.
- `tests/simulation_quality/fixtures/grade_anchors.json` — the committed anchor fixture; no changes expected unless a genuine (non-throttle) drift is found, which would be a separate follow-up.
- `tests/unit/worldassembly/test_corpus_diversity.py` — `test_generated_frontier_3_42_extended_population_stability` (lines 289-374), the tolerance-based-guard pattern to reuse for any key classified unstable.
- `tools/calibrate_simq.py` — the calibration runner used for all re-runs (`--ticks`, `--seed`, `--name`, `--profile` args already support the required same-seed re-run workflow).
- `src/engine/kernel.py` — `_tick_once_inner`, end-of-tick watchdog (`kernel.py:420-442`), mid-tick emergency throttle (`kernel.py:574-601`) — read-only reference for understanding the mechanism; no edits.
- `docs/simulation_quality/eval_matrix_results.md` — documentation target for all 18 keys' reliability status.

## Assumptions / Open Questions
- Assumes re-running calibration 2-3x per key (18 keys x 2-3 runs, at 1000-2000 ticks each) is an acceptable compute cost for this ticket; if wall-clock cost proves prohibitive on available hardware, the Investigate step should report actual per-run timing before committing to the full sweep and consider whether a reduced subset (e.g. worlds sharing the same throttle-onset profile) can stand in for the rest with a documented rationale.
- Assumes the F6 divergence mechanism (throttle onset ~tick 300-320+) is the only plausible source of run-to-run anchor instability being tested for here; if re-runs reveal grade instability with a different root cause (e.g. genuine content/logic non-determinism unrelated to wall-clock timing), that is a distinct, more serious finding that must be reported and escalated as its own ticket, not silently absorbed into a tolerance guard.
- Assumes "stable" can be judged using the existing ±1-letter GRADE_ORDER band already enforced by `test_grade_within_anchor_band_long_run` — i.e. a key is "stable" if repeated re-runs never require widening that existing tolerance, not that every re-run produces byte-identical grades.
- Assumes converting a key to a tolerance-based guard means adding/extending a `pytest.mark.slow` multi-trial test (following the `test_corpus_diversity.py` pattern), not modifying `grade_anchors.json`'s existing single-value-per-pillar schema — if the Implement step finds the existing fixture schema cannot represent a tolerance range cleanly, that is a plan-revision trigger, not something to route around silently.
- `layer: simulation` was chosen over `testing` because the ticket's subject matter is SimQ calibration/simulation-quality measurement, not general test-infrastructure work; if this reads as ambiguous during implementation, treat `simulation` as final unless the roadmap doc's own frontmatter (`layer: simulation`) is judged wrong first.

## Implementation Notes

Ran the full 18-key × 3-trial calibration sweep (54 invocations of `tools/calibrate_simq.py`,
real throttled `Kernel`, no `audit_mode`) exactly per plan.md Step 1's invocation table. Trial 1
per key used the canonical output path; trials 2/3 used `--output data/calibration/{run_key}_trial{2,3}`.
All 54 invocations completed without crashing. Raw per-trial, per-pillar grades transcribed to
`staging_artifacts/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY/raw_calibration_sweep.md`, including
per-run throttle evidence (`budget_warnings` = count of mid-tick "exceeded budget" log lines,
`watchdog_trips` = count of end-of-tick `WatchdogTrip` CRITICAL alerts).

**Classification result: all 18/18 keys are `stable`. Zero unstable, zero escalate.** Every one of
540 pillar/trial data points (18 keys × 3 trials × 10 pillars) landed within the existing ±1-`GRADE_ORDER`
band of its committed anchor in `grade_anchors.json`, using the exact `_within_band` rule already in
`test_grade_regression.py:140-148`. This held despite direct, measured evidence that the F6 throttle
mechanism fired variably during the sweep: `budget_warnings` per run ranged 41-539, `watchdog_trips`
ranged 1-3, and engine elapsed time for identical seed/code varied up to ~4x within a single key
(`unit_faction_tension_seed42_1000t`: 15.99s-18.95s for trials 1-2 vs. 71.41s for trial 3). No trial/pillar
combination fell outside the ±1 band anywhere in the sweep, so the "escalate" path (reserved for a
violation where all 3 trials agree on the same off-anchor grade, indicating a genuine non-throttle drift)
was never triggered — no genuine (non-throttle) divergence was found.

Documented all 18 keys' full per-trial pillar tables and reliability status in
`docs/simulation_quality/eval_matrix_results.md` under a new
`## Anchor Reliability Verification (TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY)` section
(appended after the existing "Long-Run Hot-Pillar Anchors" section, append-only, no prior content edited).

Step 4 (grade-stability multi-trial guard tests) is a **documented no-op**: zero keys were classified
`unstable`, so no new test was added to `tests/unit/worldassembly/test_corpus_diversity.py`. This is
recorded explicitly (not silently skipped) in both `raw_calibration_sweep.md`'s Classification section
and the `eval_matrix_results.md` "Step 4 outcome" subsection, per plan.md Step 4 and test_plan.md's
callout that a zero-conversion result is a valid outcome requiring documentation.

`src/engine/kernel.py` has zero diff lines throughout (verified via `git diff --stat`). No edits to
`FAST_ANCHOR_KEYS`, `test_grade_within_anchor_band`, `grade_anchors.json` (values or schema),
`test_generated_frontier_3_42_extended_population_stability`, or any `HAZARD_KIND_MATCH_WORLDS`/
`POPULATION_STABILITY_WORLDS` list.

**Verification note:** re-running `tests/unit/worldassembly/test_corpus_diversity.py -m slow` without
`--resource-budget large` produced one `TimeoutError` (pytest's own 60s default "medium" resource-budget
kicking in on `test_generated_frontier_3_42_extended_population_stability`, whose 3-trial×1000-tick body
routinely takes 70-100s+) — a test-harness invocation mistake, not a real regression, and consistent with
`stored_artifacts/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE/plan.md`'s own documented
finding that this test requires `--resource-budget large` (matching `.github/workflows/test.yml:230`'s CI
invocation). Re-ran with `--resource-budget large`: 17 passed, 37 deselected, clean.

**Final reliability breakdown (18/18 keys):** all stable — `dungeon_crawl_seed{42,123,456}_1000t`,
`dungeon_crawl_seed{42,123,456}_2000t`, `urban_political_seed{42,123,456}_1000t`,
`urban_political_seed42_2000t`, `sandbox_world_seed42_1000t`, `sandbox_world_seed42_2000t`,
`unit_faction_tension_seed42_1000t`, `unit_faction_tension_seed42_2000t`,
`unit_selfmodel_pilot_seed42_1000t`, `hero_guild_routing_seed42_1000t`,
`simq_routing_test_seed42_1000t`, `generated_frontier_3_42_seed42_1000t`.

## Test Summary

- `git diff --stat src/engine/kernel.py` → empty (zero-diff AC confirmed).
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"` → 51 passed, 3 skipped,
  18 deselected (fast-tier baseline unchanged).
- `pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid`
  → 1 passed.
- `pytest tests/simulation_quality/test_grade_regression.py -m slow` → 18 passed, 54 deselected (all
  18 `SLOW_ANCHOR_KEYS` now execute, not skip — previously 7 of 18 had no calibration data on disk).
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -m "not slow"` → 37 passed, 17 deselected.
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget large` → 17
  passed, 37 deselected (includes the untouched `test_generated_frontier_3_42_extended_population_stability`).
- `make simq-full-audit-slow` → 69 passed, 3 skipped (the 3 skips are pre-existing `FAST_ANCHOR_KEYS`
  entries with no calibration data on this machine, unrelated to this ticket's scope).
- `git diff --stat data/content/ config/ data/worlds/` → empty (no collateral content/config/world drift).
- `git diff --stat tests/simulation_quality/test_grade_regression.py` → empty (`FAST_ANCHOR_KEYS`
  untouched).
- `git diff --stat tests/simulation_quality/fixtures/grade_anchors.json` → empty (no schema or value
  changes — no genuine drift found).

## Files Changed

- `docs/simulation_quality/eval_matrix_results.md` — new "Anchor Reliability Verification" section
  (append-only).
- `staging_artifacts/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY/raw_calibration_sweep.md` — new
  working-evidence file (not a required staging artifact; gitignored `staging_artifacts/` directory,
  not committed).
- `tickets/inprogress/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY.md` — this file.
- No changes to `src/engine/kernel.py`, `tests/simulation_quality/test_grade_regression.py`,
  `tests/simulation_quality/fixtures/grade_anchors.json`, or
  `tests/unit/worldassembly/test_corpus_diversity.py`.

## Completion Summary

Measurement-verification ticket. Re-ran all 18 `SLOW_ANCHOR_KEYS` 3x each via the real, throttled
`Kernel` (no `audit_mode`). Result: all 18/18 keys are grade-stable within the existing ±1-letter
band, despite confirmed, measured throttle-timing variance (up to ~4x elapsed-time spread, 41-539
budget warnings, 1-3 watchdog trips per run). No genuine (non-throttle) divergence found; no
tolerance-guard test conversions needed (documented no-op); no parity ledger changes required;
`src/engine/kernel.py` untouched throughout.
