---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES
date: 2026-10-08
tags: [performance, engine, determinism]
---

# Plan: TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES

1. Red test first (`tests/unit/kernel/test_phase_cost_accounting.py`): a call-count fake clock; assert
   `sum(_phase_costs.values())` equals the sum of the seven tick-level intervals, exactly. Fails on main.
2. `kernel.py`: replace the whitelist with the pipeline's own list of recorded sub-phase costs:
   `sub_sum = sum((getattr(self._current_update, "sub_phase_costs", None) or {}).values())`. Keep the key name and the `max(0.0, ...)` floor.
   Net line change about 0 to +1 (kernel.py has 23 lines of headroom).
3. Check the tick-keyed-clock tests (`test_milestone_b_closure`) and every test that reads `resolution_overhead` or phase costs.
4. Divergence entry (Bug Fix), kernel docs, parity ledger, affected-baseline list.

Out of scope as in the ticket: governor thresholds, the combat cost itself, clearing `_phase_costs` between ticks.
