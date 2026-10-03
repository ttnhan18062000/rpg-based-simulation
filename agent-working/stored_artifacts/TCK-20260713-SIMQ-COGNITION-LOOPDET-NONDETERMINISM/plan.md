---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM
artifact_type: plan
tags: [simulation-quality, cognition, self-model, determinism]
---

# Implementation Plan — TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM

## Summary

Investigation confirmed the root cause is F6 (`docs/audits/D06_longrun_health.md` §F6): under sustained
system load, `kernel.py`'s wall-clock watchdog/throttle drops resolution-queue work, which stalls an
entity's `danger`-concern resolution and causes `decision_divergence_detected`
(`src/observability/event_extractor.py:477-496`, no already-emitted dedup gate) to genuinely re-fire
every tick the mismatch persists — a real, load-driven event-count explosion, not a code bug in
loop-detection/dedup (both confirmed correct). Per the ticket's own amended Scope/AC, this is the
documented-intentional-behavior branch (not a COGNITION-local determinism bug), so the remedy is the
same tolerance-based multi-trial guard pattern `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` already
established, applied to `urban_political_seed123_500t`'s COGNITION anchor specifically — not a
kernel-level fix (explicitly forbidden). This plan first runs a controlled idle-vs-induced-load repro to
confirm the magnitude and derive real tolerance numbers (not invented ones), documents the repro as an
explicit decision point (tolerance-guard path is expected/primary; a bit-identical path is the fallback
only if the repro unexpectedly shows load has no effect), adds the guard test to
`tests/unit/worldassembly/test_corpus_diversity.py` following
`test_generated_frontier_3_42_extended_population_stability`'s exact shape, records the anchor's
reliability status in `docs/simulation_quality/eval_matrix_results.md`, and verifies `src/engine/kernel.py`
has a zero diff throughout. The separate `weights.py` cross-pillar collision
(`TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`) is not touched anywhere in this plan.

**Planning-time finding, not blocking**: `config/simulation_quality/profiles/urban_political.yaml` (the
profile `urban_political_seed123_500t` actually calibrates under) does not set
`ENABLE_SELF_MODEL_COGNITION: "ON"` (default is OFF, `src/domains/optimization/feature_flags.py:15`;
gated in `src/engine/pipeline.py:143`). This resolves investigation.md's Open Question #5: `self_model_updated`
plausibly never fires for this anchor's real runs, but `decision_divergence_detected` — the event actually
driving the 2→119 explosion — is gated purely on `entity.strategic.concerns`/`current_project_id`
(`event_extractor.py:477-496`), independent of the self-model bundle or that flag. Step 1 records the
profile's actual feature-flag set as part of the repro evidence so this is confirmed empirically, not just
by static read.

## Steps

### Step 1 — Controlled repro: idle vs. induced-load, `urban_political` seed 123, 500t

