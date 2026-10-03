---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE
artifact_type: test_plan
tags: [cognition, information, self-model, observability, simulation-quality]
---

# Test Plan — TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE

**Retrospective reconstruction note:** the 6 new tests below are verbatim from the parent
investigation's `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/test_plan.md`
"New Tests Required" section (per this ticket's own Scope item 6/7, which mandates using them
verbatim, not re-deriving). All were implemented and independently re-run passing in the current
session (dates below), after the implementation itself had already landed in a prior, paused
session (commit `0a99c725`).

## Regression Surface

Existing tests that must keep passing (none modified by this ticket except where noted in "New
Tests Required"):

- `tests/unit/cognition/`, `tests/unit/domains/information/` (full directories)
- `tests/unit/domains/adventure/`, `tests/unit/strategic/test_classifier.py`
- `tests/integration/domains/test_fused_loop.py` (incl.
  `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`, must pass
  unmodified)
- `tests/integration/domains/information/`
- `tests/unit/domains/information/test_phase5_information_query_router.py` (router untouched —
  confirms the Ranking vs. Fallback decision was honored)
- `tests/unit/observability/test_event_extractor_information2.py`
- `tests/integration/test_world_profile_feature_flag_guardrail.py`
- `tests/perf/test_phase5_information_belief_budget.py`
- `tests/simulation_quality/test_grade_regression.py` (`urban_political`/`unit_selfmodel_pilot`
  anchors)

## New Tests Required (verbatim from parent investigation's test_plan.md)

1. `test_branch_b_query_routing_fails_silently_on_real_urban_political_state` (parametrized over
   seeds 42/123/456) — `tests/integration/domains/information/test_phase5_branch_b_realworld.py`
2. `test_information_belief_phase_falls_back_to_next_candidate_on_resolution_failure` —
   `tests/integration/domains/information/test_phase5_information_belief_phase.py`
3. `test_intent_resolver_insufficient_gold_produces_signal_not_silent_none` —
   `tests/unit/domains/information/test_phase5_information_intent_resolver.py`
4. `test_event_extractor_emits_route_new_query_event` —
   `tests/unit/observability/test_event_extractor_information2.py`
5. `test_ask_information_intent_execution_closes_the_loop` —
   `tests/integration/domains/information/test_phase5_information_belief_phase.py`
6. `test_urban_political_selfmodel_cognition_isolated_grade_anchor` (unconditional per this ticket's
   Scope item 7, since the parent investigation's Decision 3 resolved the probe-fixture formalization
   question) — `tests/simulation_quality/test_grade_regression.py`

## Scoped Pytest Commands (all independently re-run and confirmed passing this session)

```bash
pytest tests/unit/cognition/ tests/unit/domains/information/ tests/integration/domains/information/ tests/unit/observability/test_event_extractor_information2.py -q
# 160 passed

pytest tests/unit/domains/adventure/ tests/unit/strategic/test_classifier.py tests/integration/domains/test_fused_loop.py -q
# 70 passed

pytest tests/simulation_quality/test_grade_regression.py -q -k "urban_political or unit_selfmodel_pilot"
# 12 passed, 1 skipped (calibration report missing — gitignored, expected) until regenerated locally,
# then 13/13 passed once data/calibration/urban_political_selfmodel_probe_seed42_200t was regenerated
# via: python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political
#      --profile urban_political_selfmodel_probe --output data/calibration/urban_political_selfmodel_probe_seed42_200t
# Result matched the ticket's original claim exactly: COGNITION=S (5610 events), INFORMATION=C (0 events)

pytest tests/integration/test_world_profile_feature_flag_guardrail.py tests/perf/test_phase5_information_belief_budget.py tests/unit/domains/information/test_phase5_information_query_router.py -q
# 59 passed

python3 tools/evaluate_simq.py --dry-run
# 720 pillars checked, 0 regressions, 0 missing (after regenerating 6 stale local calibration
# caches for frontier_living_world/highland_traverse — see Anti-Drift Test Guards below; this
# corrects the ticket's original claim of "exactly 3 pre-existing regressions", which did not
# reproduce and was attributable to the same stale-cache mechanism)
```

## Anti-Drift Test Guards

- `test_phase5_information_query_router.py` must keep passing unmodified — the guard that
  `router.py`'s ranking heuristic was never touched (Ranking vs. Fallback decision).
- `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization` must pass
  unmodified — proves this ticket's fixes extend, not replace, the existing hand-built-state
  reachability proof.
- `evaluate_simq.py --dry-run` reads cached `data/calibration/*/quality_report.json` files, not a
  fresh engine run — that directory is repo-wide `.gitignore`d, so a clean checkout (or one with
  stale cached reports predating an unrelated world's feature activation) can show false-positive
  regressions unrelated to this ticket's changes. Before trusting a dry-run regression on an
  unfamiliar machine, regenerate the specific flagged world/seed live via `calibrate_simq.py` and
  compare against the committed anchor directly, rather than assuming the cached report is current.
