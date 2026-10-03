---
ticket_id: TCK-20260614-HASH-SCHEDULER
date: 2026-06-14
---

# Investigation: TCK-20260614-HASH-SCHEDULER

## Existing hash call sites

1. `kernel.py:_phase_persistence()` (line ~798): `CanonicalStateHasher.get_hash()` — guarded by `replay_allowed AND (audit_mode OR replay_richness=="FULL")`. Not a casual per-tick call.
2. `kernel.py:shutdown()` (line ~819): `CanonicalStateHasher.get_hash()` — sanctioned end-of-run boundary.
3. `harness.py:_get_baseline_hash()` (line ~305): `CanonicalStateHasher.get_hash()` — certification boundary.
4. `harness.py:run()` (line ~185): `CanonicalStateHasher.get_hash()` — secondary hash for determinism check; certification boundary.

## BudgetedCanonicalHasher (TCK-20260614-RESOURCE-BUDGET-GATE)

Already exists in checkpoint.py — rate-limiter (100-tick window). The `CanonicalHashScheduler` is complementary: budget gate limits call frequency; scheduler enforces call location policy.

## Sanctioned boundary definition

From `docs/engine/contracts/runtime_completion_contract_ma.md` §7: canonical hashing is required at start-of-run, end-of-run, and certification checkpoints. This maps directly to the scheduler's `tick==0`, `tick==run_end_tick`, and `reason in {"certification","audit","replay"}` logic.

## Method name

`get_hash(state)` is the canonical entry point (confirmed by grep). The ticket mention of `compute_hash()` in docs was stale; source code uses `get_hash()`.
