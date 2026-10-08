---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES
date: 2026-10-08
tags: [performance, engine, determinism]
---

# Test plan: TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES

- New: `tests/unit/kernel/test_phase_cost_accounting.py`
  - sum identity on the second tick with a call-count fake clock (exact; fails on `main`, passes after);
  - `resolution_overhead + sum(sub-phase costs) == resolution wall time` exactly;
  - every key of `_current_update.sub_phase_costs` is counted once (no key appears inside `resolution_overhead`);
  - a sub-phase key absent from any whitelist (`combat_engagement`) is covered, to prove the fix is not a bigger whitelist.
- Re-run: `test_milestone_b_closure`, `test_tick_budget_report_only`, `test_work_debt_stays_empty_in_production`, `tests/unit/kernel`,
  tests that read `resolution_overhead` (`tests/perf/test_perf_metropolis.py`), governor / phase-budget unit tests.
- Mutation proof: restore the whitelist locally; the new test must fail on the sum identity.
- Gates: `uv run make code-health`, `uv run make typecheck-py` (no new or worse).
