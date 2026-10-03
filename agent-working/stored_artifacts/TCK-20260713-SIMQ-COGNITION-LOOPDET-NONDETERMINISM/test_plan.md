---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM
artifact_type: test_plan
tags: [simulation-quality, cognition, self-model, determinism]
---

# Test Plan — TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM

## Regression Surface

Existing tests that must keep passing (grouped by domain):

**Unit — SimQ scoring core**
- `tests/simulation_quality/test_accumulator.py` — all 17 tests, especially
  `test_duplicate_event_id_is_noop`, `test_loop_detection_fires_above_threshold`,
  `test_loop_detection_does_not_fire_below_threshold`, `test_accumulator_respects_injected_window_size`,
  `test_accumulator_respects_injected_loop_threshold` — the exact mechanics this investigation
  confirmed are functioning correctly (loop detection is a correct function of its inputs; dedup
  works for identical `event_id`s). Any fix must not change this behavior.
- `tests/simulation_quality/test_cognition_scorer.py` — all classes, especially
  `TestSelfModelUpdated` and `TestDecisionDivergence` (lines 91-116) — verifies `self_model_updated`
  and `decision_divergence_detected` still map to `self_model_active`/`subjective_divergence` tags
  with the correct `ScoreRecord` shape.
- `tests/simulation_quality/test_weights.py` — all 13 tests, especially `test_getitem_known_key`,
  `test_all_10_pillars_present`, `test_dungeon_crawl_profile_overrides`,
  `test_urban_political_profile_overrides` — must keep passing regardless of whether the weights
  collision (Risk #1 in investigation.md) is fixed in this ticket or filed separately.
- `tests/simulation_quality/test_information_scorer.py` — `subjective_divergence` is also scored by
  `InformationScorer` (`scorers/information.py:140`); any weights-collision-adjacent change must not
  silently change INFORMATION's own anchors.
- `tests/simulation_quality/test_report.py` — `QualityReportBuilder` snapshot/grade-assignment logic
  (`quality_report.py`), unaffected by this ticket's scope but must not regress.
- `tests/simulation_quality/test_quality_hub_integration.py` — `QualityHub.on_envelope` dispatch and
  translation path; must confirm envelope delivery remains single-fire (no duplicate `on_envelope`
  calls) if anything in the queue/worker path is touched (it should not be, per Scope).

**Unit — observability event pipeline**
- `tests/unit/observability/` — any existing `EventRecorder`/`EventExtractor`/`ObservabilityEventEnvelope`
  tests (locate via `find tests/unit/observability -iname "*event*"`) — confirm `event_extractor.py`'s
  `self_model_updated`/`decision_divergence_detected` emission logic is untouched unless the fix
  specifically requires a gating change (Out of Scope per Anti-Drift Hazards unless explicitly
  re-scoped).

**SimQ grade regression (fast tier — includes this ticket's anchor)**
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"` — full `FAST_ANCHOR_KEYS`
  parametrized sweep, including `urban_political_seed123_500t` itself
  (`test_grade_regression.py:70`). Must confirm this anchor's current committed grade/score (B,
  0.088 for COGNITION) still passes `_within_band` and `_within_score_tolerance` against whatever
  calibration data is on disk after this ticket's changes — do not let a fix or guard silently
  regress the fast-tier baseline for this or any other anchor.
- `pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid`
  — fixture integrity.
- `pytest tests/simulation_quality/test_grade_regression.py -m slow -k urban_political` — confirm no
  collateral effect on `urban_political_seed42_1000t`/`urban_political_seed123_1000t`/
  `urban_political_seed456_1000t`/`urban_political_seed42_2000t` (all `SLOW_ANCHOR_KEYS`, already
  verified stable by `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` — must stay stable).

**Tolerance-guard pattern precedent (if F6/tolerance-guard path is chosen)**
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget large` — the
  pattern this ticket's guard (if added) must sit alongside without breaking, especially
  `test_generated_frontier_3_42_extended_population_stability` (lines 289-374), the template.

## New Tests Required

Per acceptance criteria, in priority order:

1. **Controlled repro test/script (AC #2 — "a deliberate repro... demonstrates the bug before the
   fix/guard, and its absence/bounded-tolerance containment after")**
   - Category: integration / manual-instrumented-drive (mirrors
     `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`'s methodology — not
     necessarily a permanent pytest test, but must be reproducible and documented).
   - What it verifies: runs `urban_political` seed 123, 500 ticks, via the real throttled `Kernel`
     (no `audit_mode`), twice — once under idle conditions, once under deliberately induced
     concurrent CPU load (e.g. `stress-ng --cpu $(nproc) --timeout 600s &` or a Python
     multiprocessing busy-loop pool started before the drive and killed after, matching the
     ticket's own description of "~30 minutes of sustained concurrent system load" — a shorter
     induced-load window is acceptable if it still reliably produces elevated `budget_warnings`/
     `watchdog_trips` counts, confirmed via `kernel._status` inspection or log grep for "exceeded
     budget"/`WatchdogTrip`, matching `ANCHOR-RELIABILITY-VERIFY`'s `raw_calibration_sweep.md`
     evidence style). Captures `quality_report.json`'s COGNITION `event_count`/`raw_score`/
     `loop_detected` for each run, plus `budget_warnings`/`watchdog_trips` counts, for direct
     before/after comparison.
   - Where it should live: a working-evidence file under
     `staging_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/repro_sweep.md` (mirrors
     `raw_calibration_sweep.md`'s precedent — not a committed test, but required evidence for the
     ticket's Implementation Notes).

2. **Weights-collision regression guard (recommended as a *separate* follow-up ticket per
   investigation.md Risk #1 — list here so it is not silently dropped)**
   - Test name: `test_no_duplicate_rule_keys_across_pillars` (or equivalent).
   - Category: unit / architecture guard.
   - What it verifies: `ScoringWeights.load()` (or a dedicated validation step) raises/warns if the
     same rule key appears in more than one pillar section of `scoring_weights.yaml`, OR
     `ScoringWeights.__getitem__` becomes pillar-scoped instead of globally flat. **Do not implement
     this in this ticket unless the orchestrator explicitly re-scopes it here** — it is flagged as a
     new test to write in whichever ticket ends up owning the weights.py fix.
   - Where it should live: `tests/simulation_quality/test_weights.py`.

3. **If root cause is confirmed F6-only for the event-count mechanism (expected outcome per
   investigation.md): tolerance-based multi-trial guard for `urban_political_seed123_500t`'s
   COGNITION check**, per ticket AC and Scope's explicit instruction to follow
   `test_generated_frontier_3_42_extended_population_stability`'s pattern.
   - Test name: `test_urban_political_seed123_500t_cognition_grade_stability` (or a
     multi-anchor-key variant if other `urban_political_*_500t` FAST_ANCHOR_KEYS entries are found
     to need the same treatment during repro).
   - Category: integration / slow (multi-trial, real throttled `Kernel`).
   - What it verifies: N=3 same-seed (123) trials of `urban_political` at 500 ticks, real throttled
     `Kernel`, no `audit_mode`; asserts COGNITION's grade stays within the existing ±1-band
     (`GRADE_ORDER`) **and**, if the score-tolerance check (`_within_score_tolerance`,
     `test_grade_regression.py:172-185`) is also to be satisfied, asserts the *mean* normalized_score
     across trials stays within a documented, evidence-derived tolerance band (informed by the
     repro sweep's actual trial-to-trial spread — do not invent numbers, derive them the same way
     `test_generated_frontier_3_42_extended_population_stability`'s floors were derived from its own
     two-run divergence data).
   - Where it should live: `tests/unit/worldassembly/test_corpus_diversity.py` (co-located with the
     existing tolerance-guard pattern, per ticket Scope's explicit instruction) — **not**
     `test_grade_regression.py` itself, matching the precedent (that file stays point-comparison
     against committed calibration JSON; the tolerance guard lives alongside its sibling pattern).
   - Must also update `docs/simulation_quality/eval_matrix_results.md` with this anchor's
     reliability status (stable / converted-to-tolerance / flagged-unverified), per
     `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`'s established process — this ticket's AC requires
     it explicitly ("this scenario is not left as an unguarded single-run point comparison either
     way").

4. **If repro instead shows bit-identical output is achievable (i.e. a genuinely COGNITION-local,
   independent-of-F6 cause is found — not the expected outcome per current evidence, but must be
   tested for, not assumed away)**:
   - Test name: `test_urban_political_seed123_500t_cognition_bit_identical_under_load` (or similar).
   - Category: integration.
   - What it verifies: same scenario, idle vs. induced-load runs produce byte-identical
     `quality_report.json` COGNITION section.
   - Where it should live: `tests/unit/worldassembly/test_corpus_diversity.py`, adjacent to the
     tolerance-guard tests, but as a tight assertion instead — only add this test if the repro
     actually supports it; do not add both a tight-assertion test and a tolerance-guard test for the
     same anchor.

## Scoped Pytest Commands

```bash
# Core SimQ scoring unit tests (fast, must always pass)
pytest tests/simulation_quality/test_accumulator.py tests/simulation_quality/test_cognition_scorer.py \
  tests/simulation_quality/test_weights.py tests/simulation_quality/test_information_scorer.py \
  tests/simulation_quality/test_report.py tests/simulation_quality/test_quality_hub_integration.py -v

# Fast-tier anchor regression (includes urban_political_seed123_500t)
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v

# Slow-tier urban_political anchors (already-verified-stable sibling keys — must stay stable)
pytest tests/simulation_quality/test_grade_regression.py -m slow -k urban_political -v

# Tolerance-guard pattern precedent + any new guard added to this file
pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget large -v

# If a weights.py change is made in this ticket (only if explicitly re-scoped — see Risk #1):
pytest tests/simulation_quality/ -v
```

Do not run `pytest tests/` — scope to `tests/simulation_quality/` and
`tests/unit/worldassembly/test_corpus_diversity.py` as above, per repo Testing Rule.

## Anti-Drift Test Guards

- **`test_duplicate_event_id_is_noop` (existing, `test_accumulator.py`) must keep passing unchanged**
  — confirms the dedup mechanism itself is not touched. If a fix mistakenly "improves" dedup logic
  (e.g. tries to dedupe by tick+entity+event_type instead of `event_id`), this test's semantics
  would need deliberate re-authoring, which is a signal the fix has scope-crept beyond this ticket's
  boundary (dedup logic was confirmed *not* the root cause).
- **A guard that asserts `kernel.py`'s watchdog/throttle behavior is byte-for-byte unchanged** — e.g.
  `git diff --stat src/engine/kernel.py` must be empty at Finalize, mirroring
  `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`'s own verification step exactly (that ticket ran
  this exact check as its final AC). Add this as an explicit manual verification step, not
  necessarily a pytest test, since it is a diff-emptiness check.
- **If a weights.py fix is explicitly re-scoped into this ticket**: a guard confirming that fixing
  the collision does not silently change any *other* anchor's committed grade/score beyond the
  documented tolerance — run the full `FAST_ANCHOR_KEYS` + `SLOW_ANCHOR_KEYS` sweep
  (`pytest tests/simulation_quality/test_grade_regression.py -v`, both fast and slow) and diff
  against the pre-change baseline, since 7 confirmed colliding keys span 4 pillars
  (COGNITION/INFORMATION/ECONOMY/WORLD) — any anchor exercising `belief_active`,
  `subjective_divergence`, `knowledge_rot`, `omniscience_collapse`, `ecology_cycling`,
  `ecology_broken`, or `knowledge_economy_active` is a candidate for a magnitude shift. This is
  exactly why investigation.md recommends filing this as a separate ticket instead — the blast
  radius is large enough to deserve its own dedicated test sweep and its own anchor-update pass,
  not a side effect of a loop-detection-nondeterminism ticket.
- **`test_within_band_default_tolerance_unchanged` (existing, `test_grade_regression.py:547-553`)**
  must keep passing — guards against silently widening the ±1-letter band as a shortcut to make an
  unstable anchor "pass" instead of properly converting it to a tolerance-guard or investigating
  further.
