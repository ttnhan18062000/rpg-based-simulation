---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260913-PERF-M0-OWNER-TRIAGE
date: 2026-10-02
tags: [performance, architecture]
---

# Investigation: TCK-20260913-PERF-M0-OWNER-TRIAGE

- Static `run_phase()` calls in `AuthoritativeApplyPipeline.refine`: 44 (AST count, 2026-10-02).
- `WorkerManager.get_stats()`: worker-zero returns 0.0 (fixed), queue-zero still returns 1.0.
- Persistence hashes directly (`kernel.py:1186`, `:1255`); `BudgetedCanonicalHasher` has no caller
  outside its own module and its test.
- `work_debt` is `Dict[str, int]`; the governor's `work_debt_total` is the sum.
- Roadmap Section A says "C-03/C-04" for the worker-utilization fix; the fix concerns C-03.
