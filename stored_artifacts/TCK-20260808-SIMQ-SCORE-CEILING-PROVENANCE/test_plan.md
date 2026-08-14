---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE
artifact_type: test_plan
tags: [simulation-quality, calibration]
---

# Test Plan — TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE

## New tests (`tests/tools/test_score_ceilings.py`)

1. `test_tick_budget_ceiling_flags_short_scenarios` — a synthetic run_key with `ticks <= threshold`
   for a known time_gate is flagged `tick_budget`; one with `ticks > threshold` is not.
2. `test_tick_budget_covers_all_22_time_gates` — every `detection_params.yaml` `time_gates` key
   maps to a pillar in the computation (no silently-ignored threshold).
3. `test_flag_gated_combat_ceiling_present_for_all_26_run_keys` — the hand-verified COMBAT table
   entry covers exactly the 26 known-affected run_keys.
4. `test_ceiling_lookup_returns_none_for_unclassified_pair` — a pair with no known ceiling returns
   `None`, not a false positive.
5. `test_grade_regression_failure_message_includes_ceiling_when_known` — a synthetic failing pair
   with a registered ceiling produces a failure message mentioning it (integration test against
   `test_grade_regression.py`'s own failure-formatting function).

## Scoped pytest command

`.venv/bin/python3 -m pytest tests/tools/test_score_ceilings.py tests/simulation_quality/test_grade_regression.py -q`
