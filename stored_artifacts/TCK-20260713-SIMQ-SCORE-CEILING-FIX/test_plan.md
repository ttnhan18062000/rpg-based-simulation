---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-SCORE-CEILING-FIX
artifact_type: test_plan
tags: [simulation-quality, calibration, corpus]
---

# Test Plan — TCK-20260713-SIMQ-SCORE-CEILING-FIX

## Regression Surface

All of these read `scoring_weights`/`grade_thresholds` dynamically from the actual config files via
the `scoring_weights` fixture (`tests/simulation_quality/conftest.py:26`, which loads
`ScoringWeights.load(...)` against the real `config/simulation_quality/*.yaml` paths) — confirmed
by inspecting `test_economy_scorer.py`, `test_progression_scorer.py`, `test_information_scorer.py`,
`test_world_dynamics_scorer.py`: every assertion is `rec.delta == scoring_weights["some_key"]`, not
a hardcoded literal. **This means editing `scoring_weights.yaml`'s numeric values does NOT require
editing these test files** — they will automatically re-assert against whatever the new weight is.
The regression risk here is behavioral (scorer logic), not value-drift.

### Unit — scorer logic (must pass unmodified; confirms no scorer-code regressions from a
config-only change)

- `tests/simulation_quality/test_world_dynamics_scorer.py` — full file, especially
  `TestEcologyOwnership`, `TestBuildingSabotage`
- `tests/simulation_quality/test_economy_scorer.py` — full file, especially `TestEcologyExclusion`
- `tests/simulation_quality/test_progression_scorer.py` — full file
- `tests/simulation_quality/test_information_scorer.py` — full file
- `tests/simulation_quality/test_timegate_penalties.py::TestEconomyTimegate` (L74)
- `tests/simulation_quality/test_timegate_penalties.py::TestProgressionTimegate` (L215)
- `tests/simulation_quality/test_weights.py` — `ScoringWeights` loader/validation (must still load
  the edited YAML without `ValidationError`)
- `tests/simulation_quality/test_accumulator.py` — `PillarAccumulator` raw_score/window mechanics
  (unaffected by weight *values*, must still pass since accumulation logic itself doesn't change)

### Unit — report / formula (must pass unmodified; confirms the formula itself is untouched)

- `tests/simulation_quality/test_report.py` — especially
  `test_combat_grade_stable_across_tick_counts_for_same_activity` and
  `test_active_throughout_run_behavior_unchanged` (both directly assert `normalized_score`/grade
  formula behavior — must NOT regress, since this ticket does not touch `quality_report.py`)

### Integration

- `tests/simulation_quality/test_kernel_simq_integration.py` — kernel wiring unaffected by config
  value changes
- `tests/simulation_quality/test_quality_hub_integration.py`
- `tests/simulation_quality/test_scenario_coverage.py` — SQ-01..SQ-23 event-type coverage
  (structural, not value-based; must still pass)
- `tests/simulation_quality/test_calibrate_world_loading.py`
- `tests/simulation_quality/test_evaluate_harness.py`

### Grade-anchor / calibration corpus (the primary regression surface for this ticket — expected
to show controlled, deliberate failures until anchors are updated)

- `tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band` (parametrized
  over `FAST_ANCHOR_KEYS`, ~60 keys) — **expected to fail for any anchor entry whose
  WORLD/ECONOMY/PROGRESSION/INFORMATION column moves more than ±1 letter band** until
  `tests/simulation_quality/fixtures/grade_anchors.json` is updated. This is the intended detection
  mechanism (`_within_band`, L140-151), not a bug to work around.
- `tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band_long_run`
  (parametrized over `SLOW_ANCHOR_KEYS`, `@pytest.mark.slow`) — same expectation, 1000t/2000t
  entries.