**Files:** `staging_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/repro_sweep.md` (new,
working evidence — not one of the three required staging artifacts, mirrors
`stored_artifacts/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY/raw_calibration_sweep.md`'s precedent).
Writes ephemeral output under `data/calibration/` (gitignored, not committed).

**Change:** Using `tools/calibrate_simq.py --ticks 500 --seed 123 --name urban_political` (which
resolves `--profile urban_political` per `_resolve_profile`, matching `FAST_ANCHOR_KEYS`'s
`urban_political_seed123_500t` invocation), run the real throttled `Kernel` (no `audit_mode`) twice:
1. **Idle run**: no induced load, default machine state.
2. **Induced-load run**: with deliberate concurrent CPU load running throughout the tick loop (e.g.
   `stress-ng --cpu $(nproc) --timeout 600s &` started before invocation and confirmed still running at
   completion, or a Python multiprocessing busy-loop pool) — either mechanism is acceptable per
   test_plan.md, provided it reliably produces elevated `budget_warnings`/`watchdog_trips` counts.

For both runs, capture and transcribe into `repro_sweep.md`:
- COGNITION pillar's `event_count`, `raw_score`, `normalized_score`, `grade`, `loop_detected` from
  `quality_report.json`.
- `budget_warnings` count (log lines matching "exceeded budget", mid-tick throttle, `kernel.py:574-601`)
  and `watchdog_trips` count (`WatchdogTrip` CRITICAL alerts, end-of-tick DEGRADED transition,
  `kernel.py:420-442`) — same evidence style as `raw_calibration_sweep.md`.
- The resolved profile's feature-flag set (`_load_profile_feature_flags("urban_political")` output),
  confirming whether `ENABLE_SELF_MODEL_COGNITION` is ON or OFF for this exact invocation (closes
  investigation Open Question #5 empirically).
- `elapsed_s` wall-clock tick-loop time for each run.

**Do NOT touch:** `src/engine/kernel.py` (read-only — measured subject); `grade_anchors.json`; any
`config/simulation_quality/` file; do not pass `audit_mode` or any flag that disables the throttle in
either run — both must be real, throttled runs.

**Verify:** `repro_sweep.md` contains both runs' full data table. If the induced-load run shows
`budget_warnings`/`watchdog_trips` > 0 and the idle run shows materially fewer (or zero), load-sensitivity
is confirmed as a precondition for Step 2's decision. If induced load fails to produce any elevated
throttle counts, note this explicitly and retry with a longer/heavier load window before concluding
anything — do not silently proceed to Step 2 on a null result.

### Step 2 — Decision point: classify repro result, choose remedy path

**Files:** `staging_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/repro_sweep.md`
(append a `## Decision` section).

**Change:** Compare the two runs' COGNITION `event_count`/`raw_score`/`grade`/`loop_detected` from Step 1:
- **Expected/primary outcome — F6 confirmed**: the induced-load run's `event_count` and/or `raw_score`
  diverge materially from the idle run's (consistent with the investigation's evidence-based prediction),
  and idle-run output alone is not guaranteed bit-identical across repeats. → Proceed to **Step 3a**
  (tolerance-based multi-trial guard). Record the observed idle-vs-load delta as the evidentiary basis for
  the tolerance band Step 3a derives.
- **Fallback outcome — bit-identical achievable**: both runs (and, if needed, a third idle repeat) produce
  identical COGNITION `event_count`/`raw_score`/`grade` regardless of induced load. → Proceed to **Step 3b**
  (tight byte-identical assertion) instead of 3a. Do not implement both 3a and 3b — this is a strict
  either/or per test_plan.md's explicit instruction.

Record which path was chosen and the one-paragraph justification (citing the actual Step 1 numbers) in the
`## Decision` section before starting Step 3.

**Do NOT touch:** no code or test files in this step — pure analysis of Step 1's already-captured data. Do
not widen or invent a path that mixes both remedies.

**Verify:** `## Decision` section states exactly one chosen path with a cited numeric justification from
Step 1's table.

### Step 3a — (Expected path) Tolerance-based multi-trial guard test

*Only if Step 2 selects this path.*

**Files:** `tests/unit/worldassembly/test_corpus_diversity.py` (new test function, appended after
`test_generated_frontier_3_42_extended_population_stability`, same module).

**Change:** Add `test_urban_political_seed123_500t_cognition_grade_stability` (`@pytest.mark.slow`),
following `test_generated_frontier_3_42_extended_population_stability`'s exact shape adapted for a
grade/score guard instead of a population guard (per investigation's Anti-Drift Hazards' explicit
instruction not to invent a new pattern):
1. Import `tools.calibrate_simq`'s internal helpers (`_resolve_profile`, `_load_profile_feature_flags`,
   `_load_weights`, `_build_hub`, `_replay_jsonl_through_hub`, and whatever `_run_engine`-equivalent
   drives the real throttled `Kernel` for `urban_political` seed 123 at 500 ticks) — matching
   `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`'s Step 4 approach of calling calibration internals
   in-process rather than shelling out, so the test exercises the exact same scoring path
   `grade_anchors.json` was calibrated against (profile-aware `ScoringWeights`, feature flags), not a
   hand-rolled `Kernel(profile=PROD_SMALL)` setup.
