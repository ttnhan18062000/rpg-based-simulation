---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY
date: 2026-10-06
tags: [performance, determinism, engine, testing]
---

# Plan: TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY

1. Regression test first (`tests/integration/kernel/test_tick_budget_report_only.py`): audit_mode off,
   1 ms budget, a governor that never changes mode and records `force_mode` calls. Assert no result is
   dropped by the clock, `force_mode` never called, no 9999, overrun recorded. Fails on main.
2. `RuntimeStatus.record_budget_overrun` and the two fields.
3. `kernel.py`: mid-tick throttle detects once per tick, records, logs, routes the (reworded) alert,
   keeps processing; end-of-tick check records the same signal instead of `record_dropped_work(9999)`.
4. Fix tests listed in Scope 4 one by one; camp-raid test reaches DEGRADED explicitly and asserts it.
5. Docs: deterministic_execution.md, throttle comment, intentional_divergences, parity ledger,
   wall_clock_inventory regeneration if sites move.
6. code-health / typecheck on touched files (kernel.py is near its ceilings: net line count must not grow).
