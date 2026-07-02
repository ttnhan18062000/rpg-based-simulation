# Test Plan — TCK-20260627-P1A-REJECTION-BACKOFF

## Regression Surface (existing tests that must pass)

- `tests/unit/strategic/test_strategic_detour_ph6.py` — project detour creation/resumption
- `tests/unit/strategic/test_strategic_cognition_regression.py` — general cognition regression
- `tests/unit/strategic/test_capacity_enforcement.py` — capacity limits
- `pytest tests/unit/strategic/ -x` — full strategic unit suite

## New Tests Required (per AC)

File: `tests/unit/strategic/test_rejection_backoff.py`

### test_project_abandons_after_n_consecutive_rejections
- Build entity with ACTIVE project, `failure_count=19` (one below threshold)
- Set `latest_intent_results` with all-rejected intents
- Call `evaluate_strategic_intent`
- Assert returned `StrategicUpdate.projects_add_or_update[0].status == ProjectStatus.ABANDONED`
- Assert `current_project_id_set == ""`

### test_failure_count_increments_on_rejected_intent
- Build entity with ACTIVE project, `failure_count=0`
- Set `latest_intent_results` with one rejected intent
- Call `evaluate_strategic_intent`
- Assert returned `StrategicUpdate.projects_add_or_update[0].failure_count == 1`
- Assert status still ACTIVE

### test_failure_count_resets_on_accepted_intent
- Build entity with ACTIVE project, `failure_count=10`
- Set `latest_intent_results` with one accepted intent
- Call `evaluate_strategic_intent` (may return empty if no other work)
- Assert if project update returned: `failure_count == 0`

### test_no_change_when_no_intent_results
- Build entity with ACTIVE project, `failure_count=5`
- Set `latest_intent_results` to empty list
- Call `evaluate_strategic_intent`
- Assert: no project update with changed failure_count (or returned update has same count)

### test_abandonment_emits_boredom_penalty
- Build entity with ACTIVE project, `failure_count=19`
- Set all-rejected intents
- Assert returned `StrategicUpdate.boredom_delta` has non-zero entry for `project.kind`

## Scoped Pytest Commands

```bash
pytest tests/unit/strategic/test_rejection_backoff.py -v
pytest tests/unit/strategic/ -x -q
```

## Anti-Drift Test Guards

- The constant `_MAX_CONSECUTIVE_REJECTIONS` must equal 20 (test fixture uses 19 failures + 1
  rejection = trigger exactly at 20)
- Tests must use `evaluate_strategic_intent` directly, not `fused_strategic_pass`, for isolation
- Tests must use the builder pattern from `tests/unit/strategic/test_strategic_detour_ph6.py`