2. Run **3 independent same-seed (123) trials**, each replaying its `simulation_events.jsonl` through a
   fresh `QualityHub` built with a `tempfile.TemporaryDirectory()` (hermetic — does not write into
   `data/calibration/` or clobber Step 1's evidence).
3. Extract COGNITION's `grade` and `normalized_score` per trial.
4. Assert every trial's grade is within the existing ±1 `GRADE_ORDER` band of the committed anchor
   (`B`, reproduce the band-comparison logic locally per this file's existing self-contained convention —
   do not import from `test_grade_regression.py`).
5. Assert the **mean** normalized_score across the 3 trials stays within a tolerance band whose
   floor/ceiling are derived from Step 1's actual idle-vs-load spread (not invented numbers) — same
   derivation method `test_generated_frontier_3_42_extended_population_stability` used for its tick-900/
   tick-1000 floors (worst-observed-divergence-informed, documented in the test's own docstring with a
   citation to `repro_sweep.md`).
6. On failure, the assertion message must show full per-trial grade/score data (mirrors the existing
   `Per-trial values: {...}` pattern), not just "failed."
7. Test docstring must cite this ticket ID, `repro_sweep.md`, and F6 (`docs/audits/D06_longrun_health.md`
   §F6) as the basis for the tolerance band, mirroring
   `test_generated_frontier_3_42_extended_population_stability`'s docstring citing its own investigation.

Scope this test to `urban_political_seed123_500t` only — do not add sibling
`urban_political_seed42_500t`/`urban_political_seed456_500t` variants unless Step 1's repro was
independently run against them too (out of this ticket's literal AC; would require its own repro evidence,
not assumed from one seed's result).

**Do NOT touch:** `test_generated_frontier_3_42_extended_population_stability` itself (read-only
reference); `grade_anchors.json` (schema and committed `B`/`0.088` value for this anchor stay unchanged —
the guard is a separate assertion, not a fixture edit, per the precedent's explicit "schema stays
single-grade-string" rule); `HAZARD_KIND_MATCH_WORLDS`/`POPULATION_STABILITY_WORLDS`/`ANCHORED_WORLD_BANDS`
or any other existing list in this file; `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` in
`test_grade_regression.py`.

**Verify:** `pytest tests/unit/worldassembly/test_corpus_diversity.py -k cognition_grade_stability -m slow --resource-budget large -v` passes.

### Step 3b — (Fallback path) Tight bit-identical assertion test

*Only if Step 2 selects this path instead of 3a — mutually exclusive with Step 3a.*

**Files:** `tests/unit/worldassembly/test_corpus_diversity.py` (new test function, same location as 3a
would occupy).

**Change:** Add `test_urban_political_seed123_500t_cognition_bit_identical_under_load` — same
idle-vs-induced-load structure as Step 1's repro (real throttled `Kernel`, no `audit_mode`), asserting
COGNITION's `event_count`/`raw_score`/`grade`/`loop_detected` are byte-identical between an idle run and
an induced-load run. Cite Step 1/2's repro evidence in the docstring as the basis for asserting
bit-identity is achievable for this anchor.

**Do NOT touch:** same guards as Step 3a.

**Verify:** `pytest tests/unit/worldassembly/test_corpus_diversity.py -k cognition_bit_identical -m slow --resource-budget large -v` passes.

### Step 4 — Record reliability status in `eval_matrix_results.md`

**Files:** `docs/simulation_quality/eval_matrix_results.md`.

**Change:** Append a new dated section (after the file's current last section, following its existing
convention of dated/ticketed headers — same append-only pattern
`TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` used):
`## COGNITION Loop-Detection Nondeterminism Verification (TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM)`.
Content:
- `urban_political_seed123_500t`'s COGNITION anchor (`B`, `0.088`), Step 1's idle-vs-load repro table
  (transcribed, not just referenced), and root cause (F6, cross-referenced to
  `docs/audits/D06_longrun_health.md` §F6).
- Reliability status using the established three-label vocabulary: **converted-to-tolerance** (if Step 3a
  was taken) or **stable** (if Step 3b was taken, since bit-identical is a stronger result than
  tolerance-bounded stability). Do not use **flagged-unverified** — this ticket's whole purpose is to
  resolve that classification for this anchor (it was previously an untested `FAST_ANCHOR_KEYS` entry per
  investigation's baseline confirmation).
- A pointer to the new test added in Step 3a or 3b.
- A note that `urban_political_seed42_500t`/`urban_political_seed456_500t` (sibling `FAST_ANCHOR_KEYS`
  entries) remain unverified against F6 — out of this ticket's scope, candidates for a future ticket if
  needed.

**Do NOT touch:** any earlier section of this file (existing per-world grade tables, D2-fix notes,
hazard-kind recompile notes, the ANCHOR-RELIABILITY-VERIFY section) — append-only, do not edit history.

**Verify:** Manual scan confirms `urban_political_seed123_500t` appears in the new section with exactly
one of the two applicable status labels and cited repro evidence.

### Step 5 — Full scoped regression verification

**Files:** None changed — verification only.

**Change:** Run, in order:
1. `git diff --stat src/engine/kernel.py` — must show no output (zero-diff AC, mirrors
   `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`'s own final AC).
2. `git diff --stat src/simulation_quality/weights.py config/simulation_quality/scoring_weights.yaml` —
   must show no output (confirms no accidental drift into the sibling ticket's territory).
3. `git diff --stat src/observability/event_extractor.py` — must show no output (confirms
   `decision_divergence_detected`'s dedup gating was not touched).
4. `pytest tests/simulation_quality/test_accumulator.py tests/simulation_quality/test_cognition_scorer.py tests/simulation_quality/test_weights.py tests/simulation_quality/test_information_scorer.py tests/simulation_quality/test_report.py tests/simulation_quality/test_quality_hub_integration.py -v` —
   all pass, including `test_duplicate_event_id_is_noop` unchanged.
5. `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v` — all pass, including
   `test_within_band_default_tolerance_unchanged` and `urban_political_seed123_500t`'s existing
   point-comparison entry (fixture untouched).
6. `pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid` —
   fixture structural integrity.
7. `pytest tests/simulation_quality/test_grade_regression.py -m slow -k urban_political -v` — sibling
   `SLOW_ANCHOR_KEYS` `urban_political_*` entries stay stable (already verified by
   `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`; must not regress).
8. `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget large -v` — full
   file including the new Step 3a/3b test and the untouched
   `test_generated_frontier_3_42_extended_population_stability`.

**Do NOT touch:** nothing changes in this step. If any command surfaces a regression, return to Step 3/4
to re-derive the tolerance band or re-document — do not patch thresholds to force a pass.

**Verify:** All 8 commands complete with the stated expected result; this is the evidence base for the
ticket's Test Summary.

### Step 6 — Update ticket file (close-out)

**Files:** `tickets/inprogress/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM.md`.

**Change:**
- **Implementation Notes**: summarize the confirmed root cause (F6, no COGNITION-local determinism bug),
  the repro's actual idle-vs-load numbers, which path (3a tolerance-guard or 3b bit-identical) was taken
  and why, and the `ENABLE_SELF_MODEL_COGNITION`-is-OFF finding (planning-time, confirmed empirically in
  Step 1) with a one-line pointer to `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` as the separate,
  explicitly-out-of-scope raw_score-magnitude cause.
- **Test Summary**: list the Step 5 commands and pass counts.
- **Files Changed**: `tests/unit/worldassembly/test_corpus_diversity.py`,
  `docs/simulation_quality/eval_matrix_results.md`, plus the two staging-artifact files
  (`repro_sweep.md` is working evidence, not migrated as a fourth stored artifact — same disposition as
  `raw_calibration_sweep.md`'s precedent).
- **Completion Summary**: one paragraph confirming all three ACs are met and `src/engine/kernel.py` has a
  zero diff.

**Do NOT touch:** Scope/Out of Scope/Acceptance Criteria sections (already amended twice; this step only
fills in the close-out sections).

**Verify:** All six required ticket sections (Status, Implementation Notes, Test Summary, Files Changed,
Completion Summary, plus Status flips to DONE) are filled before the ticket moves to `tickets/done/`.

## Scope Guards

- **`src/engine/kernel.py`** — zero diff, checked explicitly in Step 5. It is the measured subject, not a
  target; no change to the tick-budget watchdog (`kernel.py:420-442`) or mid-tick emergency throttle
  (`kernel.py:574-601`) anywhere in this plan.
- **`src/simulation_quality/weights.py`** and **`config/simulation_quality/scoring_weights.yaml`** — zero
  diff, checked explicitly in Step 5. The cross-pillar flat-key collision is
  `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`'s territory; this plan does not depend on or block on it.
- **`src/observability/event_extractor.py`**'s `decision_divergence_detected` gating (lines 477-496) —
  zero diff, checked explicitly in Step 5. Do not add an "already-emitted" dedup gate to this event type
  as a shortcut fix — that changes gameplay-observable SimQ event semantics for all runs, a bigger and
  different change than guarding one anchor against throttle variance (per investigation's Anti-Drift
  Hazards).
- **`SLOW_ANCHOR_KEYS`** (`test_grade_regression.py`) — no entries added, removed, or reclassified.
  `urban_political_seed123_500t` stays a `FAST_ANCHOR_KEYS` entry; this ticket adds a supplementary guard
  test alongside it, it does not migrate the anchor between tiers.
- **`grade_anchors.json`** — no value or schema change. The anchor's committed `B`/`0.088` for
  `urban_political_seed123_500t` COGNITION is untouched; the new guard test is a separate assertion.
- **`docs/guidelines/intentional_divergences.md`**'s F6 entry — not reopened, not added (the documentation
  gap noted in investigation.md is explicitly out of scope, awareness-only).
- **`test_generated_frontier_3_42_extended_population_stability`** — read-only reference pattern, not
  modified.
- **`test_duplicate_event_id_is_noop`** (`test_accumulator.py`) and **`test_within_band_default_tolerance_unchanged`**
  (`test_grade_regression.py:547-553`) — must keep passing unchanged; both are explicitly checked in
  Step 5.
- Do not implement both Step 3a and Step 3b — Step 2's decision selects exactly one.
- Do not expand this ticket's guard to `urban_political_seed42_500t`/`urban_political_seed456_500t` or
  any other `FAST_ANCHOR_KEYS` entry beyond `urban_political_seed123_500t` — out of this ticket's literal
  AC; note as future-ticket candidates in Step 4 only.

## Dependency Map

- Step 1 → Step 2 (the decision requires Step 1's actual repro numbers; cannot be pre-decided).
- Step 2 → Step 3a **or** Step 3b (exactly one, chosen by Step 2's classification).
- Step 3a/3b → Step 4 (the reliability-status label and test pointer require knowing which path was
  taken and that the test passes).
- Step 4 and Step 3a/3b's own passing state jointly feed Step 5 (full regression verification needs the
  new test and the doc update both in place).
- Step 5 → Step 6 (ticket close-out cites Step 5's verification results).
- No step depends on `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` landing first, in either direction.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Root cause identified with file:line evidence, explicit F6-vs-COGNITION-local determination | Already established in investigation.md; restated in Step 6 Implementation Notes | Step 1/2's repro data corroborates the investigation's static-analysis finding |
| A deliberate repro (controlled induced load) demonstrates the bug before the fix/guard, and its absence/bounded-tolerance containment after | Step 1 (before), Step 3a or 3b (after) | Step 1's `repro_sweep.md` data + `pytest ... -k cognition_grade_stability` (or `cognition_bit_identical`) `-m slow` |
| F6/kernel-throttle path: `urban_political_seed123_500t`'s COGNITION check converted to tolerance-based multi-trial guard, reliability status recorded in `eval_matrix_results.md` | Step 3a + Step 4 | `pytest tests/unit/worldassembly/test_corpus_diversity.py -k cognition_grade_stability -m slow` + manual scan of Step 4's new section |
| No regressions in `test_grade_regression.py` or COGNITION scorer/self-model test suites | Step 5 | Commands 4-8 in Step 5 |

## Anti-Drift Notes

- **`decision_divergence_detected` has no dedup gate by design (confirmed, not a bug)** — the natural
  instinct on reading `event_extractor.py:477-496` is to add a per-entity cooldown like
  `_emitted_stale_leads`/`_emitted_social_memory`/`_emitted_contract_milestones` use elsewhere in the same
  file. Resist it: that is a distinct, much larger-blast-radius design decision (changes SimQ event
  semantics for every run, not just throttled ones) that needs its own ticket per investigation's explicit
  hazard note, not a fold-in here.
- **`event_id` is not content-derived** (`uuid.uuid4().hex` default factory,
  `src/observability/events.py:56`) — a real design smell flagged by investigation but confirmed not the
  cause of this symptom. Do not "fix" it as a side effect; it touches every `SimulationEvent` construction
  path repo-wide, including the stream-republish round-trip in `event_recorder.py:134-147`.
- **Do not conflate `urban_political_seed123_500t` (`FAST_ANCHOR_KEYS`) with the 18 already-verified
  `SLOW_ANCHOR_KEYS`** — `ANCHOR-RELIABILITY-VERIFY`'s "18/18 stable" result says nothing about this key;
  it was explicitly excluded from that sweep. This ticket is the first test of that boundary assumption
  for this specific anchor.
- **Derive the tolerance band from Step 1's actual measured spread, never invented numbers** — same
  requirement `test_generated_frontier_3_42_extended_population_stability`'s tick-900/1000 floors were
  held to (derived from that ticket's own two-run divergence data, not guessed).
- **`weights.py`'s collision inflates `raw_score` magnitude on every run, load-independent** — do not be
  surprised if Step 1's idle-run `raw_score` for a 2-event baseline is not exactly the committed anchor's
  `11.0`; that anchor was presumably calibrated under a different point in `scoring_weights.yaml`'s
  history. This magnitude question belongs to `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`, not this
  ticket — Step 1/2's classification should focus on **event_count**/**loop_detected**/**grade** shifts
  (the F6-attributable signal), not on whether `raw_score`'s absolute value matches `11.0` exactly.
- **`ENABLE_SELF_MODEL_COGNITION` is OFF for `urban_political`'s actual calibration profile** — confirmed
  during planning (`config/simulation_quality/profiles/urban_political.yaml` has no such flag;
  `src/domains/optimization/feature_flags.py:15` defaults it OFF). This does not block the plan because
  `decision_divergence_detected` — the event actually driving the 2→119 explosion — does not depend on the
  self-model bundle. Step 1 re-confirms this empirically via `_load_profile_feature_flags` output; if the
  repro's actual feature-flag dump contradicts this (i.e. shows `ENABLE_SELF_MODEL_COGNITION: "ON"`),
  treat that as new evidence requiring investigation.md to be updated before proceeding to Step 2.

## Unresolved Questions

None. Step 2's idle-vs-load classification is the one genuine fork in this plan, and it is handled as an
explicit in-plan decision point (Step 2) rather than a pre-implementation unknown — the primary/expected
path (Step 3a) is fully specified, and the fallback (Step 3b) is fully specified as a mutually exclusive
alternative, so no orchestrator decision is required before the implementer starts.
