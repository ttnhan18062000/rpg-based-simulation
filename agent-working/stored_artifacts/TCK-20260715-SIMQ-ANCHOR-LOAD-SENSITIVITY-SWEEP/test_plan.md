---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP
artifact_type: test_plan
tags: [simulation-quality, calibration, determinism]
---

# Test Plan — TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP

## Regression Surface

Existing tests that must keep passing, grouped by domain.

**Unit — SimQ scoring core (unaffected by this ticket's scope, must not regress)**
- `tests/simulation_quality/test_accumulator.py` — all tests, especially
  `test_duplicate_event_id_is_noop`, `test_loop_detection_fires_above_threshold` /
  `test_loop_detection_does_not_fire_below_threshold` — confirms the dedup/loop-detection
  mechanics this ticket's investigation confirmed are functioning correctly per their
  inputs are untouched.
- `tests/simulation_quality/test_cognition_scorer.py`, `test_social_scorer.py`,
  `test_combat_scorer.py`, `test_progression_scorer.py`, `test_narrative_scorer.py`,
  `test_economy_scorer.py` — the 6 scorers whose pillars are represented in this
  ticket's 14 anchors; confirms `EVENT_TYPES` → `ScoreRecord` mapping is unaffected by
  any guard added here.
- `tests/simulation_quality/test_weights.py` — all tests, especially
  `test_real_config_seven_known_collisions_resolve_per_pillar` (INFRA-271's cited test,
  see Anti-Drift Test Guards) — this ticket does not touch `weights.py`; must stay green
  unmodified.
- `tests/simulation_quality/test_report.py`, `test_quality_hub_integration.py` —
  `QualityReportBuilder` and `QualityHub.on_envelope` dispatch, unaffected by this
  ticket's scope.

**Unit — observability event pipeline**
- Any existing `EventRecorder`/`EventExtractor` tests under `tests/unit/observability/`
  (locate via `find tests/unit/observability -iname "*event*"`) — confirms
  `event_extractor.py`'s emission logic for `decision_divergence_detected` and the
  SOCIAL/COMBAT/PROGRESSION/NARRATIVE delta-events audited in investigation.md is
  untouched (this ticket adds guards, it does not change emission logic, per Out of
  Scope).

**SimQ grade regression — both tiers, including all 14 anchors under investigation**
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v` — full
  `FAST_ANCHOR_KEYS` sweep (9 of the 14 anchors), plus the two standalone probe tests
  (`test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
  `test_urban_political_selfmodel_execution_isolated_grade_anchor`) and the structural
  tests (`test_grade_anchor_file_exists_and_valid`,
  `test_grade_anchors_entry_count_unchanged`, `test_within_band_default_tolerance_unchanged`,
  `test_score_tolerance_catches_within_band_regression`).
- `pytest tests/simulation_quality/test_grade_regression.py -m slow -v` — full
  `SLOW_ANCHOR_KEYS` sweep (5 of the 14 anchors: `simq_routing_test_seed42_1000t`,
  `hero_guild_routing_seed42_1000t`, `unit_selfmodel_pilot_seed42_1000t`,
  `urban_political_seed42_1000t`, `urban_political_seed123_1000t`) plus the other 13
  already-verified-stable `SLOW_ANCHOR_KEYS` — must confirm no collateral regression on
  the 13 anchors outside this ticket's scope.

