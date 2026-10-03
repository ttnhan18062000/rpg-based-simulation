---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY
artifact_type: plan
tags: [simulation-quality, calibration, determinism, corpus]
---

# Implementation Plan — TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY

## Summary

This is a measurement-verification ticket, not a behavior change: re-run all 18 `SLOW_ANCHOR_KEYS`
three times each via `tools/calibrate_simq.py`, classify each key's per-pillar grade stability
against the existing ±1-letter `GRADE_ORDER` band, document a reliability status for all 18 keys in
`docs/simulation_quality/eval_matrix_results.md`, and — only for keys that turn out unstable —
add a grade-stability multi-trial guard test to `tests/unit/worldassembly/test_corpus_diversity.py`
following the `test_generated_frontier_3_42_extended_population_stability` pattern, reusing
`tools/calibrate_simq.py`'s internal functions directly (in-process, no subprocess) rather than
extending `grade_anchors.json`'s single-grade-string schema. `src/engine/kernel.py` is read-only
throughout — it is the object being measured, not modified. The full classification cannot be known
until Step 1's data exists, so Step 1 is data-gathering (real calibration runs, not yet a code/doc
change) and Steps 2-4 build on its output.

**Resolved decisions (see Investigation's Risks section for the open questions these answer):**
1. **Reruns per key: 3**, not 2 — investigation's timing measurement (33s/1000t for the largest
   world) puts the full 18×3 sweep at ~25-60 min wall-clock, comfortably affordable, and 3 trials
   give materially stronger statistical confidence than 2 at negligible added cost.
2. **Tolerance-guard shape for unstable keys**: a new, dedicated `@pytest.mark.slow` test per
   unstable world/tick-count pair in `tests/unit/worldassembly/test_corpus_diversity.py`, calling
   `tools/calibrate_simq.py`'s internal helpers (`_run_engine`, `_resolve_profile`,
   `_load_profile_feature_flags`, `_load_weights`, `_build_hub`, `_replay_jsonl_through_hub`)
   directly in-process across 3 trials, comparing each trial's per-pillar grade to the anchor via
   the same ±1-`GRADE_ORDER`-band rule already enforced in `test_grade_regression.py`. This does
   **not** touch `grade_anchors.json`'s schema — mirrors the precedent
   (`test_generated_frontier_3_42_extended_population_stability`) which lives entirely as a
   separate test with its own logic, not a fixture change.
3. **`make evaluate-full` AC-phrase resolution**: the ticket's AC is satisfied via the "equivalent
   scoped regression sweep" branch — `make simq-full-audit-slow` (equivalently
   `pytest tests/simulation_quality/test_grade_regression.py -m slow`) — never bare
   `make evaluate-full`, which is fast-tier-only (≤500t) and never touches any of the 18 keys.

## Steps

### Step 1 — Full 18-key × 3-trial calibration sweep, raw evidence capture

