---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE
phase: open
date: 2026-10-11
tags: [simulation-quality, grade-thresholds, determinism, regression]
---

# TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE

## Title
The SimQ grade anchors are measured under audit_mode, so an anchor grades the rules and not host
speed; the whole anchor family is re-anchored once from deterministic runs, with provenance

## Status
INPROGRESS

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
The `*_grade_stability` tests in `tests/unit/worldassembly/test_corpus_diversity.py` drive the
real throttled `Kernel` without `audit_mode`, on purpose (see the module docstring §5 and the
population-stability docstring). Outside audit_mode the kernel's wall-clock watchdog and throttle,
the replay backlog and the per-phase costs change what an entity does
(`docs/engine/kernel.md` "Emergency Throttling"; `docs/engine/deterministic_execution.md`). So an
anchor's result depends partly on how fast the host is.

Evidence from 2026-10-11:
- rpg-implementer-3 (TCK-20261009-CAMPAIGN-EPISODE-DELIBERATE-ATTACKS-STRICT-XFAIL-DEPENDS-ON-TEST-ORDER)
  showed that one 10 ms delay in tick 1, from a cold lazy import, flips a campaign episode's
  deliberate attacks from 2 to 5. Under audit_mode the count is a stable 2.
- On one SHA, isolated runs of simq_routing seed42 1000t COGNITION gave main 20f67b744 F/p/F and
  batch3 b6468a5b2 p/F/F.
- SOCIAL event_count drifts 710-770 across trials on the same SHA. The trial values are recorded
  in TCK-20261007-SIMQ-SOCIAL-ANCHOR-FAMILY-STEP-RISE-BISECT-THEN-REBASELINE.
- The existing `band_tolerance=2` "bimodal" override on urban_political seed123 500t COGNITION is
  the same effect, already absorbed into a tolerance.

**rpg-planner ruling (2026-10-11):** the grade anchors move to audit_mode. An anchor grades what
the simulation does, which is a property of the rules, and the M0 rpg gate harness judges the same
thing (PinnedNormalGovernor + audit_mode). There is one re-anchor of the whole family, with
provenance. The SOCIAL family's "bisect" becomes: re-run under audit_mode on main, and bisect only
if a step remains there. Coverage of the throttled kernel moves to a small test of its own that is
not an anchor. testing-planner owns the re-anchor mechanics, the provenance and the retirement of
the known-reds catch-all; whether a re-anchored value is the intended behaviour is rpg-planner's
call (Bible over tests).

## Scope
1. **One shared pinned runner.** Every anchor in `grade_anchors.json` must be measured the same
   way:
   - Every `*_grade_stability` test in `test_corpus_diversity.py` runs its engine run with
     `audit_mode` on.
   - Investigate whether `tools/calibrate_simq.py::_run_engine`'s `extra_flags` (YAML string
     values) can carry it. If not, add a narrow, explicit parameter.
   - Do NOT change the default for the calibration CLI's other callers.
   - Investigate every other consumer of `tests/simulation_quality/fixtures/grade_anchors.json`
     (`test_grade_regression.py`, `tools/evaluate_simq.py`, `test_evaluate_harness.py`,
     `test_idea4_regression_coverage_confirmation.py`, `tests/tools/test_corpus_registry.py`,
     `tests/tools/test_evaluate_simq_scenario_scope.py`,
     `tests/unit/tools/test_simq_audit_gaps.py`,
     `tests/integration/test_world_profile_feature_flag_guardrail.py`).
   - Any consumer that produces the runs it grades must produce them under audit_mode too. Read-only
     consumers that only check the fixture's shape need no change. The fixture must not end up with
     anchors measured two ways.
2. **Determinism proof before any re-anchor.**
   - For each anchored (world, seed, ticks) run, take 2 isolated fresh-process runs under
     audit_mode on one main SHA.
   - Each pair must be bit-identical for every anchored pillar's event_count and raw_score.
   - A run that is not identical is a finding for rpg-planner (a determinism bug under audit_mode),
     and its anchor is not re-anchored in this ticket.
