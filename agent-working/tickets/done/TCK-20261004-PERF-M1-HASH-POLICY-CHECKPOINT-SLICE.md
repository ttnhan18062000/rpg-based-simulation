---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE
phase: done
date: 2026-10-04
tags: [performance, determinism, certification, testing]
---

# TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE

## Title
PERF-M1-T03a: apply the `checkpoint.py` half of the PERF-D5 hash policy and move parity tests to the proof digest

## Status
DONE

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
- **Gate finding:** `src/certification/harness.py` (gated) imports `HashMode` and calls `compute_hash(..., mode=HashMode.FULL, reason="certification")`. So `HashMode` stays with the single member `FULL`, and the `mode` parameter stays (default now `FULL`), until `PERF-M1-T03b`. Only `HashMode.LIGHT` is gone. No gated file was edited.
- `checkpoint.py`: `PROOF_DIGEST_SCHEME = "flat-sha256-v1"`, `DigestStatus` (`COMPUTED`, `NOT_COMPUTED_UNSANCTIONED_BOUNDARY`, `NOT_COMPUTED_LIVE_POLICY` (defined for T03b, no producer yet)), frozen `ProofDigest(scheme, tick, status, value)` (value set if and only if computed), `CanonicalHashScheduler.compute_digest` (reports instead of raising). `compute_hash` is flat-only. `BudgetedCanonicalHasher` removed.
- `DEFAULT_HASHING_BUDGET` / `max_full_hashes_per_100_ticks` in `src/config/optimization_profiles.py` now have no consumer. Left in place (config is outside this ticket); recorded in parity ledger `INFRA-196`.
- Inventory: `tools/perf/hash_callsite_inventory.py` drops the Budgeted entries and gains `compute_digest`; committed JSON and the generated block of the md regenerated with the tool; a dated update note added to the md (its 2026-10-03 prose is history). `--check` exits 0.
- Docs: `docs/engine/deterministic_execution.md` ("The canonical hash") and the PERF-D5 status line updated. Parity ledger: `INFRA-196` set to `unsupported` with a support boundary (retired), `INFRA-197` text updated; `make parity-ledger-schema-check` OK (0 rose, 0 new).
- AC1 byte-identity: the fixture digest `ec75b106...05f5` was computed with `origin/main`'s own `checkpoint.py` (`git show`), equals the current one, and is pinned in `test_proof_digest_contract.py`. `checkpoint.py` is identical at `9793aee08` and `origin/main`.

- **Process deviation (fact):** staging artifacts were written after implementation; content matches what was done.

### Carry-over to PERF-M1-T03b (gated, waits for the RPG-core entry gate)
- Kernel per-tick and shutdown digests go through the scheduler, with the typed status replacing `"SKIPPED"` (and `NOT_COMPUTED_LIVE_POLICY` gets its producer).
- The harness's hand-written copy (`CertificationHarness._write_full_evidence`) is replaced by a call; that then removes `HashMode` and the `mode` parameter.
- `DEFAULT_HASHING_BUDGET` and the `hashing` budget entry are retired.
- The digest schedule becomes a declared runtime-profile field.

### Fingerprint-comparing tests: disposition (AC3)
| Test | Claim | Disposition |
|---|---|---|
| `tests/integration/kernel/test_executor_determinism.py` (2 tests) | sequential vs concurrent, run vs run equality | moved to `CanonicalStateHasher.get_hash` |
| `tests/integration/kernel/test_seed_stability.py` (2 tests) | same seed equal per tick; different seeds differ | moved to `get_hash` |
| `tests/perf/test_concurrency_parity.py` | local vs concurrent executor equality | moved to `get_hash` |
| `tests/perf/test_dirty_parity.py` | dirty-set vs full-scan equality | moved to `get_hash` (variables renamed `digest_*`) |
| `tests/integration/campaigns/test_phase9_campaign_runner.py` | two campaign runs equal | moved to `get_hash` |
| `tests/perf/test_apply_compaction_perf.py`, `tests/unit/domains/optimization/test_state_update_compactor.py` | compacted state equals raw state | moved to `get_hash` |
| `tests/certification/test_world_compile_determinism.py` | two compiles equal; different seeds differ | moved to the report's `canonical_state_hash`; the fingerprint assertion stays beside it, commented as a stability check |
| `tests/integration/kernel/test_replay_fidelity.py`, `tests/unit/replay/test_fingerprint_identity_coverage.py` | what the fingerprint can see (coverage) | relabelled in the module docstring as stability-check coverage tests |
| `tests/integration/kernel/test_p1_replay_fidelity.py` (fingerprint test), `tests/unit/core/test_entity_integrity.py` (fingerprint test), `tests/architecture/test_social_write_paths.py` (comment only) | fingerprint coverage of a field; no cross-run equality | unchanged: coverage of the fingerprint itself, not a proof claim |

## Test Summary
- New `tests/unit/engine/test_proof_digest_contract.py` (6 passed): byte-identity, harness copy equals `get_hash` on a real movement and resource state, cached-dict audit on real runs (non-vacuous: 10 to 11 cached classes found) and a guard that an in-place poisoned cache is detected (mutation proof).
- `test_hash_scheduler.py` rewritten for flat-only and `ProofDigest`; Budgeted block removed from `test_resource_budget_gate.py`.
- Migrated parity tests: 37 passed (budget off, 65 s total). Scoped bundle (docs, scheduler, budget gate, contract, inventories, checkpoint reproducibility, determinism suite, snapshot integrity, evidence levels, unit/perf; `not slow`): 194 passed, 2 skipped, 1 xfailed.
- `hash_callsite_inventory.py --check` exits 0; `git grep` finds no `BudgetedCanonicalHasher` or `HashMode.LIGHT` in `src/`, `tests/`, `tools/`.
- AC6: no test is newly slow. The flat hash costs 0.41 ms against 0.05 ms for the fingerprint on a 6-entity state; the slowest migrated test (`test_dirty_parity`, 21 s) was already `slow`. No marker added.

## Files Changed
- `src/engine/checkpoint.py` (the only `src/` file)
- `tools/perf/hash_callsite_inventory.py`; `docs/performance/hash_callsite_inventory.{json,md}`
- `docs/engine/deterministic_execution.md`, `docs/architecture/performance_optimization_decisions.md`, `docs/parity_ledger/infrastructure.yaml`, `docs/REGISTRY.yaml`
- Tests: `tests/unit/engine/test_proof_digest_contract.py` (new), `tests/unit/engine/test_hash_scheduler.py`, `tests/unit/engine/test_resource_budget_gate.py`, `tests/tools/test_hash_callsite_inventory.py`, and the migrated parity tests listed above

## Completion Summary
The `checkpoint.py` half of PERF-D5 is built: the proof digest scheme is named `flat-sha256-v1` and has a typed record and status, `BudgetedCanonicalHasher` and `HashMode.LIGHT` are retired, and cross-run parity tests compare the flat hash. Hash values are unchanged. The kernel and certification-harness half (T03b) is carried over and waits for the entry gate.
