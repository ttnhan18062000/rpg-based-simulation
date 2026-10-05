---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY
date: 2026-10-06
tags: [performance, determinism, engine, testing]
---

# Test plan: TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY

- New regression: forced overrun, audit_mode False: every result processed, `force_mode` not called,
  `total_dropped_work == 0`, overrun signal recorded (fails on main).
- Non-reader proof: `PressureSignals` has no overrun field and the governor module does not reference
  the status field (source check), plus a run showing the mode sequence is unchanged by recording.
- Determinism (not added: PhaseBudgetGovernor still reads wall-clock costs, a hash-equality test is unreliable; see the ticket): two short runs with an injected overrun give the same canonical hash every tick, if it
  fits the CI budget.
- Existing: Scope 4 list, each run and recorded (unaffected / fixed / not runnable locally).
