---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM
phase: done
date: 2026-07-13
tags: [simulation-quality, cognition, self-model, determinism]
---

# TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM

## Title
COGNITION self-model loop-detection produces a load-sensitive, non-reproducible runaway-loop
result under sustained system load — a real "do not break determinism" violation

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Discovered as a side finding during `TCK-20260713-SIMQ-SCORE-CEILING-FIX`'s Step 12 live-mode
`evaluate_simq.py` corpus sweep. The scenario `urban_political_seed123_500t` is committed in
`tests/simulation_quality/fixtures/grade_anchors.json` with COGNITION grade B (`raw_score=11.0`,
`event_count=2`) — reproduced identically 3 separate times outside the live sweep (once during
SCORE-CEILING-FIX's own Step 6 regeneration, twice more standalone afterward), all bit-for-bit
identical. But one specific run of the full-corpus live-mode sweep (run under ~30 minutes of
sustained concurrent system load, with repeated `WatchdogTrip`/tick-budget-exceeded warnings
throughout its own log) produced a wildly different result for the exact same scenario/seed:
`grade=S`, `raw_score=3521.0`, `event_count=119`, `loop_detected=True` on
`self_model_active`/`subjective_divergence` — a runaway-loop signature in the self-model cognition
subsystem's loop-detection path.

This is NOT reflective of the true, stable scenario behavior (3/3 clean reproductions match the
committed anchor). It is real evidence that the project's "do not break determinism" hard rule is
not currently holding for the COGNITION self-model's loop-detection path under sustained system
load — a pre-existing, load-sensitive nondeterminism, not a corpus/anchor staleness issue.

**Correction (investigation finding, superseding the original claim above):** this ticket
originally asserted SCORE-CEILING-FIX's diff was "confirmed NOT caused" via a check of whether
COGNITION's own code/weights/config changed. That check was incomplete. Investigation found the
anomaly's magnitude (`raw_score=3521.0` vs. an expected ~595-600 for the same event count) is
compounded by a second, independent, load-*independent* bug: `src/simulation_quality/weights.py`'s
shared cross-pillar flat weight-key namespace causes INFORMATION's `subjective_divergence` weight
(`30.0`) to silently override COGNITION's own declared value (`5.0`) for the same key — a 6x
amplification, present in every run regardless of load. SCORE-CEILING-FIX's independent per-pillar
rescale made this collision worse (was 6x, is now ~6x at a higher base) without touching COGNITION's
own section. This bug is real, always-present, and has a blast radius far beyond this scenario — it
is filed separately as `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` and is explicitly **out of
scope** for this ticket (see Out of Scope). The *event-count* anomaly (2→119) remains independently
attributable to F6 (below); only the *raw_score magnitude* (11.0→3521.0) required both causes
together to explain.

## Scope
- Investigate `src/` COGNITION self-model loop-detection logic (the path producing
  `loop_detected`/`self_model_active`/`subjective_divergence` signals) for what state it reads that
  could be load/timing-sensitive (e.g. wall-clock reads, tick-budget-driven early-exit branches,
  any non-deterministic iteration order or race in shared state).
- Reproduce the runaway-loop condition deliberately under induced system load (e.g. concurrent
  CPU-bound background processes) to confirm the load-sensitivity hypothesis with a controlled
  repro, rather than relying on the one incidental sweep observation.
- Determine root cause. **If** it traces to a genuinely COGNITION-local mechanism independent of
  `src/engine/kernel.py`'s tick-budget watchdog/throttle, fix it so output is bit-identical
  regardless of load. **If** it traces to the same wall-clock-driven watchdog/throttle mechanism
  already recorded as F6 in `docs/audits/D06_longrun_health.md` (documented, intentional engine
  behavior — see Out of Scope), apply the same tolerance-based multi-trial regression-guard pattern
  `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` established for this class of finding (converting
  `urban_political_seed123_500t`'s COGNITION anchor check to an averaged/tolerance-bounded
  multi-trial guard, following `test_generated_frontier_3_42_extended_population_stability`'s
  pattern, `tests/unit/worldassembly/test_corpus_diversity.py:289-374`), and record the finding in
  `docs/simulation_quality/eval_matrix_results.md` per that ticket's established reliability-status
  process — do not silently leave the anchor unguarded either way.

## Out of Scope
- Any of SCORE-CEILING-FIX's weight/threshold changes — confirmed unrelated via `git diff`, not
  reopened here.
- Any other pillar's determinism — this is scoped to COGNITION's self-model loop-detection path
  specifically, the only place this symptom was observed.
- **Any change to `src/engine/kernel.py`'s tick-budget watchdog or mid-tick emergency throttle
  logic, anywhere** — this is documented, intentional engine behavior (F6,
  `docs/audits/D06_longrun_health.md`; `docs/engine/kernel.md` §"Emergency Throttling";
  `docs/engine/performance_contract.md` §7 "Adaptive Phase Budget Governor"). Note: investigation
  found F6 is *not* actually recorded as a dedicated entry in
  `docs/guidelines/intentional_divergences.md` (only an incidental cross-reference exists) — this
  ticket does not fix that documentation gap either, it is noted for awareness only. Confirming the
  throttle is (or is not) the cause of this specific COGNITION symptom is in scope; changing how
  the throttle behaves is not — this precedent was already settled by
  `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` and is not reopened here.
- Reopening `docs/guidelines/intentional_divergences.md`'s F6 entry itself — if investigation
  confirms this ticket's symptom is F6, the correct action is applying the existing tolerance-guard
  remedy pattern to this specific anchor, not revising the divergence record.
- **`src/simulation_quality/weights.py`'s cross-pillar flat weight-key namespace collision** —
  confirmed real and load-independent by investigation (7 colliding keys across
  COGNITION/INFORMATION/ECONOMY/WORLD), but out of this ticket's blast radius (fixing it would
  change scoring for every anchor touching any of the 7 keys, not just this one). Filed separately
  as `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`. This ticket's fix (F6 tolerance guard, if
  applicable) must not depend on or block on that separate ticket landing first.

