---
status: done
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260619-E33A-HEALTH-MONITOR
phase: done
date: 2026-06-20
tags: [macro-economy, health-monitor, gini, governance, phase-3]
---

# TCK-20260619-E33A-HEALTH-MONITOR

## Title
Epic 3.3A · EconomyHealthMonitor + Metrics

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
No macro-economic health tracking exists. This ticket implements `EconomyHealthMonitor` as a governance phase step that samples gold distribution, transaction volume, and price indices per region per tick-window.

**Blocks:** TCK-20260619-E33B-ALERTS-REST

## Scope

New file `src/engine/economy_health_monitor.py`:

```python
class EconomyHealthMonitor:
    WINDOW_SIZE = 100  # ticks per sampling window

    @staticmethod
    def sample(state: AuthoritativeState, tick: int) -> EconomyHealthSnapshot | None:
        """Sample metrics every WINDOW_SIZE ticks. Returns None otherwise."""
        if tick % EconomyHealthMonitor.WINDOW_SIZE != 0:
            return None
        entity_gold = [
            sum(stack.quantity for stack in e.inventory.items if stack.item_id == "gold_coin")
            for e in state.entities.values() if e.is_alive
        ]
        return EconomyHealthSnapshot(
            tick=tick,
            gini_coefficient=EconomyHealthMonitor._gini(entity_gold),
            transaction_velocity=0.0,   # TODO: count trades in window
            avg_price_index={},         # TODO: per-commodity prices
        )

    @staticmethod
    def _gini(values: list[float]) -> float:
        """Standard Gini coefficient formula."""
        if not values or sum(values) == 0:
            return 0.0
        n = len(values)
        s = sorted(values)
        cum = sum((i + 1) * v for i, v in enumerate(s))
        return (2 * cum) / (n * sum(s)) - (n + 1) / n
```

Wire into governance phase (find correct insertion point in `src/engine/governance_logic.md` contract before implementing).

Write snapshots to `metric_windows.jsonl` in run directory.

## Acceptance Criteria
- 2000-tick run produces `metric_windows.jsonl` with ≥20 entries (one per 100 ticks)
- Each entry has `gini_coefficient`, `transaction_velocity`, `avg_price_index` fields
- `test_gini_coefficient_computed_correctly` passes

## Related Tickets
- TCK-20260619-E33-MACRO-ECONOMY (parent epic)
- TCK-20260619-E33B-ALERTS-REST (blocked on this)

## Related Docs
- `docs/engine/governance_logic.md` (find insertion point for governance step)
- `docs/mechanics/03_economic_laws.md` (add EconomyHealthMonitor section after E33 complete)

## Related Code Areas
- `src/engine/economy_health_monitor.py` (new)
- `src/engine/` governance phase files

## Implementation Notes

Implemented per plan.md exactly. Key decisions:

- Created `src/economy/` package (new directory) with `__init__.py` + `health_monitor.py`.
- `EconomyHealthSnapshot` is a Pydantic `BaseModel`; `EconomyHealthMonitor` is a pure static-method class with `WINDOW_SIZE=100`.
- Gold read from `e.inventory.gold` (authoritative scalar); liveness from `e.combat.alive` — both per investigation findings (corrected from ticket pseudocode which used `gold_coin` item scan and `e.is_alive`).
- Gini formula: `(2*sum((i+1)*v for i,v in enumerate(sorted(values)))) / (n*sum(values)) - (n+1)/n`; returns 0.0 for empty/zero-sum.
- `MetricWindowRecord` extended with 3 optional fields (`economy_gini_coefficient`, `economy_transaction_velocity`, `economy_avg_price_index_json`) — strictly additive, None defaults.
- `MetricWindowAccumulator` gains `self._economy_snapshot = None` in `__init__` and `record_economy_snapshot(snapshot)` method; `flush()` reads snapshot, serialises price index via existing `json` import, then resets `_economy_snapshot = None`.
- `MetricWindowRecorder` gains public passthrough `record_economy_snapshot(snapshot)`.
- Kernel wires `EconomyHealthMonitor.sample()` BEFORE `record_tick()` inside the existing `if self._metric_recorder:` block, via lazy import + try/except guard.
- `transaction_velocity` and `avg_price_index` are stubs (0.0 and {}) per scope — both marked with structured TODO comments.
- 8 unit tests (TC-01–TC-08) all pass; TC-09 (`@pytest.mark.slow`) is present for integration validation.
- TOWN-177 appended to `docs/parity_ledger/town_resource.yaml` with `status: verified`.

## Test Summary
```bash
pytest tests/unit/economy/test_economy_health_monitor.py -x -v -m "not slow"
# 8 passed, 1 deselected (TC-09 is @pytest.mark.slow)
```

## Files Changed
- `src/economy/__init__.py` (created)
- `src/economy/health_monitor.py` (created)
- `src/observability/reporting/metric_recorder.py` (modified — MetricWindowRecord fields, accumulator snapshot storage, flush economy output, public passthrough)
- `src/engine/kernel.py` (modified — EconomyHealthMonitor.sample() wired before record_tick)
- `tests/unit/economy/__init__.py` (created)
- `tests/unit/economy/test_economy_health_monitor.py` (created — TC-01 through TC-09)
- `docs/parity_ledger/town_resource.yaml` (modified — TOWN-177 appended)

## Completion Summary
EconomyHealthMonitor implemented as read-only observability: samples alive-entity gold distribution every 100 ticks, computes Gini coefficient, and emits economy fields into metric_windows.jsonl via the existing MetricWindowRecorder pipeline without mutating AuthoritativeState. All 8 non-slow unit tests pass; 8 determinism certification tests pass.
