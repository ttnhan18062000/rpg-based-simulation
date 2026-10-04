---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE
phase: open
date: 2026-10-04
tags: [performance, determinism, certification, testing]
---

# TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE

## Title
PERF-M1-T03a: apply the `checkpoint.py` half of the PERF-D5 hash policy and move parity tests to the proof digest

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
PERF-D5 (hash policy) was approved by the owner on 2026-10-03, and its mechanism changes waited for
the entry gate. The partial lift on 2026-10-04 allows `src/engine/checkpoint.py`. It does not allow
`kernel.py` or `src/certification/harness.py`. This ticket is the slice that fits inside the lift.
The rest is `PERF-M1-T03b`, unfiled, which waits for the gate:
- the kernel's per-tick and shutdown hashes going through the scheduler;
- a typed digest status in place of `"SKIPPED"` in the kernel's output;
- the harness's hand-written hash copy replaced by a call.

Facts (`docs/performance/hash_callsite_inventory.md`, re-checked 2026-10-04):
- `BudgetedCanonicalHasher` has no production caller. It is used only by
  `tests/unit/engine/test_resource_budget_gate.py` and a fixture in
  `tests/tools/test_hash_callsite_inventory.py`.
- `HashMode.LIGHT` is never requested in production. The certification harness always passes
  `HashMode.FULL`. `CanonicalHashScheduler.compute_hash` still defaults to `LIGHT`.
- Several determinism tests compare fingerprints, not flat hashes:
  - `tests/perf/test_concurrency_parity.py`;
  - `tests/perf/test_dirty_parity.py`;
  - `tests/integration/kernel/test_p1_replay_fidelity.py`;
  - others found by a search for `get_fingerprint`.

## Scope
- **Scheme identity (D5 point 2, definitions only):** name the proof digest scheme
  `flat-sha256-v1` as a constant in `checkpoint.py`. Add a typed digest record (scheme, tick,
  status) and a typed status enum (computed / not computed and why). `CanonicalHashScheduler`
  returns or exposes it. Digest values do not change
- **Retire stale-serving mechanisms (D5 point 3):** remove `BudgetedCanonicalHasher` and
  `HashMode.LIGHT`, and make `CanonicalHashScheduler.compute_hash` compute the flat digest only.
  Update or delete the tests that exercise them, and update `tools/perf/hash_callsite_inventory.py`
  and its committed inventory. Rerun its `--check`
- **Parity tests use the proof digest (D5 point 6):** every test that claims cross-run,
  cross-executor or replay equality compares `CanonicalStateHasher.get_hash`. A fingerprint
  comparison is either moved to the flat hash or renamed and documented as a stability check. List
  each test and its disposition in the ticket. Tests only; no `src/` change for this part
- **Verification from D5:**
  - a test that the certification harness's digest equals `get_hash` for the same state, until
    T03b removes the copy;
  - an audit test that recomputes each cached canonical dict and compares it with the cache, over
    a short non-combat run.
- Update `docs/engine/deterministic_execution.md` ("The canonical hash") and the parity ledger
  (`infrastructure.yaml`) for the scheme name and the retired mechanisms

## Out of Scope
- `src/engine/kernel.py` and `src/certification/harness.py`: no edit (T03b, gated)
- Changing when Live runs hash (D5 point 4: unchanged until Gate A)
- Float rounding (D5 point 5: removed from the contract, not implemented)
- Incremental or tree hashing (D5 point 7)
- Any hash cost measurement as evidence (gated)

## Acceptance Criteria
1. `flat-sha256-v1` and a typed digest record and status exist in `checkpoint.py`. For any state,
   `get_hash` output is byte-identical to `origin/main`, checked by a test on a fixed fixture
2. `BudgetedCanonicalHasher` and `HashMode.LIGHT` are gone. `git grep` finds no reference in
   `src/`, `tests/` or `tools/`, except historical docs
3. Every fingerprint-comparing determinism test is moved or relabelled, with a per-test table in
   the ticket
4. The harness-equals-`get_hash` test and the cached-canonical-dict audit test pass. The audit
   test fails when a cached dict is mutated in place (mutation proof recorded)
5. `hash_callsite_inventory.py --check` passes. No gated file appears in `git diff --stat`
6. Tests moved to the flat hash and newly slow are marked `slow`, and that is stated in the ticket

## Related Tickets
- `TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION` (uses the proof digest)
- `TCK-20261004-PERF-M1-PHASE-INVENTORY-REGEN` (adds the inventory `--check` test)

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D5)
- `docs/performance/hash_callsite_inventory.md`
- `docs/engine/deterministic_execution.md`
- `docs/plans/design_enhancement/performance_optimization/performance_m1_correctness_prerequisites_epic.md` (PERF-M1-T03)

## Related Stored Artifacts
- none

## Related Code Areas
- `src/engine/checkpoint.py` (edit allowed)
- `src/engine/kernel.py`, `src/certification/harness.py` (read only)
- `tests/unit/engine/test_hash_scheduler.py`, `tests/unit/engine/test_resource_budget_gate.py`,
  `tests/tools/test_hash_callsite_inventory.py`, and the fingerprint-comparing tests

## Assumptions / Open Questions
- `test_resource_budget_gate.py` also tests other budget mechanisms. Remove only the
  `BudgetedCanonicalHasher` part
- A replay payload schema note is needed only when the kernel emits the typed status (T03b), not here
- If a fingerprint test cannot move without a `src/` change outside `checkpoint.py`, relabel it and
  leave the move to T03b

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
