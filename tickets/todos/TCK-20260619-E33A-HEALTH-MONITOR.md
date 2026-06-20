---
status: open
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260619-E33A-HEALTH-MONITOR
phase: open
date: 2026-06-20
tags: [macro-economy, health-monitor, gini, governance, phase-3]
---

# TCK-20260619-E33A-HEALTH-MONITOR

## Title
Epic 3.3A · EconomyHealthMonitor + Metrics

## Status
OPEN

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

## Test Summary
```bash
pytest tests/unit/economy/test_economy_health_monitor.py::test_gini_coefficient_computed_correctly -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