## Acceptance Criteria
- [x] Root cause of the load-sensitive nondeterminism identified with file:line evidence, including
      an explicit determination of whether it is the same mechanism as F6
      (`docs/audits/D06_longrun_health.md`, `src/engine/kernel.py`'s watchdog/throttle) or a
      genuinely COGNITION-local cause independent of it. (Confirmed: same mechanism as F6, not
      COGNITION-local — see Implementation Notes.)
- [x] A deliberate repro (controlled induced load) demonstrates the bug before the fix/guard, and
      its absence (or bounded-tolerance containment) after. (`repro_sweep.md`: two idle + two
      escalating induced-load runs; throttle mechanism confirmed load-sensitive, COGNITION output
      bit-identical.)
- [x] **If COGNITION-local root cause:** `urban_political_seed123_500t` (and ideally a broader
      COGNITION-active sample) produces bit-identical output across multiple runs under both idle
      and induced-load conditions.
      **If F6/kernel-throttle root cause:** `urban_political_seed123_500t`'s COGNITION regression
      check is converted to a tolerance-based multi-trial guard (matching the established pattern),
      and its reliability status is recorded in `eval_matrix_results.md` — this scenario is not
      left as an unguarded single-run point comparison either way. (Root cause is F6, but bit-identity
      was empirically achievable per the repro, so the bit-identical branch's guard —
      `test_urban_political_seed123_500t_cognition_bit_identical_under_load` — was used per Step 2's
      fallback path; reliability status recorded as **stable** in `eval_matrix_results.md`.)
- [x] No regressions in `tests/simulation_quality/test_grade_regression.py` or the COGNITION
      scorer/self-model test suites.

## Related Tickets
- `TCK-20260713-SIMQ-SCORE-CEILING-FIX` (done) — where this was discovered as a side finding during
  Step 12's live-mode sweep; confirmed unrelated to that ticket's own diff.
- `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` (done) — the precedent ticket for this exact class
  of finding (wall-clock-throttle-driven variance in a long-run SimQ anchor). Its Out of Scope
  explicitly classified `urban_political_seed123_500t`-scale anchors (500t) as a `FAST_ANCHOR_KEYS`
  entry not yet verified against F6, with the caveat that unexpected instability "must be reported,
  not silently acted on" — this ticket is that report and its natural follow-up. Its established
  remedy pattern (tolerance-based multi-trial guard, not a kernel-level determinism fix) is the
  template this ticket's Scope/AC now follow if root cause matches F6.
- `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` (open) — filed as a direct result of this ticket's
  investigation. `src/simulation_quality/weights.py`'s shared cross-pillar flat weight-key
  namespace silently amplifies COGNITION's `subjective_divergence`/`belief_active` scoring (among
  7 total colliding keys) regardless of load — explains the anomaly's raw_score *magnitude* but not
  its *event-count* jump (which remains attributable to F6 alone). Explicitly out of scope here;
  no dependency in either direction.

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` — self-model/cognition mechanics chapter.
- `docs/engine/kernel.md` — tick-budget/watchdog behavior (the `WatchdogTrip` warnings observed
  alongside the anomalous result).
- `docs/audits/D06_longrun_health.md` §F6 — the existing documented finding for wall-clock-driven,
  load-sensitive divergence past ~tick 300-320; likely the same mechanism, first checked here.
- `docs/guidelines/intentional_divergences.md` — records F6 as a permanent intentional divergence;
  not to be revised by this ticket (see Out of Scope).
- `docs/engine/performance_contract.md` §7 — the Adaptive Phase Budget Governor mechanism F6
  attributes the variance to.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/plan.md`
