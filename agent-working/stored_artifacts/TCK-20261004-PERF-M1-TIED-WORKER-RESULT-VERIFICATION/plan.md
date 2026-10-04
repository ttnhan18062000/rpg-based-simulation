---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION
date: 2026-10-04
tags: [performance, determinism, testing]
---

# Plan: TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION

Verification only. No `src/` edit.
1. `tests/integration/kernel/test_tied_worker_result_order.py`: a `PermutingKernel` subclass overrides `_phase_resolution` to permute `_final_results` (identity, reverse, two seeded shuffles) and records the five levels; `AuthoritativeApplyPipeline.refine` is wrapped by a fixture to capture the raw and refined update.
2. Cases: all scenarios by local/thread/process routes; ID-zero tie; equal class and local priority; same-entity tie (validator and resolution guard); validator gap characterisation; shipped constructors emit no duplicate subsystem; mutation proof with a non-commutative same-subsystem pair.
3. Record the outcome in `docs/engine/deterministic_execution.md` (Rule 2) and parity ledger `INFRA-420`.
Scope guard: if a seam needs `kernel.py`, stop and report.
