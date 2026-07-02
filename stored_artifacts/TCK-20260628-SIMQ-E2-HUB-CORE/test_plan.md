---
artifact_type: test_plan
ticket_id: TCK-20260628-SIMQ-E2-HUB-CORE
---

# Test Plan — TCK-20260628-SIMQ-E2-HUB-CORE

## Regression Surface

Existing tests to keep passing:
- `tests/simulation_quality/test_accumulator.py`
- `tests/simulation_quality/test_feed.py`
- `tests/simulation_quality/test_persistence.py`
- `tests/simulation_quality/test_report.py`
- `tests/simulation_quality/test_weights.py`

## New Tests Required

### test_agency_scorer.py

- `test_action_executed_scores_positive` — +1 for `action_executed`
- `test_route_family_first_use_scores_novelty` — +3 for `route_family_first_use`
- `test_project_completed_scores_project_done` — +3 for `project_completed`
- `test_project_completed_commitment_scores_extra` — +4 for `project_completed` with `is_commitment=True`
- `test_route_selected_scores_navigation` — +1 for `route_selected`
- `test_defer_scores_negative` — -1 for `defer_with_reason`
- `test_stasis_time_gate_no_fire_before_threshold` — no extra delta before stasis_gate_ticks
- `test_stasis_time_gate_fires_after_threshold` — extra -3 per tick beyond gate
- `test_rejection_cascade_normal` — -5 for `rejection_cascade_tick` with count ≤ 100
- `test_rejection_cascade_sustained` — -15 for `rejection_cascade_tick` with count > 500
- `test_project_cycle_fires_on_immediate_restart` — -2 for abandon+restart same project
- `test_project_cycle_no_fire_different_project` — no -2 for different project type
- `test_null_for_unknown_event` — returns None for unknown event_type
- `test_population_stasis_fires_when_window_empty` — -25 when no action_taken in window

### test_combat_scorer.py

- `test_combat_initiated_positive` — +2 `combat_active`
- `test_combat_resolved_positive` — +3 `combat_resolved`
- `test_near_death_survival_positive` — +2 `survival_tension`
- `test_combat_damage_first_modifier` — +1 `tactical_variety` on first unique modifier
- `test_combat_damage_duplicate_modifier_no_score` — no +1 for repeat modifier
- `test_entity_killed_attrition` — -1 `attrition`
- `test_entity_killed_early_extinction` — -10 `early_extinction` before tick 10
- `test_attrition_spiral` — -20 for `attrition_threshold_crossed` with 50pct at tick ≤ 100
- `test_extinction_degenerate` — -50 for 90pct threshold at tick ≤ 200
- `test_combat_hard_law_violation` — -30
- `test_null_for_unknown_event` — returns None

### test_quality_hub_integration.py

- `test_hub_routes_event_to_correct_scorer` — agency event → AGENCY accumulator
- `test_hub_accumulator_updated` — raw_score updated after on_envelope
- `test_hub_persistence_write` — quality_scores.jsonl written
- `test_scorer_exception_isolated` — exception from one scorer does not propagate, other scorers continue
- `test_disable_env_var_blocks_scoring` — QUALITY_SCORING_DISABLED=1 → no accumulator updates
- `test_get_pillar_score` — read-only query returns current raw_score
- `test_get_pillar_grade` — read-only query returns grade string
- `test_get_quality_report` — returns valid QualityReport

### test_broker_feed.py additions

- `test_broker_feed_skips_gracefully_when_redis_unavailable` — no exception, health returns "unavailable"
- `test_broker_feed_health_stopped` — health when not started

## Scoped Pytest Commands

```bash
pytest tests/simulation_quality/ -x -v
```

Or individual files:
```bash
pytest tests/simulation_quality/test_agency_scorer.py tests/simulation_quality/test_combat_scorer.py tests/simulation_quality/test_quality_hub_integration.py -v
```

## Anti-Drift Test Guards

- All scorer tests inject a `ScoringWeights` fixture loaded from real config — no hardcoded floats in tests
- Integration test uses `tmpdir` for `QualityPersistence` to avoid cross-test contamination
- `QUALITY_SCORING_DISABLED` test uses `monkeypatch.setenv` and confirms accumulator untouched
