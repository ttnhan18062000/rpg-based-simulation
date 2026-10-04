---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS
date: 2026-10-04
tags: [performance, testing]
---

# Investigation: TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS

## Findings
- `src/perf/long_run_harness.py:211` computes `sum(len(q) for q in kernel.state.work_debt.values())` guarded by `if kernel.state.work_debt else 0`. `work_debt` is `Dict[str, int]` (`src/core/state.py:1423`), so `len(int)` raises `TypeError` on the first sample after any debt exists. The guard hides it while the dict is empty, which is true of every fixture today.
- `candidate_count` has no consumer: grep over `src/`, `tests/`, `tools/` and `docs/` (excluding the archive) finds it only in the harness. It is not in `LongRunStabilityReport.to_dict()`, so no JSON artifact carries it.
- Nothing in `src/` adds debt. Debt is only seeded into the initial state (`src/certification/scenarios.py::inject_work_debt` does it for certification). The scheduler (`scheduler.py:124`) emits a `DRAIN_DEBT` item for each system with debt > 0, and `DomainLogic.drain_debt` returns `-profile.max_worker_count`. `apply.py:323` applies it with `max(0, old + delta)`. So with `max_worker_count == 0` (the cert profile) debt never drains; with `max_worker_count == n` each system loses `n` per tick until it reaches zero.
- Docs cite `long_run_harness.py:225` (`active_mode`) and `:267` (`gc_stable`). A single-line edit at line 211 and a same-line field rename keep those line numbers valid.

## Decision: what `candidate_count` means
Rename it to `systems_with_debt`: the number of systems whose debt is greater than zero. Reason: the sum is already `work_debt`; a count of systems tells a reader whether debt is concentrated in one system or spread over many, which the sum cannot. The old name ("candidate") promised a meaning nobody can state for an integer counter (PERF-D3). No consumer, so the rename is safe.

## Open risks
- A profile with `max_worker_count > 0` may make the kernel use worker threads; check the test stays deterministic before relying on it.
- The wall-clock salience coupling (`TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`) can break determinism outside `audit_mode`; the non-interference test uses `audit_mode=True`.