- `stored_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/investigation.md`
- `stored_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/test_plan.md`
- `stored_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/repro_sweep.md` (working evidence, migrated alongside the other staging artifacts — matches `raw_calibration_sweep.md`'s actual precedent, which is also fully migrated to `stored_artifacts/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY/`, not left in `staging_artifacts/`)

## Related Code Areas
- COGNITION self-model loop-detection path (locate via `graphify query "self model loop detection"`
  or `grep -rn "loop_detected" src/`) — not yet pinned to a specific file:line, first investigation
  task.
- `src/engine/kernel.py` (tick-budget/watchdog — possible interaction, not confirmed).

## Assumptions / Open Questions
- Whether the root cause is in the self-model subsystem itself or in how the kernel's tick-budget
  throttle interacts with it under load is not yet known — first investigation task.

## Implementation Notes

**Root cause (restated from investigation.md, corroborated empirically here)**: the observed
2->119/`grade=S` anomaly on `urban_political_seed123_500t` traces to the same mechanism as F6
(`docs/audits/D06_longrun_health.md` §F6) — `decision_divergence_detected`
(`src/observability/event_extractor.py:477-496`) has no "already-emitted" dedup gate and re-fires
every tick an entity's `danger` concern (`urgency > 0.7`) persists alongside a non-survival active
project; F6's wall-clock watchdog/throttle (`src/engine/kernel.py:420-442`, `574-601`) can, under
sustained load, drop resolution-queue work and stall that resolution across many consecutive ticks.
This is not a COGNITION-local determinism bug. The `raw_score` *magnitude* (11.0 -> 3521.0) is
separately compounded by a load-independent cross-pillar weight-key collision in
`src/simulation_quality/weights.py`, filed as `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` and
explicitly out of scope here.

**Repro (Step 1/2, full data in `stored_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/repro_sweep.md`)**: drove
`urban_political` seed 123, 500 ticks, via `tools/calibrate_simq.py`'s real internal helpers (real
throttled `Kernel`, no `audit_mode`), two idle repeats and two escalating induced-load levels
(multiprocessing busy-loop pool, 2x and 4x core oversubscription on a 4-core machine — no `stress-ng`
available):

| Run | budget_warnings | watchdog_trips | wall_elapsed_s | COGNITION event_count/raw_score/normalized_score/grade/loop_detected |
|---|---|---|---|---|
| idle-1 | 28 | 0 | 12.24 | 2 / 11.0 / 0.088 / B / True |
| idle-2 | 31 | 0 | 12.32 | 2 / 11.0 / 0.088 / B / True |
| load-2x | 40 | 1 | 21.52 | 2 / 11.0 / 0.088 / B / True |
| load-4x | 108 | 0 | 43.03 | 2 / 11.0 / 0.088 / B / True |

The throttle mechanism is confirmed load-sensitive (budget_warnings climbs monotonically with load
intensity, a genuine mid-tick emergency throttle fired at 2x, wall-clock time grew up to 3.5x) — this
satisfies Step 1's "retry with heavier load before concluding a null result" requirement; the result
is not null, the throttle demonstrably fires more under load. But COGNITION's own output stayed
bit-identical across all four runs and matched the committed anchor (`B`/`0.088`) exactly.
`urban_political_seed123_500t` does not appear to place any entity into the danger-concern-stuck
state F6's mechanism requires to explode `decision_divergence_detected`, at this seed/tick-count and
up to 4x core oversubscription. `ENABLE_SELF_MODEL_COGNITION` was confirmed OFF for every run
(absent from `config/simulation_quality/profiles/urban_political.yaml`'s `feature_flags:` block, per
`_load_profile_feature_flags` output), closing investigation Open Question #5 empirically — this does
not affect the result since `decision_divergence_detected` is independent of that flag.

**Decision (Step 2)**: fallback path selected — **bit-identical achievable** (Step 3b), not the
tolerance-guard path (Step 3a). Full justification in `repro_sweep.md`'s `## Decision` section.

**Test added (Step 3b)**: `test_urban_political_seed123_500t_cognition_bit_identical_under_load`
(`tests/unit/worldassembly/test_corpus_diversity.py`), placed adjacent to
`test_generated_frontier_3_42_extended_population_stability` (section 2c). Drives the scenario
in-process via `tools.calibrate_simq`'s internals (idle run in a `tempfile.TemporaryDirectory()`,
then a load run under a 2x-core-oversubscription busy-loop pool, also in a fresh temp dir), and
asserts the two runs' COGNITION `event_count`/`raw_score`/`normalized_score`/`grade`/`loop_detected`
dict are exactly equal.

