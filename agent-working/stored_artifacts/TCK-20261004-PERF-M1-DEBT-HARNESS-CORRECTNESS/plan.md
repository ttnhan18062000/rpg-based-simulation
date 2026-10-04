---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS
date: 2026-10-04
tags: [performance, testing]
---

# Plan: TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS

## Summary
One-line source fix in `src/perf/long_run_harness.py`, plus a new test module.

## Steps
1. Line 44 `candidate_count: int` becomes `systems_with_debt: int`; line 211 becomes `systems_with_debt = sum(1 for d in kernel.state.work_debt.values() if d > 0)`; line 223 passes it. Keep line count identical.
2. New `tests/unit/perf/test_long_run_harness_debt.py`:
   - specification tests of the sampled counts on hand-set state (one system, several, one returned to zero, empty);
   - kernel-driven test: a recording Kernel subclass patched into the harness, a wrapped scenario builder that seeds `work_debt`, a profile with `max_worker_count` 1 so debt drains for real; every sample equals the recorded `kernel.state.work_debt` at its tick;
   - non-interference: harness run (sample every tick) vs a bare kernel loop, equal `CanonicalStateHasher.get_hash` at each compared tick, `audit_mode=True`, non-combat scenario.
3. Revert proof: restore the old `len()` line, run the new tests, record the `TypeError`.
4. Docs/parity: search `docs/performance/` and `docs/parity_ledger/infrastructure.yaml` for the field; update if cited.

## Scope guard
Only `src/perf/long_run_harness.py` under `src/`. If real debt cannot be produced without a gated file, stop and report.