**Files:** None changed yet (data-gathering). Writes ephemeral output under `data/calibration/`
(gitignored) and a new working-evidence file
`staging_artifacts/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY/raw_calibration_sweep.md` (not one
of the three required artifacts — a transcription scratch file, since `data/calibration/` does not
survive to commit and the ticket's AC requires "grades observed per trial, not just a conclusion").

**Change:** For each of the 18 keys below, run `tools/calibrate_simq.py` 3 times at the key's
existing seed/ticks/profile. Trial 1 uses the canonical output path (no `--output` override, so it
lands at `data/calibration/{run_key}/quality_report.json` and lets
`test_grade_within_anchor_band_long_run` exercise — not skip — the 7 currently-missing keys after
this step). Trials 2 and 3 use `--output data/calibration/{run_key}_trial2` /
`..._trial3` to avoid clobbering trial 1 before all three are captured.

Invocation table (from investigation.md — profile omitted below defaults to `--name`):

| Key | `--name` | `--seed` | `--ticks` | `--profile` |
|---|---|---|---|---|
| `dungeon_crawl_seed42_1000t` | dungeon_crawl | 42 | 1000 | dungeon_crawl |
| `dungeon_crawl_seed123_1000t` | dungeon_crawl | 123 | 1000 | dungeon_crawl |
| `dungeon_crawl_seed456_1000t` | dungeon_crawl | 456 | 1000 | dungeon_crawl |
| `dungeon_crawl_seed42_2000t` | dungeon_crawl | 42 | 2000 | dungeon_crawl |
| `dungeon_crawl_seed123_2000t` | dungeon_crawl | 123 | 2000 | dungeon_crawl |
| `dungeon_crawl_seed456_2000t` | dungeon_crawl | 456 | 2000 | dungeon_crawl |
| `urban_political_seed42_1000t` | urban_political | 42 | 1000 | urban_political |
| `urban_political_seed123_1000t` | urban_political | 123 | 1000 | urban_political |
| `urban_political_seed456_1000t` | urban_political | 456 | 1000 | urban_political |
| `urban_political_seed42_2000t` | urban_political | 42 | 2000 | urban_political |
| `sandbox_world_seed42_1000t` | sandbox_world | 42 | 1000 | sandbox_world |
| `sandbox_world_seed42_2000t` | sandbox_world | 42 | 2000 | sandbox_world |
| `unit_faction_tension_seed42_1000t` | unit_faction_tension | 42 | 1000 | default (no profile file) |
| `unit_faction_tension_seed42_2000t` | unit_faction_tension | 42 | 2000 | default |
| `unit_selfmodel_pilot_seed42_1000t` | unit_selfmodel_pilot | 42 | 1000 | unit_selfmodel_pilot |
| `hero_guild_routing_seed42_1000t` | hero_guild_routing | 42 | 1000 | hero_guild_routing |
| `simq_routing_test_seed42_1000t` | simq_routing_test | 42 | 1000 | simq_routing_test |
| `generated_frontier_3_42_seed42_1000t` | generated_frontier_3_42 | 42 | 1000 | generated_frontier_3_42 |

Example: `python3 tools/calibrate_simq.py --ticks 1000 --seed 42 --name dungeon_crawl` (trial 1),
`python3 tools/calibrate_simq.py --ticks 1000 --seed 42 --name dungeon_crawl --output data/calibration/dungeon_crawl_seed42_1000t_trial2` (trial 2), etc.

After each invocation, transcribe the printed "Pillar breakdown" block (10 pillar grades) into
`raw_calibration_sweep.md` under a `## {run_key}` heading with three sub-entries (`trial1`,
`trial2`, `trial3`), each showing all 10 pillar grades verbatim. Do not summarize or round —
this raw table is the evidentiary basis Step 2 classifies from and Step 3 cites.

**Do NOT touch:** `src/engine/kernel.py` (read-only — the object under measurement);
`grade_anchors.json` (not edited this step); any `FAST_ANCHOR_KEYS` entry or its calibration data;
`config/simulation_quality/` files (must not drift); do not pass `audit_mode` or any flag that
disables the throttle — these must be real, throttled runs, matching the ticket's stated purpose.

**Verify:** `ls data/calibration/{run_key}/quality_report.json` exists for all 18 canonical
`run_key` values (confirms the 7 previously-missing keys are no longer skip-only). All 54 trial
invocations (18 × 3) completed without a crash/traceback; any invocation that fails to complete is
itself a finding — record it in `raw_calibration_sweep.md` rather than silently retrying with
different flags (e.g. do not add `audit_mode` to work around a crash).

### Step 2 — Classify each key: stable / unstable

**Files:** `staging_artifacts/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY/raw_calibration_sweep.md`
(append a `## Classification` section).

**Change:** For each of the 18 keys, compare each of the 3 trials' 10 pillar grades against the
key's committed anchor in `tests/simulation_quality/fixtures/grade_anchors.json`, using the exact
`_within_band` rule already in `tests/simulation_quality/test_grade_regression.py:140-148`
(`abs(GRADE_ORDER.index(actual) - GRADE_ORDER.index(anchor)) <= 1`, `GRADE_ORDER = ["D","C","B","A","S"]`).
A key is:
- **Stable**: every trial, every pillar, is within the ±1 band of the committed anchor.
- **Unstable**: at least one trial has at least one pillar outside the ±1 band, AND the divergence
  is consistent with the F6 throttle-timing mechanism (population/behavioral variance past
  tick ~300-320, not a deterministic-looking shift present in all 3 trials identically).
- **Escalate, do not classify** (per ticket Assumptions): if a key shows grade instability that
  looks like genuine content/RNG non-determinism rather than throttle-driven variance (e.g. all 3
  trials produce the *same* off-anchor grade, which would indicate a real drift, not run-to-run
  noise) — stop, do not fold this into Step 3/4, and report it for a separate follow-up ticket per
  the ticket's own Assumptions section.

Record the per-key classification (stable/unstable/escalate) in the new `## Classification`
section, one row per key, citing which trial/pillar triggered "unstable" if applicable.

**Do NOT touch:** any test or fixture file in this step — this is pure analysis of Step 1's already-
captured data. Do not widen `_within_band`'s tolerance to make a borderline key look stable.

**Verify:** All 18 keys have exactly one of the three classifications recorded, each with a cited
reason (trial data reference, not just a label).

### Step 3 — Document reliability status in `eval_matrix_results.md`

**Files:** `docs/simulation_quality/eval_matrix_results.md`.

**Change:** Add a new `## Anchor Reliability Verification (TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY)`
section (append near the end of the file, after the existing `## Long-Run Hot-Pillar Anchors`
section at line 1415, following the file's existing convention of dated/ticketed section headers).
For each of the 18 `SLOW_ANCHOR_KEYS`, add one entry stating:
- The key name and its 3 trials' per-pillar grades (a compact table, all 10 pillars × 3 trials —
  transcribed from `raw_calibration_sweep.md`, not just referenced).
- Its reliability status: exactly one of **stable**, **converted-to-tolerance**, or
  **flagged-unverified** (per the ticket's AC — these three labels only; "escalate" cases from
  Step 2 are documented as flagged-unverified here with a pointer to the separate follow-up ticket
  filed for the genuine-divergence finding, not silently dropped).
- For **converted-to-tolerance** keys: a pointer to the new test added in Step 4
  (`test_{world}_{ticks}t_grade_stability` in `test_corpus_diversity.py`).
- For **flagged-unverified** keys: the specific reason a tolerance-guard conversion wasn't a clean
  fit (per ticket Scope, option (b)).

**Do NOT touch:** any earlier section of this file (the existing per-world grade tables, D2-fix
notes, hazard-kind recompile notes, etc.) — append-only, do not edit history.

**Verify:** Manual scan confirms all 18 `SLOW_ANCHOR_KEYS` string values appear in the new section,
each with exactly one of the three status markers and cited per-trial grade evidence (this is the
"Reliability-status completeness guard" from test_plan.md's Anti-Drift Test Guards — performed as a
grep/read check, not a new automated test, per the test_plan's own "optional-but-recommended"
framing of a dedicated completeness test — out of scope to add here since it would exceed the
ticket's documentation-only AC).

### Step 4 — Grade-stability multi-trial guard tests for unstable keys

**Files:** `tests/unit/worldassembly/test_corpus_diversity.py`.

**Change:** For each key classified **unstable** in Step 2 (count unknown until Step 2 completes —
plausibly zero, given the single confirmatory re-run in investigation.md matched exactly), add one
`@pytest.mark.slow` test named `test_{world}_{ticks}t_grade_stability`, grouped by world/tick-count
pair (not one test per seed, matching the existing precedent's grouping). Each test:
1. Imports `tools.calibrate_simq`'s internal helpers: `_run_engine`, `_resolve_profile`,
   `_load_profile_feature_flags`, `_load_weights`, `_build_hub`, `_replay_jsonl_through_hub`.
2. Runs 3 independent same-seed trials of the real, throttled `Kernel` (via `_run_engine` — never
   sets `audit_mode`), replays each trial's JSONL through a `QualityHub` built with
   `_build_hub(weights, tmp_dir, run_id)` where `tmp_dir` is a `tempfile.TemporaryDirectory()` (not
   `data/calibration/` — keeps this test hermetic and avoids clobbering Step 1's evidence files).
3. Extracts each trial's 10 pillar grades from `hub.get_quality_report().pillars`.
4. Asserts every trial's every pillar grade is within the ±1-`GRADE_ORDER` band of the key's
   committed anchor in `grade_anchors.json` — reproduce the band-comparison logic locally in this
   test file (a small local `GRADE_ORDER` list + comparison, ~10 lines) rather than importing from
   `tests/simulation_quality/test_grade_regression.py`, consistent with this file's existing
   convention of self-contained tests with their own hardcoded thresholds
   (`test_generated_frontier_3_42_extended_population_stability` does not import from
   `test_grade_regression.py` either).
5. On failure, the assertion message must show the full per-trial, per-pillar grade table (mirrors
   the existing test's `Per-trial values: {...}` pattern) — not just "failed."

If Step 2 classifies **zero** keys as unstable, this step is a documented no-op: state explicitly in
`raw_calibration_sweep.md`'s Classification section and in the Step 3 doc update that no
conversions were needed — do not skip this documentation silently (per test_plan.md's explicit
callout that this is "a valid outcome... must still be documented as such").

**Do NOT touch:** `test_generated_frontier_3_42_extended_population_stability` (the existing
population-stability precedent — read-only reference, not to be modified);
`grade_anchors.json` (schema and values unchanged by this step); `HAZARD_KIND_MATCH_WORLDS` /
`POPULATION_STABILITY_WORLDS` or any other existing world list in this file; any `FAST_ANCHOR_KEYS`-
tier logic.

**Verify:** `pytest tests/unit/worldassembly/test_corpus_diversity.py -k "grade_stability" -m slow -v`
— every newly added test passes. If zero tests were added, this command has no matches (expected,
and not a failure).

### Step 5 — Full scoped regression verification

**Files:** None changed — verification only.

**Change:** Run, in order:
1. `git diff --stat src/engine/kernel.py` — must show no output (zero-diff AC).
2. `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"` — fast-tier isolation
   guard; pass/fail counts must be unchanged from pre-ticket baseline.
3. `pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid`
   — fixture structural integrity (guards against any accidental `grade_anchors.json` malformation).
4. `pytest tests/simulation_quality/test_grade_regression.py -m slow` — all 18 `SLOW_ANCHOR_KEYS`
   must now execute (not skip, per Step 1) and pass.
5. `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow` and
   `pytest tests/unit/worldassembly/test_corpus_diversity.py -m "not slow"` — full file, both tiers,
   including any Step 4 additions and the untouched `test_generated_frontier_3_42_extended_population_stability`.
6. `make simq-full-audit-slow` — the ticket AC's "equivalent scoped regression sweep" (bare
   `make evaluate-full` is explicitly insufficient per investigation.md — do not substitute it).
7. `git diff --stat data/content/ config/ data/worlds/` — must show no output (no collateral content/
   config/world-compile drift).

**Do NOT touch:** nothing changes in this step; it is pure verification. If any command surfaces a
regression, return to Step 2/3/4 to re-classify or re-document — do not patch test thresholds to
force a pass.

**Verify:** All 7 commands above complete with the stated expected result. This step's own output
is the evidence for the ticket's Test Summary section at close-out.

## Scope Guards

- `src/engine/kernel.py` — zero diff, in every step. It is the measured subject, not a target.
- No change to the tick-budget watchdog (`kernel.py:420-442`) or mid-tick emergency throttle
  (`kernel.py:574-601`) — documented, intentional behavior per `docs/engine/kernel.md`.
- No widening of the existing ±1-letter `GRADE_ORDER` band (`_within_band`,
  `test_grade_regression.py:140-148`) to make an unstable key appear stable.
- No edits to `grade_anchors.json` values or schema, except in the narrow escalation case (Step 2)
  where a genuine non-throttle divergence is found — and even then, the fix is a **separate follow-
  up ticket**, not an in-line edit here.
- No use of `audit_mode=True` anywhere in the re-runs or new tests — it disables both throttle paths
  and would measure a materially different, non-representative scenario.
- No expansion of the calibration corpus (new worlds, seeds, or pillars) — Phases 2-4 of the roadmap,
  explicitly gated on this ticket.
- No fixing of the `moon_cave`/`bandit_road`/`town_council` hazard-kind or hazard-exposure content
  gaps (P2-O/P2-Q) even if re-runs surface them again — report, do not fix here.
- No edits to `FAST_ANCHOR_KEYS`, `test_grade_within_anchor_band` (the fast-tier test), or any
  fast-anchor calibration data.
- No edits to `HAZARD_KIND_MATCH_WORLDS`, `POPULATION_STABILITY_WORLDS`, or
  `test_generated_frontier_3_42_extended_population_stability` in `test_corpus_diversity.py`.
- No edits to `config/simulation_quality/scoring_weights.yaml`, `grade_thresholds.yaml`, or
  `detection_params.yaml`.
- No parity ledger status changes (`docs/parity_ledger/world_dynamics.yaml::WORLD-029`/`WORLD-060`,
  `docs/parity_ledger/infrastructure.yaml::INFRA-258`) — unless Step 2's escalation path fires, in
  which case the parity question belongs to the separate follow-up ticket, not this one.

## Dependency Map

- Step 1 → Step 2 (classification requires Step 1's raw trial data; cannot be pre-decided).
- Step 2 → Step 3 (doc status labels require the classification).
- Step 2 → Step 4 (which keys, if any, get a new test requires the classification; Step 4 may be a
  documented no-op if Step 2 finds zero unstable keys).
- Step 3 and Step 4 can proceed in parallel once Step 2 is complete (independent files: one is docs,
  one is a test file).
- Step 5 depends on Steps 1-4 all being complete (it verifies the combined result).
- No step depends on anything outside this ticket's own artifacts.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| All 18 keys re-run 2-3× (3×, per resolved decision) via `tools/calibrate_simq.py`, same-machine back-to-back | Step 1 | Step 1's own `ls data/calibration/{run_key}/` check + `raw_calibration_sweep.md` contents |
| `eval_matrix_results.md` documents reliability status (stable/converted-to-tolerance/flagged-unverified) for all 18 keys, with cited per-trial evidence | Step 3 | Manual completeness scan (Step 3 Verify) |
| Every "unstable" key converted to tolerance guard or explicitly flagged with reason | Step 4 (conversion) + Step 3 (flagging text) | `pytest tests/unit/worldassembly/test_corpus_diversity.py -k grade_stability -m slow` |
| `src/engine/kernel.py` zero diff | Scope Guard, checked in Step 5 | `git diff --stat src/engine/kernel.py` |
| `pytest tests/simulation_quality/test_grade_regression.py -m slow` and new/modified tolerance-guard tests pass | Step 5 | Commands 4 and 5 in Step 5 |
| `make evaluate-full` (resolved: `make simq-full-audit-slow`) reports 0 regressions | Step 5 | Command 6 in Step 5 |
| No parity ledger entry requires a status change (absent an unrelated genuine-divergence escalation) | Scope Guard | Step 5's own review; no parity file edits expected in `git status` |

## Anti-Drift Notes

- **`data/calibration/` is gitignored and ephemeral.** Nothing written there in Step 1 survives to
  commit. `raw_calibration_sweep.md` (in `staging_artifacts/`) is the durable transcription of
  evidence for this ticket's session; `eval_matrix_results.md` (Step 3) is the durable, committed
  record. Do not treat the raw JSON reports themselves as sufficient evidence at close-out.
  `raw_calibration_sweep.md` is a working file, not one of the three required staging artifacts
  (`plan.md`/`investigation.md`/`test_plan.md`) — it does not get migrated to `stored_artifacts/`
  as a fourth artifact type; its content is fully absorbed into `eval_matrix_results.md` by Step 3,
  so it can be left behind or discarded once Step 3 is complete and verified.
- **Do not silently substitute `audit_mode=True`** for any re-run or new test, in Steps 1 or 4 — it
  structurally disables the throttle paths under measurement and would produce a false "stable"
  reading that doesn't reflect real/CI conditions. `tools/calibrate_simq.py`'s `_run_engine` never
  sets `audit_mode`; keep it that way.
- **Distinguish throttle-timing instability from genuine content/RNG non-determinism** (Step 2's
  "Escalate" path). A key where all 3 trials land on the *same* off-anchor grade is not throttle
  noise — throttle-driven variance should look like run-to-run scatter, not a consistent shift.
  Escalate the latter as a separate ticket per the ticket's own Assumptions section; do not fold it
  into a tolerance guard, which would mask a real regression.
- **`grade_anchors.json`'s schema stays single-grade-string.** The tolerance-guard pattern (Step 4)
  lives entirely in `test_corpus_diversity.py`, mirroring
  `test_generated_frontier_3_42_extended_population_stability`, which never touches the fixture.
  If an implementer is tempted to add a `tolerance_band` or list-valued field to
  `grade_anchors.json` to make Step 4 "cleaner," that is scope creep — resist it; the precedent
  already proves the separate-test pattern works without a fixture change.
- **`make evaluate-full` alone gives a false "0 regressions" signal for this ticket** — it is
  fast-tier-only (≤500t) and never touches any of the 18 `SLOW_ANCHOR_KEYS`. Always pair it with
  (or substitute) `make simq-full-audit-slow` / `pytest tests/simulation_quality/test_grade_regression.py -m slow`
  when reporting this ticket's AC as satisfied.
- **Timing budget**: investigation measured ~33s/1000t for the largest world (44 entities); full
  18×3 sweep extrapolates to ~25-60 min wall-clock. If actual per-world costs run significantly
  higher than this extrapolation (investigation flagged ±30-50% variance as plausible, driven by
  event density / JSONL replay time), that is worth noting in `raw_calibration_sweep.md` but is not
  grounds to reduce the sweep to fewer than 3 trials/key or fewer than all 18 keys — the whole
  premise of this ticket is that a single-run sample size is what caused the original problem.

## Deviations

- **Step 1 execution mechanics**: ran the 54 invocations via a single shell loop script (not one
  invocation at a time) to fit the ~25-40 min wall-clock sweep inside one background process rather
  than 54 separate tool calls. This is a process/tooling detail, not a scope deviation — every
  invocation still used the exact `--ticks`/`--seed`/`--name`/`--output` arguments from the plan's
  table, ran the real throttled `Kernel` with no `audit_mode`, and all 54 completed without a crash.
  Actual measured cost (~40 min wall-clock) landed inside the plan's own ~25-60 min estimate.
- **Step 5 verification hiccup (not a plan deviation, a self-corrected invocation mistake)**: the
  first `tests/unit/worldassembly/test_corpus_diversity.py -m slow` verification run was invoked
  without `--resource-budget large` and hit pytest's own 60s default "medium" resource-budget
  `TimeoutError` on `test_generated_frontier_3_42_extended_population_stability` (its 3-trial×1000-tick
  body routinely takes 70-100s+). This matches a finding already on record in
  `stored_artifacts/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE/plan.md` (that test's
  own precedent required `--resource-budget large`, matching `.github/workflows/test.yml:230`'s CI
  invocation) — re-running with the correct flag passed cleanly (17 passed, 37 deselected). No plan
  step, scope guard, or acceptance criterion required revision; this was purely a missing CLI flag on
  a verification command, caught and corrected within Step 5 itself.
- **No other deviations.** All 18 keys classified `stable`, matching the plan's own stated expectation
  ("plausibly zero" unstable keys) — Step 4's tolerance-guard-conversion path was not exercised, exactly
  as the plan anticipated as a valid, documented outcome.
