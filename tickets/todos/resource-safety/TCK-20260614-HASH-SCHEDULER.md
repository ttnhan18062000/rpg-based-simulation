---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-HASH-SCHEDULER
phase: open
date: 2026-06-14
tags: [resource-safety, hashing, canonical-hash, performance, determinism]
---

# TCK-20260614-HASH-SCHEDULER

## Title
Add Canonical Hash Scheduler — make full canonical state hash a deliberate action

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`CanonicalStateHasher.compute_hash()` builds a full canonical dictionary from all collections (entities, regions, local scars, resource nodes, buildings, corpses, ground items, chests, groups, home storage, camps, blocked tiles — see `src/engine/checkpoint.py:36-67`), sorts them, serializes JSON, then computes SHA-256. This is expensive and should only run at defined boundaries: start of run, end of run, certification boundary, and explicit audit/replay mode. Currently nothing prevents callers from triggering it casually per tick. Add a `CanonicalHashScheduler` that enforces `FULL_HASH` only at sanctioned points and provides a cheap `LIGHT_HASH` for tick-local dirty detection.

## Scope
- Add `HashMode(str, Enum)` in `src/engine/checkpoint.py`: `FULL = "full"`, `LIGHT = "light"`
- Add `CanonicalHashScheduler` class in `src/engine/checkpoint.py`:
  - `allow_full_hash_at(tick: int, reason: str) -> bool` — returns True only if: tick == 0 (start), tick == run_end_tick, `reason` is `"certification"` or `"audit"` or `"replay"`
  - `compute_hash(state: AuthoritativeState, tick: int, mode: HashMode = HashMode.LIGHT, reason: str = "") -> str`
  - `LIGHT`: hash only `(tick, seed, len(entities), len(regions))` — fast dirty signal, not deterministic proof
  - `FULL`: delegates to `CanonicalStateHasher.compute_hash(state)` — only allowed when `allow_full_hash_at()` returns True; raises `HashScheduleViolation` if called outside sanctioned boundaries
- Add `HashScheduleViolation(RuntimeError)` exception
- In certification harness (`src/certification/harness.py`), replace any direct `CanonicalStateHasher.compute_hash()` calls with `CanonicalHashScheduler.compute_hash(..., mode=HashMode.FULL, reason="certification")`
- Add architecture test: no direct call to `CanonicalStateHasher.compute_hash()` from inside `Kernel.tick_once()` path

## Out of Scope
- Changing the canonical hash algorithm
- Replacing existing baseline/final hash in certification (those calls become FULL with reason="certification")
- Incremental hashing or Merkle trees

## Acceptance Criteria
- `HashMode` enum exists with FULL and LIGHT values
- `CanonicalHashScheduler.compute_hash()` works for both modes
- `FULL` hash outside sanctioned boundaries raises `HashScheduleViolation`
- `LIGHT` hash is fast (no JSON serialization)
- Certification harness uses scheduler with `reason="certification"` — existing hash values unchanged
- Architecture test: grep or AST check confirms no `CanonicalStateHasher.compute_hash()` called from tick hot path

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260614-RESOURCE-BUDGET-GATE (hash budget gate defined there feeds into scheduler enforcement)
- TCK-20260614-CERT-EVIDENCE-LEVELS (uses CanonicalStateHasher for full state export — should use scheduler)

## Related Docs
- `docs/engine/contracts/runtime_completion_contract_ma.md` — section 7: Canonical Checkpoint Law; authoritative source for when canonical hashing is required
- `docs/engine/deterministic_execution.md` — CAUTION: this doc references `get_hash()` but source code at `src/engine/checkpoint.py:19` has `compute_hash()` — implementer must verify the canonical method name before writing the scheduler (see Assumptions)
- `docs/engine/kernel.md` — 6-phase tick pipeline
- `docs/engine/authoritative_pipeline.md`
- `docs/parity_ledger/infrastructure.yaml`
- `memory_features.md` (Feature 5)

## Related Code Areas
- `src/engine/checkpoint.py:11` — `CanonicalStateHasher` class
- `src/engine/checkpoint.py:17` — `get_hash(state)` — the single canonical hash entry point
- `src/engine/checkpoint.py:36` — `to_canonical_data()` — full collection walk
- `src/engine/kernel.py:780` — `get_hash()` called inside tick (verify if audit-mode guarded)
- `src/engine/kernel.py:800` — `get_hash()` called at run end (sanctioned boundary)
- `src/certification/harness.py:182` / `:263` — `get_hash()` for secondary and final hash (sanctioned boundary)
- `src/replay/fingerprint.py:14` — mentions full replay/certification hashing

## Assumptions / Open Questions
- **Canonical method name is `get_hash()`**: `docs/engine/deterministic_execution.md` and source code at `src/engine/checkpoint.py:17` agree — the method is `CanonicalStateHasher.get_hash(state)`. It is already called from `kernel.py:780`, `kernel.py:800`, and `harness.py:182`/`263`. No discrepancy. The scheduler must wrap `get_hash()`, not introduce a second name.
- Is `CanonicalStateHasher.get_hash()` called from inside the tick pipeline at `kernel.py:780`? Yes — the architecture test must confirm whether this is a sanctioned audit-mode call or a casual per-tick call. If it is inside audit mode guard, it may be acceptable; if unconditional, that is the violation the scheduler fixes.
- LIGHT hash collision risk: tick+seed+collection counts is not cryptographically safe, but it's sufficient as a dirty signal. Document this explicitly.

## Implementation Notes
- `HashScheduleViolation` should print the caller tick and reason so the violation is easy to diagnose
- The LIGHT hash can use `hashlib.md5` (not SHA-256) since it is non-cryptographic; document this clearly
- The sanctioned-boundary list is hardcoded in `allow_full_hash_at()` — do not make it runtime-configurable for now

## Test Summary
- `tests/unit/engine/test_hash_scheduler.py` (new):
  - `test_full_hash_allowed_at_tick_zero`
  - `test_full_hash_allowed_with_certification_reason`
  - `test_full_hash_raises_outside_sanctioned_boundary`
  - `test_light_hash_always_allowed`
  - `test_light_hash_is_fast` (assert duration < 1ms for small state)
  - `test_architecture_no_casual_compute_hash_in_tick_path` (grep/AST based)
- Run: `pytest tests/unit/engine/ -v`

## Files Changed
_(filled after implementation)_

## Completion Summary
_(filled after implementation)_
