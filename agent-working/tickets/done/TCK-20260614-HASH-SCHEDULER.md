---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-HASH-SCHEDULER
phase: done
date: 2026-06-14
tags: [resource-safety, hashing, canonical-hash, performance, determinism]
---

# TCK-20260614-HASH-SCHEDULER

## Title
Add Canonical Hash Scheduler — make full canonical state hash a deliberate action

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add `CanonicalHashScheduler` that enforces `FULL` canonical hashing only at sanctioned boundaries (tick=0, run-end, or explicit reason="certification"/"audit"/"replay"), and provides a cheap `LIGHT` hash for tick-local dirty detection.

## Scope
- Added `HashMode(str, Enum)` with `FULL` and `LIGHT` values to `src/engine/checkpoint.py`
- Added `HashScheduleViolation(RuntimeError)` exception
- Added `CanonicalHashScheduler` class with `allow_full_hash_at()` and `compute_hash()` methods
- Updated `src/certification/harness.py` two call sites to use `CanonicalHashScheduler(..., reason="certification")`
- LIGHT hash uses MD5 on `(tick:seed:entity_count:region_count)` — fast dirty signal, documented as non-cryptographic

## Out of Scope
- Changing the canonical hash algorithm
- Incremental hashing or Merkle trees

## Acceptance Criteria
- [x] `HashMode` enum exists with FULL and LIGHT values
- [x] `CanonicalHashScheduler.compute_hash()` works for both modes
- [x] FULL hash outside sanctioned boundaries raises `HashScheduleViolation`
- [x] LIGHT hash is fast (< 0.1ms per call)
- [x] Certification harness uses scheduler with `reason="certification"`
- [x] 19 tests pass

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260614-RESOURCE-BUDGET-GATE (BudgetedCanonicalHasher — complementary rate-limiter)

## Related Code Areas
- `src/engine/checkpoint.py` — new: `HashMode`, `HashScheduleViolation`, `CanonicalHashScheduler`
- `src/certification/harness.py:185,305` — updated to use scheduler

## Implementation Notes
- `_phase_persistence()` in kernel calls `get_hash()` only when `audit_mode OR replay_richness=="FULL"` — already guarded, not a violation.
- `shutdown()` hash is a sanctioned end-of-run boundary. Not changed.
- Both harness.py call sites now use `CanonicalHashScheduler().compute_hash(..., reason="certification")`.
- LIGHT uses `hashlib.md5(..., usedforsecurity=False)` to satisfy Python 3.9+ FIPS compliance flag.
- Pre-existing certification test failures (`test_certification_detects_semantic_drift`, `test_harness_catches_failed_recovery`) confirmed on branch baseline — not introduced.

## Test Summary
- `tests/unit/engine/test_hash_scheduler.py` — 19 tests: FULL mode (allowed/rejected), LIGHT mode (always allowed, fast, no JSON, tick-sensitive), `allow_full_hash_at()`, architecture test.

## Files Changed
- `src/engine/checkpoint.py` — Added `HashMode`, `HashScheduleViolation`, `CanonicalHashScheduler`
- `src/certification/harness.py` — Lines 185 and 305: replaced direct `CanonicalStateHasher.get_hash()` with scheduler call
- `tests/unit/engine/test_hash_scheduler.py` — New file, 19 tests

## Completion Summary
`HashMode` enum, `HashScheduleViolation`, and `CanonicalHashScheduler` added to checkpoint.py. Scheduler enforces sanctioned-boundary rule for FULL hashes and provides a zero-allocation LIGHT dirty signal. Certification harness updated. 19 tests pass, no regressions on affected modules.
