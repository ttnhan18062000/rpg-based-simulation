---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER
date: 2026-10-06
tags: [performance, determinism, engine, testing]
---

# Plan: TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER

1. Tests first: kernel digest equals `CanonicalStateHasher.get_hash` for a fixed seed; computed and not-computed payloads;
   harness calls the scheduler; update `test_hash_scheduler.py` DEGRADED assertion to the typed status.
2. `kernel.py` `_phase_persistence` and `shutdown` via the scheduler. Keep line count and complexity flat or down.
3. `harness.py` both sites via `compute_digest(...).value`.
4. Remove `HashMode` and the `mode` parameter (`checkpoint.py`, tests).
5. Retire `DEFAULT_HASHING_BUDGET` and the `"hashing"` entry; update the budget-gate test; INFRA-196.
6. Docs: deterministic_execution.md (canonical hash, TICK_END schema note old vs new), known_limitations 2.4, kernel.md,
   PERF-D5 status line; regenerate the hash call-site inventory with the tool.
7. code-health, typecheck, scoped tests; close.
