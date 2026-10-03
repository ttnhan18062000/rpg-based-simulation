---
ticket_id: TCK-20260619-E33B-ALERTS-REST
phase: test_plan
date: 2026-06-21
---

# Test Plan: Economic Alert Events + REST Endpoint

## Regression Surface (existing tests that must pass)

```
pytest tests/unit/economy/test_economy_health_monitor.py -x -v -m "not slow"
# 8 tests — TC-01 through TC-08; must not be broken by alert additions
```

## New Tests Required (per AC)

### Unit tests — `tests/unit/economy/test_economy_alerts.py`

| ID | Test | AC mapped |
|---|---|---|
| TC-B01 | `test_inflation_spiral_fires_above_gini_threshold` — gini=0.82 → emits INFLATION_SPIRAL | AC: alert event kinds defined |
| TC-B02 | `test_gold_hoarding_fires_above_08_gini` — gini=0.85 → emits GOLD_HOARDING | AC: GOLD_HOARDING kind |
| TC-B03 | `test_no_alert_below_thresholds` — gini=0.3 → no alerts emitted | AC: no false positives |
| TC-B04 | `test_check_alerts_returns_list` — return type is `list[SimulationEvent]` | AC: typed return |
| TC-B05 | `test_alert_events_have_correct_fields` — event_type, event_category="economy", region_id set | AC: shaped events |

### Unit tests — `tests/unit/api/test_economy_route.py`

| ID | Test | AC mapped |
|---|---|---|
| TC-B06 | `test_economy_health_endpoint_returns_200` — GET /api/v1/economy/health returns 200 with correct shape | AC: endpoint functional |
| TC-B07 | `test_economy_health_response_schema` — response has `tick`, `regions` dict with per-region keys | AC: response shape |
| TC-B08 | `test_economy_presenter_shapes_correctly` — `EconomyPresenter.present_health()` returns typed dict, no raw state | AC: no raw domain models |

### Integration test (slow) — `tests/integration/scenarios/test_macro_economy.py`

| ID | Test | AC mapped |
|---|---|---|
| TC-B09 | `test_inflation_spiral_alert_emitted` — 2000-tick run with rapid gold creation; assert ≥1 INFLATION_SPIRAL event captured | AC primary |

## Scoped Pytest Commands

```bash
# Fast unit tests (run first)
pytest tests/unit/economy/test_economy_health_monitor.py tests/unit/economy/test_economy_alerts.py tests/unit/api/test_economy_route.py -x -v

# Integration (slow — run after unit pass)
pytest tests/integration/scenarios/test_macro_economy.py::test_inflation_spiral_alert_emitted -x -v -m slow
```

## Anti-Drift Test Guards

- TC-B01/B02 must use `EconomyHealthMonitor.check_alerts(snapshot, region_id)` — not re-implement the Gini formula.
- TC-B04 must assert `isinstance(result, list)` and each item `isinstance(item, SimulationEvent)`.
- TC-B06 must use FastAPI `TestClient` with a mocked `get_engine_manager()` that returns a fake manager with `latest_state`.
- TC-B08 must assert the presenter output is a plain `dict` (not a Pydantic model or raw state object).
- TC-B09 must capture events via a list listener registered before the run, not by reading JSONL.
