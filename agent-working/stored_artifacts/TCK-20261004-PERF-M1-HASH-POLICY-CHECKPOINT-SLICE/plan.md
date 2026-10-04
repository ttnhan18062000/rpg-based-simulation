---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE
date: 2026-10-04
tags: [performance, determinism, testing]
---

# Plan: TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE

1. `checkpoint.py`: add `PROOF_DIGEST_SCHEME`, `DigestStatus`, `ProofDigest`; add `CanonicalHashScheduler.compute_digest`; make `compute_hash` flat-only (default mode `FULL`); remove `BudgetedCanonicalHasher`, `HashMode.LIGHT`, the unused `logging` and config imports.
2. Tests: rewrite `test_hash_scheduler.py` LIGHT tests; delete the Budgeted block of `test_resource_budget_gate.py`; update the synthetic source in `test_hash_callsite_inventory.py`; new `tests/unit/engine/test_proof_digest_contract.py` (byte-identity, harness copy equality, cached-dict audit).
3. Tool and inventory: remove Budgeted/LIGHT from `tools/perf/hash_callsite_inventory.py`, add `compute_digest`; regenerate `docs/performance/hash_callsite_inventory.{json,md}`; add an update note.
4. Move every fingerprint-based equality claim to `CanonicalStateHasher.get_hash`; relabel the fingerprint coverage tests.
5. Docs: `deterministic_execution.md`, PERF-D5 status line, parity ledger INFRA-196 (retired) and INFRA-197.

Scope guard: no gated file; if one is needed, stop.