3. **One family re-anchor with provenance.**
   - Re-anchor every anchor whose audit_mode value differs from the committed one, in a single
     commit.
   - Write the provenance to `agent-working/stored_artifacts/<ticket>/reanchor_provenance.md`:
     - the main SHA;
     - the 2-run identity table;
     - for each row: old anchor, new value, grade band, and whether it moved;
     - the cited rpg-planner ruling.
   - The in-test copies of anchor values (the comments "correct X to grade_anchors.json in the same
     commit") stay in sync with the fixture.
   - Send rpg-planner the moved rows for the "intended?" ruling before the PR is marked ready.
4. **Tolerances added only to absorb wall-clock nondeterminism are tightened back.**
   - Find each per-test override whose own docstring cites the throttle, the watchdog, F6 timing or
     "bimodal" trials, e.g. the `band_tolerance=2` override on urban_political seed123 500t.
   - Return it to the shared default if the audit_mode runs are identical.
   - List each one in the provenance file.
   - The shared `_within_band` default is unchanged.
5. **Throttled-kernel coverage as its own small test.**
   - Add one slow test that runs the real throttled `Kernel` (no audit_mode) on one anchored world
     for a bounded number of ticks.
   - It asserts a coarse band only: no stall, no crash, more than 0 decisions made, the tick count
     reached, and population above 0.
   - It is not an anchor and reads nothing from `grade_anchors.json`.
   - Whether it lives in the perf suite or in testing's is agreed with perf-planner before
     Implement. testing-planner asks; the default is `tests/unit/worldassembly/`, next to the
     population-stability tests.
6. **Known-reds reconciliation in `tools/test_architecture/slow_known_reds.yaml`.**
   - Remove the specific entries this ticket makes green.
   - Narrow or delete the `test_corpus_diversity*` catch-all on its own evidence: the anchors it
     covers are now deterministic; the population-stability entries it also covers are out of
     scope (see below) and keep an entry.
   - Any anchor still red after re-anchoring keeps a specific entry, owned by rpg.
   - Retiring an entry still needs 3 tested slow greens; this ticket only edits what it can prove.
   - The catch-all expires 2026-11-04; this ticket must land before then, or the catch-all's
     re-review cites it.
7. **The tickets that become redundant are updated, not silently left.**
   - TCK-20261007-SIMQ-SOCIAL-ANCHOR-FAMILY-STEP-RISE-BISECT-THEN-REBASELINE,
     TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE and
     TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE are rpg's. Send rpg-planner the
     audit_mode result of each so that rpg-planner can close or re-scope them (bisect only where a
     step remains).
   - TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED (testing, inprogress) gets this
     ticket's result in its Implementation Notes.
8. **Docs.**
   - Update the `test_corpus_diversity.py` module docstring (§5's "tracked separately" note becomes
     resolved for the anchors).
   - Update the "Re-Baseline" note in `docs/testing/regression_policy.md`.
   - Update `test_grade_regression.py`'s re-anchor how-to: anchors are measured under audit_mode,
     with 2 identical isolated runs, provenance required.

## Out of Scope
- `src/engine/kernel.py`'s throttle and watchdog, and the F6 intentional-divergence record: no
  engine change.
- The `decision_divergence_detected` dedup gate (F6 root-cause fix): separate, rpg's.
- `test_population_stability[*]` and `test_generated_frontier_3_42_extended_population_stability`:
  - They deliberately measure the throttled kernel with averaged tolerances and are not anchors.
  - They keep their known-red coverage.
  - Whether they too move is a later question for rpg-planner and perf-planner.
- Deciding whether a re-anchored value is intended behaviour: rpg-planner rules.
- The campaign-episode audit_mode fix (rpg-implementer-3, dispatched by rpg-planner).
- The rpg gate harness (already pinned).

## Acceptance Criteria
- AC1: Every anchor in `grade_anchors.json` is produced under audit_mode by every consumer that
  produces runs. A test shows the anchor tests' runner passes audit_mode, e.g. by asserting the
  kernel flags.
- AC2: The provenance file shows 2 isolated runs under audit_mode, identical for every anchored run
  that is re-anchored, on one recorded main SHA. Non-identical runs are listed and routed, not
  re-anchored.
- AC3: All `*_grade_stability` tests pass on that SHA, in 2 fresh isolated processes and in the
  whole-file order. Any that cannot pass is listed with an rpg owner and a specific known-red
  entry.
- AC4: Each throttle-absorbing tolerance override is either back to the default or kept with a
  stated audit_mode reason.
- AC5: The throttled-kernel smoke test exists, passes and is slow-marked. Its location is agreed
  with perf-planner and recorded in the ticket.
- AC6: `slow_known_reds.yaml` is reconciled per Scope 6. `tests/architecture` known-reds
  validation passes, and the catch-all is narrowed or removed with its reason in the note.
- AC7: rpg-planner has ruled on the moved rows. The ruling is cited in the provenance file, and the
  3 rpg anchor tickets have been sent their audit_mode result.
- AC8: The first tested slow run after the merge shows no new unowned red in corpus diversity. Its
  run id is recorded.

## Related Tickets
- TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED (catch-all owner, inprogress)
- TCK-20261007-SIMQ-SOCIAL-ANCHOR-FAMILY-STEP-RISE-BISECT-THEN-REBASELINE (rpg)
- TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE (rpg)
- TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE (rpg)
- TCK-20261009-CAMPAIGN-EPISODE-DELIBERATE-ATTACKS-STRICT-XFAIL-DEPENDS-ON-TEST-ORDER (same cause, rpg)
- TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2 (parked determinism cause behind the catch-all)
- TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM, TCK-20260817-STANDARD-SIMQ-COGNITION-BIT-IDENTICAL-GUARD-TOLERANCE-CONVERSION (the tolerance precedent this replaces)
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC (same pinning as the gate harness)

## Related Docs
- docs/engine/kernel.md ("Emergency Throttling"), docs/engine/deterministic_execution.md
- docs/testing/regression_policy.md
- docs/audits/D06_longrun_health.md §F6

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261009-FACTION-TREASURY-IS-ONE-TYPED-ACCOUNT-EXCH-02-C/probes/paired_table_main_vs_batch3.txt

## Related Code Areas
- tests/unit/worldassembly/test_corpus_diversity.py
- tests/simulation_quality/fixtures/grade_anchors.json, tests/simulation_quality/test_grade_regression.py
- tools/calibrate_simq.py (`_run_engine`), tools/evaluate_simq.py
- tools/test_architecture/slow_known_reds.yaml

## Assumptions / Open Questions
- Assumed: audit_mode can be passed through `_run_engine` without changing what the calibration CLI
  does by default. Investigate first; if not, raise it with testing-planner before choosing a
  path.
- Open (testing-planner asks perf-planner): where the throttled-kernel smoke test lives.
- Cost: about 15 anchored runs × 2 isolated runs, with the 1000t runs `resource_budget_large`.
  Budget the investigation accordingly, using the slow job's xdist settings as a guide.

## Implementation Notes
Filed by testing-planner 2026-10-11 after rpg-planner's audit_mode ruling. Lands in the single open testing PR #531 (user rule: one PR for all current work). Full record: `agent-working/stored_artifacts/TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE/reanchor_provenance.md` (table: `reanchor_table.tsv`; run rows: `audit_rows.jsonl`).
- Path (AC1): `_run_engine(..., audit_mode=True)` and `calibrate_simq --audit-mode`; `evaluate_simq._run_calibration` passes it for every anchor key; the 15 stability-test engine calls use it. `tests/simulation_quality/test_anchors_audit_mode.py` pins the Kernel flags, the argv and the call lines.
- Unique run ids: the Kernel default id (`run_<sec>_<seeded suffix>`) is the same for every same-seed process, so same-second runs shared a `data/runs/<id>` and doubled events (found when the first parallel stage-1 batch gave COGNITION 2 vs 4 events). `_run_engine` now passes `<name>_<seed>_<ticks>_<pid>_<uuid8>`; frozen-clock regression test. The root cause belongs to rpg (TCK-20261011-DEFAULT-RUN-ID-CANNOT-COLLIDE-ACROSS-SAME-SEED-PROCESSES).
- Determinism proof (AC2): 81 of 81 anchors, 2 isolated audit_mode runs each, identical on every pillar and overall, twice: on main 1e42208d0 (proof SHA dca84e1aa) and again after PR #536 on main b396080cc (proof SHA a329112a2, `src/` identical to main, clean tree). Re-anchored from the second.
- Re-anchor (AC7): rpg-planner 2026-10-12 accepted every moved row (FACTION=0 included: b1ab4cc92 / #198, not a regression; no exclusions; the designer may later move FACTION by design). 467 of 810 rows moved on the post-#536 main (167 beyond the grade band, 300 inside it but outside the score tolerance). `simq_reanchor.py` writes the fixture and the table from the run rows; byte-exact round trip. Cause of the move: #536 (hunting, grazing, healing, upkeep, services) on top of anchors last changed 2026-08-31.
- Tolerances (AC4): the 5 `SCORE_TOLERANCE_OVERRIDES` are gone (empty table, pinned by a test); `test_corpus_diversity.py` reads each anchor from the fixture via `_anchor(...)`, drops the `abs_floor`/`band_tolerance` widenings and runs one trial; the 3 class-(c) COGNITION guards run one audit_mode run against the fixture.
- Smoke test (AC5): `tests/unit/worldassembly/test_throttled_kernel_smoke.py` (slow, sandbox_world seed 42, 150 ticks, throttled kernel, coarse: tick reached, events > 0, population alive; unique run id, removes its directory). Location: next to the stability tests (perf-planner has no live session, so the ticket's default was taken).
- Known reds (AC6): 3 specific `flaky` entries (frontier_marches, urban_political and generated_frontier_3_42 population stability) before the catch-all; the `test_corpus_diversity*` catch-all stays last, re-pointed to this ticket, same owner and expiry 2026-11-04; the ph9 entry was retired with its 3 tested greens (38127831767, 38166802362, 38315414967). `test_slow_regression_report.py` updated.
- CI cost: slow job 113 min of 240; corpus step 20 min, audit_mode x1.35 typical (+7 min), x2.1 worst (+22 min). `simq-grade-drift` runs the fast tier only, informational.
- The old reporting-path ticket TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED was closed as superseded by this one.
- Docs: `docs/testing/regression_policy.md` §11b, the `test_corpus_diversity.py` §5 note and the re-anchor how-to in `test_grade_regression.py`.
- OPEN until after the merge: AC8 (first tested slow run, its run id). Cross-host proof: slow-regression dispatched on the PR branch (run id in the PR).

## Test Summary
On the re-anchor commit (main b396080cc, local host, 6 cores): `tests/unit/tools tests/simulation_quality tests/static` plus the smoke test: 1465 passed, 85 skipped. The 3 class-(c) COGNITION guards plus the urban_political 500t stability test: 8 passed. `test_corpus_diversity.py -k "stability or grade"` in whole-file order: 31 passed, 1 failed: `test_generated_frontier_3_42_extended_population_stability` hit the resource time limit (`TimeoutError`) while other jobs shared the host; it is the throttled, non-anchor population test, covered by its specific `flaky` known-red entry (owner testing-implementer, expiry 2026-11-04), not a grade-anchor failure. The 2-fresh-isolated-process check of AC3 and the cross-host proof are the slow-regression dispatch on the PR branch (run id on #531). The anchor-reading tests in `test_grade_regression.py` read `data/calibration/` (populated by `evaluate_simq`), which this run did not repopulate; their fixture is validated by the 81-key identity proof and the structure tests.

## Files Changed

## Completion Summary