**Tolerance-guard pattern precedents (whatever this ticket's guards sit alongside)**
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget large -v`
  — the existing `test_generated_frontier_3_42_extended_population_stability`
  (population-checkpoint tolerance guard, lines 293-373) and
  `test_urban_political_seed123_500t_cognition_bit_identical_under_load` (bit-identical
  guard, lines 395+) must both keep passing unmodified — this ticket's new guards join
  this file (or an equivalent) without altering either existing test.

## New Tests Required

One repro (documented, not necessarily a pytest test) plus one guard per anchor, per
AC #1/#2. In priority order, grouped by the investigation's findings:

### 1. Controlled idle-vs-load repro per anchor (AC #1)
- Category: integration / manual-instrumented-drive (mirrors
  `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`'s `repro_sweep.md` methodology
  exactly — idle repeats + escalating induced-load trials via `tools/calibrate_simq.py`'s
  internal helpers, `budget_warnings`/`watchdog_trips` counted from the
  `src.engine.kernel` logger).
- What it verifies: for each of the 14 anchors, whether the drifted pillar's
  `event_count`/`raw_score`/`normalized_score`/`grade`/`loop_detected` (or relevant
  subset) is bit-identical across idle and induced-load conditions, or genuinely
  variable. Per investigation.md's finding, this must specifically also capture *which
  tick* delta-based events (SOCIAL/PROGRESSION/NARRATIVE/COMBAT) land on across trials,
  not just final counts — since the hypothesized mechanism for those pillars is
  tick-shift, not event-count inflation.
- Where it should live: `staging_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md`
  (working-evidence file, mirrors both precedents' naming).
- Anchors sharing world/seed/mechanism (investigation.md Risk #5) may be grouped into
  fewer repro sessions if the planner judges the underlying mechanism identical — but
  each anchor's *result* (bit-identical vs. variable) must still be recorded
  individually, since `TCK-20260713`'s precedent proved throttle activity does not
  automatically imply score instability for every anchor.

### 2. Per-anchor regression guard (AC #2) — shape depends on repro outcome
For each of the 14 anchors, exactly one of the following two test shapes (not both):

**2a. Bit-identical guard** (if repro shows stable output across idle/load):
- Test name pattern: `test_<anchor>_<pillar>_bit_identical_under_load`
- Category: integration.
- What it verifies: idle vs. induced-load runs produce byte-identical pillar-level
  `event_count`/`raw_score`/`normalized_score`/`grade`/`loop_detected`.
- Where it should live: `tests/unit/worldassembly/test_corpus_diversity.py`, adjacent
  to `test_urban_political_seed123_500t_cognition_bit_identical_under_load` (the direct
  template, lines 395+).

**2b. Tolerance-based multi-trial guard** (if repro shows genuine variance):
- Test name pattern: `test_<anchor>_<pillar>_grade_stability`
- Category: integration / slow (multi-trial, real throttled `Kernel`, N=3 trials
  minimum per both precedents' established N).
- What it verifies: grade stays within the existing ±1-`GRADE_ORDER` band across N
  same-seed trials; if score-tolerance is also to be satisfied, the *mean*
  normalized_score across trials stays within an evidence-derived tolerance band
  (derived from the repro's actual trial-to-trial spread, not invented).
- Where it should live: `tests/unit/worldassembly/test_corpus_diversity.py`, adjacent
  to `test_generated_frontier_3_42_extended_population_stability` (the direct template
  for tolerance-guard shape, lines 293-373) — adapted for grade/score instead of
  population.

**2c. If a given anchor's repro instead reveals a non-F6, non-load-sensitive cause**
(per the ticket's Scope fallback and investigation.md Risk #1's "3 exception" anchors):
- Do not force a bit-identical or tolerance guard — investigate and fix/guard per the
  actual cause found (e.g. a content/anchor-staleness fix with a normal single-run
  regression test). Document the deviation explicitly in `repro_sweep.md` and this
  ticket's Implementation Notes; do not silently apply the F6 guard pattern to a
  non-F6 cause.

### 3. `docs/simulation_quality/eval_matrix_results.md` reliability-status entries (AC #3)
- Not a pytest test — a documentation requirement. Extend the existing "Anchor
  Reliability Verification" section (`eval_matrix_results.md:1638+`) with a new
  subsection for this ticket's 14 anchors, following the same per-key format
  (`### <anchor> — <stable|converted-to-tolerance|flagged-unverified|non-F6-fixed>`)
  established by `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`.

### 4. `combat_damage`/`entity_killed` emission-path trace (conditional — only if repro implicates it)
- Category: investigation follow-up, not necessarily a new test.
- What it verifies: if `generated_frontier_3_42_seed123_200t`'s or either
  `frontier_extended_seed123_200t`/`frontier_living_world_seed123_200t`'s COMBAT drift
  traces to `combat_damage`/`entity_killed` (constructed outside `event_extractor.py`
  per investigation.md's gap), locate and characterize that emission path before
  writing a guard. Do not write a guard against a mechanism that has not been located.

## Scoped Pytest Commands

```bash
# Core SimQ scoring unit tests (fast, must always pass) — regression surface
pytest tests/simulation_quality/test_accumulator.py tests/simulation_quality/test_cognition_scorer.py \
  tests/simulation_quality/test_social_scorer.py tests/simulation_quality/test_combat_scorer.py \
  tests/simulation_quality/test_progression_scorer.py tests/simulation_quality/test_narrative_scorer.py \
  tests/simulation_quality/test_economy_scorer.py tests/simulation_quality/test_weights.py \
  tests/simulation_quality/test_report.py tests/simulation_quality/test_quality_hub_integration.py -v

# Fast-tier anchor regression (9 of the 14 anchors + 2 standalone probes)
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v

# Slow-tier anchor regression (5 of the 14 anchors + 13 already-stable siblings)
pytest tests/simulation_quality/test_grade_regression.py -m slow -v

# Full file, unfiltered — this is the literal AC #4 command
pytest tests/simulation_quality/test_grade_regression.py -v

# Tolerance-guard / bit-identical-guard pattern precedents + any new guards added here
pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget large -v
```

Do not run `pytest tests/`. Do not substitute `make evaluate-full` for the slow-tier
sweep — it only re-runs ≤500t fast anchors and would silently skip 5 of this ticket's 14
anchors, per `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`'s already-documented Anti-Drift
Hazard on this exact point.

## Anti-Drift Test Guards

- **`test_within_band_default_tolerance_unchanged` (existing,
  `test_grade_regression.py:547-553`) must keep passing unchanged** — guards against
  silently widening the ±1-letter band as a shortcut to make an unstable anchor "pass"
  instead of properly repro-ing and guarding it.
- **`test_score_tolerance_catches_within_band_regression` (existing,
  `test_grade_regression.py:527-541`) must keep passing unchanged** — guards against
  silently loosening `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT`.
- **`test_grade_anchors_entry_count_unchanged` (existing,
  `test_grade_regression.py:556`) must keep passing** — pins the anchor fixture at 76
  top-level scenario entries; this ticket only edits existing entries' pillar
  grade/score values (or adds a guard test elsewhere), it does not add or remove
  top-level anchor keys.
- **A guard confirming `src/engine/kernel.py` is byte-for-byte unchanged** — e.g.
  `git diff --stat src/engine/kernel.py` empty at Finalize, matching both precedent
  tickets' own final verification step exactly (hard Out of Scope).
- **`test_duplicate_event_id_is_noop` (existing, `test_accumulator.py`) must keep
  passing unchanged** — if repro work for the COGNITION anchors tempts a dedup-gate
  "fix" for `decision_divergence_detected` (explicitly out of scope, per Anti-Drift
  Hazards in investigation.md), this test's semantics would need deliberate
  re-authoring, which is the signal that scope has crept beyond this ticket's boundary.
- **Any existing `EventRecorder`/`EventExtractor` tests exercising
  `reputation_delta`/`social_memory_created`/`group_joined`/`contract_offer_created`/
  `progression_plateau_detected`/`narrative_milestone` emission logic must keep passing
  unchanged** — confirms this ticket's guard additions do not touch the delta-based
  emission logic itself, only add repro-driven regression guards around its output.
- **New guards added for the 3 "200t exception" anchors must not silently assume F6**
  without a documented repro result showing bit-identical-or-not at that specific
  anchor/seed/tick-count — if the repro instead finds a non-F6 cause (investigation.md
  Risk #1), the corresponding new test must reflect that actual cause (e.g. a normal
  single-run regression assertion, not an idle-vs-load bit-identical/tolerance guard),
  and this deviation must be visible in the test's own docstring, mirroring
  `test_urban_political_seed123_500t_cognition_bit_identical_under_load`'s docstring
  style (states what was tried, what was found, why this specific guard shape was
  chosen).
- **`docs/simulation_quality/eval_matrix_results.md`'s new subsection must record a
  reliability status for all 14 anchors, not a subset** — a guard against silently
  closing the ticket with, e.g., only the 5 SLOW anchors documented and the 9 FAST/
  standalone anchors left unrecorded (or vice versa); AC #3 requires all 14.
