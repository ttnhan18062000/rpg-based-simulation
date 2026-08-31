---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION
artifact_type: test_plan
tags: [simulation-quality, information, social, grade-thresholds, calibration, feature-flags]
---

# Test Plan — TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION

## Regression Surface

Existing tests that must keep passing when this drift is eventually resolved (re-anchor and/or
fix), grouped by category:

**Unit — self-model / knowledge assimilation**
- `tests/unit/cognition/test_phase2_self_model_phase.py`
- `tests/unit/cognition/test_phase2_knowledge_model_service.py`
- `tests/unit/config/test_phase10_feature_flags.py` (flag registry defaults — must NOT change as
  a side effect of this work; this ticket's scope explicitly excludes flipping any flag default)

**Unit — cooperation domain**
- `tests/unit/domains/cooperation/test_cooperation_phase.py`
- `tests/unit/domains/cooperation/test_phase7_help_need_evaluator.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`

**Integration**
- `tests/integration/scenarios/test_phase2_self_model_scenarios.py`
- `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py`
- `tests/integration/domains/test_fused_loop.py -k "self_model or branch_b or belief"`
- `tests/integration/test_world_profile_feature_flag_guardrail.py`

**Simulation-quality / grade-anchor regression**
- `tests/simulation_quality/test_grade_regression.py` full file (in particular: both target tests
  `test_urban_political_selfmodel_cognition_isolated_grade_anchor` and
  `test_urban_political_selfmodel_execution_isolated_grade_anchor`; the `FAST_ANCHOR_KEYS`
  parametrized `test_grade_within_anchor_band`/`test_grade_within_score_tolerance` sweep, since a
  `grade_anchors.json` edit must not silently perturb unrelated entries; the
  `test_score_tolerance_catches_within_band_regression`,
  `test_within_band_default_tolerance_unchanged`, and `SCORE_TOLERANCE_OVERRIDES`-coverage
  anti-drift guards at the bottom of the file)
- `tests/simulation_quality/test_social_scorer.py`
- `tests/simulation_quality/test_agency_scorer.py` (AGENCY co-moves with SOCIAL cooperation
  wiring per `regression_policy.md` §9-10's own precedent — must not silently regress alongside a
  SOCIAL change)
- `tests/perf/test_phase7_social_cooperation_budget.py` (a retry-cooldown fix changes
  `CooperationPhase`'s per-tick evaluation volume — must stay within its performance budget)

**Architecture / anti-drift guards**
- `tests/architecture/test_adventure_routing_flag_inert.py` (unrelated to this ticket's own diff,
  but lives in the same feature-flag-adjacent test family and should be re-run as a cheap sanity
  check any time `feature_flags.py`-adjacent code changes)

## New Tests Required

Per this investigation's findings, an eventual implementation ticket should add:

1. **`test_information_assimilation_independent_of_belief_assimilation_flag`**
   - Category: unit (architecture-guard flavor)
   - Verifies: `SelfModelUpdatePhase.run()`'s Step 1 Knowledge Assimilation fires from a seeded
     `InformationResponse`-shaped event with `ENABLE_BELIEF_ASSIMILATION` OFF and
     `ENABLE_SELF_MODEL_COGNITION` ON — durably encodes this investigation's Root Cause
     Determination (intended independence, not accidental coupling) so a future change that
     accidentally wires the two together is caught immediately, and so the `INFORMATION=C/0.0`
     anchor's original (now-corrected) assumption cannot silently re-appear uncaught.
   - Location: `tests/unit/cognition/test_phase2_self_model_phase.py`

2. **`test_cooperation_offer_no_immediate_reoffer_after_expiry`** (already required by
   `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`'s own Acceptance Criteria — listed here
   only as a cross-reference so whichever ticket implements the SOCIAL side of this drift does not
   duplicate it)
   - Category: unit
   - Verifies: an entity does not re-propose a cooperation offer on the tick immediately following
     a prior offer's expiry.
   - Location: `tests/unit/domains/cooperation/` (exact file per that ticket's own implementation)

3. **`test_urban_political_selfmodel_probe_social_score_reachable_by_band_check`** (new,
   scoped to this ticket's own Anti-Drift Hazards finding)
   - Category: unit / regression-structure
   - Verifies: `test_urban_political_selfmodel_cognition_isolated_grade_anchor`'s hard-coded
     `INFORMATION` grade assert does not prevent `SOCIAL`'s band/score-tolerance checks from
     running — i.e. restructure the test (or add a companion assertion) so a `SOCIAL` regression on
     this run key cannot hide behind an unrelated `INFORMATION` failure the way it does today. This
     is not a new production-code test — it is a test-harness structure fix implied by this
     ticket's own investigation.
   - Location: `tests/simulation_quality/test_grade_regression.py`

4. **(Conditional on re-anchor path)** If `INFORMATION` is re-anchored for
   `urban_political_selfmodel_probe_seed42_200t`, no *new* test is required beyond updating
   `grade_anchors.json` itself — the existing `test_urban_political_selfmodel_cognition_isolated_grade_anchor`
   already covers it once its own hard-coded `== "C"` assert is updated to `== "B"` (or replaced by
   the band/score-tolerance path used everywhere else in this file, for consistency — implementer's
   judgment, but the docstring's stated rationale for `C` must be corrected either way, not left
   contradicting the code).

5. **(Conditional on multi-draw sweep)** If a multi-draw SOCIAL sweep is run to resolve Risks item
   1 (nondeterminism), the resulting evidence should be captured the same way
   `SCORE_TOLERANCE_OVERRIDES`' existing entries are documented (module docstring derivation +
   `abs_floor` entry keyed on `(run_key, "SOCIAL")`) rather than a bare anchor-value edit — this
   keeps the git-blame-traceable-justification bar the Acceptance Criteria require.

## Scoped Pytest Commands

```
# The two target grade-anchor tests (fast — reads existing data/calibration/ reports, no new run)
.venv/bin/python3 -m pytest \
  tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_cognition_isolated_grade_anchor \
  tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_execution_isolated_grade_anchor \
  -v

# Full grade-regression file, including the FAST_ANCHOR_KEYS sweep and anti-drift guards
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -q

# Self-model / knowledge-assimilation unit + integration surface
.venv/bin/python3 -m pytest \
  tests/unit/cognition/test_phase2_self_model_phase.py \
  tests/unit/cognition/test_phase2_knowledge_model_service.py \
  tests/unit/config/test_phase10_feature_flags.py \
  tests/integration/scenarios/test_phase2_self_model_scenarios.py \
  -q

# Cooperation domain surface (relevant if SOCIAL's retry-cooldown fix lands as part of this work)
.venv/bin/python3 -m pytest \
  tests/unit/domains/cooperation/ \
  tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py \
  tests/simulation_quality/test_social_scorer.py \
  tests/simulation_quality/test_agency_scorer.py \
  -q

# Feature-flag guardrail (must show no default changed)
.venv/bin/python3 -m pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q
```

Note: `.venv/bin/python3` (main checkout's venv) must be used, not bare `python3` — this worktree's
bare interpreter lacks `pydantic` (pre-existing, unrelated environment gap, confirmed during this
investigation's own fresh test run and consistent with prior sibling tickets' documented
workaround).

## Anti-Drift Test Guards

- `test_within_band_default_tolerance_unchanged` and the `SCORE_TOLERANCE_OVERRIDES`-coverage test
  at the bottom of `test_grade_regression.py` must keep passing — they guard against a re-anchor
  quietly widening global tolerance instead of adding a scoped, evidence-derived override entry.
- Re-running the full `FAST_ANCHOR_KEYS` sweep (`test_grade_within_anchor_band` /
  `test_grade_within_score_tolerance`, parametrized) after any `grade_anchors.json` edit catches
  accidental cross-contamination — this file's own JSON is shared across ~80 run keys, and a
  hand-edit to the 2 entries in this ticket's scope must not touch any other key's block.
  `python3 -c "import json; json.load(open('tests/simulation_quality/fixtures/grade_anchors.json'))"`
  as a cheap parse-validity check before running the suite is worth doing given hand-editing risk.
- `tests/unit/config/test_phase10_feature_flags.py` must keep asserting the exact current default
  set (`ENABLE_SELF_MODEL_COGNITION: OFF`, `ENABLE_BELIEF_ASSIMILATION: ON`,
  `ENABLE_SOCIAL_COOPERATION: ON`, etc.) — this ticket's Out of Scope explicitly forbids flipping
  any flag default, and this test is the guard that would catch an accidental flip smuggled in
  alongside a gating fix.
- If a `CooperationPhase` retry-cooldown fix is implemented, `tests/perf/test_phase7_social_cooperation_budget.py`
  is the guard against the fix accidentally changing per-tick evaluation cost/budget in a way that
  regresses performance while fixing correctness — a cooldown that skips re-evaluation entirely vs.
  one that still evaluates-then-suppresses have different cost profiles.
- `tests/architecture/test_adventure_routing_flag_inert.py::test_enable_adventure_routing_has_no_live_gating_call_site`
  is unrelated in subject but is the established pattern for "assert a specific flag has exactly
  the call sites we expect, no more" — the recommended new test #1 above
  (`test_information_assimilation_independent_of_belief_assimilation_flag`) should follow the same
  style: assert the absence of an `ENABLE_BELIEF_ASSIMILATION` reference in `self_model_phase.py`/
  `knowledge_model.py`, not just the presence of the current independent behavior, so a future PR
  that adds a check cannot silently pass this guard by coincidence.
