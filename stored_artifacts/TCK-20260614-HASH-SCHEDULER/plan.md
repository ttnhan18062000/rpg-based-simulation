---
ticket_id: TCK-20260614-HASH-SCHEDULER
date: 2026-06-14
---

# Plan: TCK-20260614-HASH-SCHEDULER

## Step 1 — Add types to checkpoint.py
- `HashMode(str, Enum)`: FULL="full", LIGHT="light"
- `HashScheduleViolation(RuntimeError)` with INFRA-197 citation
- `_SANCTIONED_REASONS = frozenset({"certification","audit","replay"})`

## Step 2 — Add CanonicalHashScheduler to checkpoint.py
- `__init__(run_end_tick: int = -1)`
- `allow_full_hash_at(tick, reason) -> bool`
- `compute_hash(state, tick, mode=LIGHT, reason="") -> str`
  - FULL: validate schedule, delegate to `CanonicalStateHasher.get_hash()`
  - LIGHT: `md5(f"{tick}:{seed}:{len(entities)}:{len(regions)}")`

## Step 3 — Update harness.py
- Line 185: `secondary_hash = CanonicalHashScheduler().compute_hash(kernel2.state, tick=..., mode=FULL, reason="certification")`
- Line 305: `return CanonicalHashScheduler().compute_hash(kernel.state, tick=..., mode=FULL, reason="certification")`

## Step 4 — Tests (19 tests in test_hash_scheduler.py)
HashMode values, violation type, FULL allowed/rejected, LIGHT always allowed + fast + no-JSON, allow_full_hash_at(), architecture guard.

## Files Changed
- `src/engine/checkpoint.py`
- `src/certification/harness.py`
- `tests/unit/engine/test_hash_scheduler.py` (new)