- `tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_cognition_isolated_grade_anchor`
  — isolated single-scenario anchor probe; verify it still isolates correctly (COGNITION-focused,
  should be unaffected by this ticket's 4 pillars unless that world happens to have WORLD/ECONOMY/
  PROGRESSION/INFORMATION activity — check before assuming it's untouched).
- `tests/simulation_quality/test_traceability_path.py` — worst_events → tag → root-cause path;
  should be unaffected by weight *magnitude* changes (tags/reasons don't change) but verify no
  hardcoded delta-magnitude assumptions.

**Note on `data/calibration/`:** this directory is committed (109 scenario subdirectories present
in this checkout, confirmed via `ls`), not session-local/transient like `data/runs/`. The anchor
tests read directly from `data/calibration/{run_key}/quality_report.json` — after any weight or
threshold change, these committed calibration reports must be regenerated (`make calibrate` or the
per-scenario `calibrate_simq.py` invocation) for the fast/slow anchor tests to reflect the new
formula inputs, per the existing workflow documented at the top of `test_grade_regression.py`
(steps 1-5).

## New Tests Required

Per AC 1 ("at least one real corpus scenario reaches grade A or S ... for each of the 4 affected
pillars") and AC 2 ("structurally-inert entries remain C"):

- **Name:** `test_economy_richest_run_reaches_a_or_s`
  **Category:** integration (grade-anchor assertion against a real calibration report, not a
  synthetic unit)
  **Verifies:** the identified richest-observed ECONOMY scenario (69-event run per
  `current_state.md` — exact `run_key` to be identified during implementation by grepping
  `data/calibration/*/quality_report.json` for `event_count` near 69 on the ECONOMY pillar) grades
  A or S under the recalibrated weights/thresholds.
  **Location:** `tests/simulation_quality/test_grade_regression.py` (new standalone test, or a new
  entry added to `grade_anchors.json` + covered by the existing parametrized
  `test_grade_within_anchor_band` — prefer reusing the existing parametrized mechanism over a new
  bespoke test unless the specific scenario isn't already an anchor key).

- **Name:** `test_world_richest_run_reaches_a_or_s`
  **Category:** integration
  **Verifies:** same shape as above for WORLD (38-event run candidate).
  **Location:** same file/mechanism as above.

- **Name:** `test_progression_richest_run_reaches_a_or_s`
  **Category:** integration
  **Verifies:** same shape for PROGRESSION (46-event run candidate).
  **Location:** same file/mechanism as above.

- **Name:** `test_information_best_case_reaches_a_or_s`
  **Category:** integration
  **Verifies:** same shape for INFORMATION. **Open question flagged in investigation.md:** the
  cited "best case" for INFORMATION is only a 1-event run reaching 0.04 — this may not be a
  genuine best case, just the richest one *currently in the corpus*. If no existing anchor can
  reach A/S even after a reasonable weight increase (because event density, not weight, is the
  limiting factor), this test may require a new minimal synthetic/probe scenario per the ticket's
  own Scope ("...or a new minimal test scenario if none exists") — implementer must construct one
  (e.g. a short scripted sequence of `belief_assimilated`/`paid_information_transaction`/
  `decision_diverged_by_belief` events at a controlled tick count) rather than assume a real-corpus
  scenario suffices. This is the one pillar where "raise weights" alone might not be sufficient —
  verify empirically before assuming symmetry with the other 3.

- **Name:** `test_economy_zero_activity_remains_c`
  **Category:** integration / anti-drift guard
  **Verifies:** at least one committed zero-ECONOMY-event anchor (candidates already identified in
  `eval_matrix_results.md`: lines ~324 and ~1254, "0 events, all 3 seeds" / "stable — no
  gather_resource/craft/buy events scored this run") still grades C after the fix — directly
  covers AC 2's "structurally-inert entries... remain C."
  **Location:** `tests/simulation_quality/test_grade_regression.py` (covered by the existing
  parametrized anchor test if that scenario/seed is already a `FAST_ANCHOR_KEYS` entry — confirm
  before adding a new bespoke test).

- **Name:** `test_world_zero_activity_remains_c`, `test_progression_zero_activity_remains_c`,
  `test_information_zero_activity_remains_c`
  **Category:** integration / anti-drift guard
  **Verifies:** same shape as the ECONOMY zero-activity guard, one per remaining pillar. Identify
  concrete zero-event anchor candidates for each during implementation (WORLD: several
  `Stress`/`Unit`-tier worlds per `corpus_tier_taxonomy.md` are documented as intentionally inert
  for pillars outside their focus; PROGRESSION: any world with `ENABLE_ADVENTURE_ROUTING`/XP
  systems off; INFORMATION: any non-`urban_political`/non-probe world per the Phase 5 gate's
  "9/17 worlds carry calibrated content" finding).
  **Location:** same file/mechanism.

- **Name:** `test_uniform_weight_multiplier_guard` (anti-drift, addresses the investigation's
  "watch for uniform/blanket weight inflation" hazard)
  **Category:** unit / architecture guard
  **Verifies:** the 4 pillars' positive-signal weight values are NOT all scaled by an identical
  multiplier relative to their pre-fix values (i.e. confirms per-signal reasoning was applied, not
  a single global multiplier) — compares the ratio of at least 2 distinct signal weights
  pre-fix-vs-post-fix per pillar and asserts they are not uniform. This is a softer, judgment-based
  guard; consider making it a documented manual verification step in the PR description instead of
  an automated test if a clean automatable assertion isn't feasible (e.g. via a git-diff-based
  fixture of old vs new `scoring_weights.yaml` values).
  **Location:** `tests/simulation_quality/test_weights.py` if automatable, otherwise a checklist
  item in `plan.md`/PR description.

Per AC 3 ("0 unattributed regressions"): no single new test covers this — it is a *process*
requirement (full `evaluate_simq.py` live sweep + manual review of every anchor diff against a
documented reason), not a pytest assertion. Track via the Scoped Pytest Commands section below plus
the manual sweep step.

Per AC 4 (`current_state.md` doc updates): not a test — a doc-update checklist item for
`plan.md`/implementation, cross-referenced here so it isn't dropped: update the grade-distribution
table and discriminative-power section once the corrected state is known.

## Scoped Pytest Commands

```bash
# Scorer unit tests for the 4 affected pillars — fast, no calibration data needed
pytest tests/simulation_quality/test_world_dynamics_scorer.py \
       tests/simulation_quality/test_economy_scorer.py \
       tests/simulation_quality/test_progression_scorer.py \
       tests/simulation_quality/test_information_scorer.py \
       tests/simulation_quality/test_timegate_penalties.py \
       tests/simulation_quality/test_weights.py \
       tests/simulation_quality/test_accumulator.py -v

# Formula-stability tests — confirm quality_report.py is untouched behaviorally
pytest tests/simulation_quality/test_report.py -v

# Full anchor sweep — fast tier (excludes 1000t+ slow runs); requires regenerated
# data/calibration/ reports for any changed weights/thresholds to be reflected
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v

# Slow tier (1000t/2000t long runs) — run once fast tier is clean
pytest tests/simulation_quality/test_grade_regression.py -m slow -v

# Full simulation_quality domain sweep before claiming completion (still scoped to the
# domain under modification, per the Testing Rule — do not run pytest tests/)
pytest tests/simulation_quality/ -m "not slow" -v
```

```bash
# Live-mode full-corpus sweep (tooling bug already fixed by TCK-20260713-SIMQ-EVAL-PROFILE-BUG,
# confirmed done — safe to use repeatedly per AC 3's "0 unattributed regressions" requirement)
python3 tools/evaluate_simq.py   # live mode, not --dry-run, per the ticket's own instruction
```

## Anti-Drift Test Guards

- **`test_grade_regression.py`'s existing parametrized sweep over all `FAST_ANCHOR_KEYS`/
  `SLOW_ANCHOR_KEYS`** already functions as the primary anti-drift guard for the 6+ pillars this
  ticket must NOT touch (NARRATIVE, COMBAT, FACTION, SOCIAL, COGNITION, AGENCY) — any unintended
  side effect (e.g. a shared `detection_params.yaml` value accidentally edited, or a profile
  `pillar_weights` block accidentally touched) would surface as an unexpected grade shift in one of
  these pillars' columns across ~60+ fast anchors. Run the FULL parametrized sweep, not a filtered
  subset — narrowing to only WORLD/ECONOMY/PROGRESSION/INFORMATION columns would blind this guard.
- **`test_world_dynamics_scorer.py::TestEcologyOwnership` /
  `test_economy_scorer.py::TestEcologyExclusion`** — guard against accidentally re-coupling
  `ecology_cycle_completed` ownership between `WorldDynamicsScorer` and `EconomyScorer` (the
  `SQ-08` conflict note) while touching WORLD and ECONOMY weights in the same session — easy to
  conflate since both pillars are being edited together.
  `test_information_scorer.py` (no specific alliance-exclusion analog for INFORMATION, but
  `INFRA-245`'s note that `paid_information_transaction` is scored in `InformationScorer` not
  `EconomyScorer` should be spot-checked for the same reason, since ECONOMY and INFORMATION are
  both being edited).
- **Zero-activity anchor checks** (the `*_zero_activity_remains_c` tests above) are the direct
  automated guard for AC 2 — without them, a broad weight increase could silently be validated only
  against best-case scenarios while regressing worst-case ones un-noticed.
- **`test_weights.py`'s `ScoringWeights.load()` validation** guards against a malformed
  `scoring_weights.yaml` edit (wrong type, typo'd key) failing loudly at load time (per §4.8's
  Pydantic `ValidationError` contract) rather than silently at score time — run this test FIRST
  after any YAML edit, before running the full anchor sweep, to fail fast on syntax/type errors.
- **Manual diff review of every `grade_anchors.json` change** (process guard, not automatable):
  per the ticket's AC 3, every anchor letter-grade change in the committed diff must be traceable
  to one of the 4 pillars' weight/threshold edits — a change appearing in an unrelated pillar
  column, or in a pillar that should have zero activity for that scenario, is the signal that
  something drifted beyond the intended scope.
