---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL
date: 2026-10-05
tags: [performance, determinism, testing]
---

# Plan: TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL

Edit scope: `src/engine/worker_manager.py` only (plus tests, docs, parity ledger). `governor.py` is
tests-only; if an edit looks needed, stop and ask perf-planner.

1. Spec tests first, from PERF-D1 (red against current code where applicable).
2. `WorkerManager.__init__`: raise `ValueError` naming both values when `max_workers < 0`,
   `max_queue_depth < 0`, or `max_workers >= 1` and `max_queue_depth <= 0`. Zero workers with zero
   or positive queue stays valid.
3. `get_stats()`: queue utilization `0.0` when `max_queue_depth <= 0` (reachable only with zero
   workers); update the comment block to cite PERF-D1.
4. Governor tests in `tests/unit/resource/test_resource_governor_contract.py`.
5. Docs: check `deterministic_execution.md` and `runtime_profiles.md`; edit only a wrong or present
   statement. Parity ledger entry in `docs/parity_ledger/infrastructure.yaml`.
6. Baseline disposition table in the ticket (read `latest.json`, `matrix_full.json`, both baseline dirs).
7. Run the AC 8 test set, `make code-health`, `make typecheck-py`; close via hand-orchestrated tool.
