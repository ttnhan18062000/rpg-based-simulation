---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS
date: 2026-10-07
tags: [performance, determinism, engine]
---

# Test plan: TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS

No tests added or changed (read-only ticket). Read-only checks run:
- grep of `PeriodicDefinition(`, `_periodic_defs`, `scheduler=`, `DeterministicScheduler(` over `src/` and `tools/`.
- `git log --all -S"PeriodicDefinition(" -- '*.py'` for the history.
- grep of every `GovernorPolicy` field's readers outside `policy.py`.
- grep of `dropped_work` / `total_dropped_work` over the committed baseline directories and `tests/regression`.
- Read `scheduler.py`, `policy.py`, `executor.py` (periodic work kinds) and the matrix docs.