**Side note, not a scope deviation**: `pytest tests/simulation_quality/test_grade_regression.py -m
"not slow"` initially failed on `test_grade_anchor_file_exists_and_valid`'s field-confusion guard
(`TypeError: 'NoneType' object is not subscriptable`) because
`data/calibration/hero_guild_routing_seed42_1000t/quality_report.json` did not exist locally
(`data/calibration/` is fully gitignored, ephemeral, machine-local). This is unrelated to this
ticket's diff — confirmed by checking `git log` on that path (never tracked) and that no file this
ticket touches has any connection to that run key/pillar. Regenerated the missing local calibration
report via `tools/calibrate_simq.py --ticks 1000 --seed 42 --name hero_guild_routing` (ephemeral,
gitignored, not part of Files Changed) so the guard test's pre-existing environment dependency is
satisfied; re-ran and confirmed pass. No code, test, or doc file was changed to accommodate this.

**Zero-diff checks (Step 5, run at close of Step 5, verbatim)**:
```
$ git diff --stat src/engine/kernel.py
(no output)
$ git diff --stat src/simulation_quality/weights.py config/simulation_quality/scoring_weights.yaml
(no output)
$ git diff --stat src/observability/event_extractor.py
(no output)
```
All three empty, confirming no scope-guard violation.

## Test Summary
All Step 5 commands run in order, all pass:
1. `pytest tests/simulation_quality/test_accumulator.py tests/simulation_quality/test_cognition_scorer.py tests/simulation_quality/test_weights.py tests/simulation_quality/test_information_scorer.py tests/simulation_quality/test_report.py tests/simulation_quality/test_quality_hub_integration.py -v` — 91 passed, including `test_duplicate_event_id_is_noop` (verified individually too).
2. `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v` — 6 passed, 57 skipped (no local calibration data for those specific run keys — pre-existing, expected skip behavior), 18 deselected. Includes `test_within_band_default_tolerance_unchanged` and `test_grade_anchor_file_exists_and_valid` (both pass).
3. `pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid` — 1 passed.
4. `pytest tests/simulation_quality/test_grade_regression.py -m slow -k urban_political -v` — 4 skipped (no local `SLOW_ANCHOR_KEYS` calibration data for `urban_political_*_1000t/2000t` in this environment; consistent skip behavior, no failures).
5. `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget large -v` — 18 passed (194.51s), including the new `test_urban_political_seed123_500t_cognition_bit_identical_under_load` and the untouched `test_generated_frontier_3_42_extended_population_stability`.
6. `pytest tests/unit/worldassembly/test_corpus_diversity.py -k cognition_bit_identical -m slow --resource-budget large -v` — 1 passed (isolated run, confirms Step 3b's own Verify clause).

## Files Changed
- `tests/unit/worldassembly/test_corpus_diversity.py` — new test `test_urban_political_seed123_500t_cognition_bit_identical_under_load`.
- `docs/simulation_quality/eval_matrix_results.md` — new appended section "COGNITION Loop-Detection Nondeterminism Verification (TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM)".
- `stored_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/plan.md`, `investigation.md`, `test_plan.md` — migrated from `staging_artifacts/`.
- `stored_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/repro_sweep.md` — new working-evidence file, migrated from staging alongside plan.md/investigation.md/test_plan.md (matches `raw_calibration_sweep.md`'s actual precedent).
- `tickets/inprogress/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM.md` (this file, moving to `tickets/done/`).
- No `src/` files touched (verified via three zero-diff checks above).

## Completion Summary
All three ACs are met. Root cause identified with file:line evidence and explicitly determined to be
the same mechanism as F6 (not COGNITION-local) — `src/engine/kernel.py`'s watchdog/throttle
interacting with `decision_divergence_detected`'s by-design missing dedup gate. A controlled repro
(two idle repeats, two escalating induced-load runs) demonstrated the throttle mechanism itself is
load-sensitive but this specific anchor's COGNITION output is bit-identical regardless of load — the
bit-identical fallback path (Step 3b) was correctly selected over the tolerance-guard path per Step
2's evidence-based decision criteria, and `urban_political_seed123_500t`'s COGNITION check is no
longer an unguarded single-run point comparison (a new bit-identical regression test now covers it).
Reliability status recorded in `eval_matrix_results.md` as **stable**. No regressions in
`test_grade_regression.py` or the COGNITION scorer/self-model suites. `src/engine/kernel.py`,
`src/simulation_quality/weights.py`, `config/simulation_quality/scoring_weights.yaml`, and
`src/observability/event_extractor.py` all show a zero diff, confirmed explicitly.
