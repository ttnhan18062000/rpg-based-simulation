---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE
date: 2026-10-04
tags: [performance, determinism, testing]
---

# Investigation: TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE

## Findings
- Gate: `src/certification/harness.py` (gated) calls `CanonicalHashScheduler().compute_hash(..., mode=HashMode.FULL, reason="certification")` at lines 186 and 311 and imports `HashMode`. Removing `HashMode` or the `mode` parameter would force a gated edit, so `HashMode` stays with only `FULL` and `mode` stays accepted until PERF-M1-T03b. Only `HashMode.LIGHT` is removed.
- `BudgetedCanonicalHasher` had no production caller; its only users were `tests/unit/engine/test_resource_budget_gate.py` (one class) and a text fixture in `tests/tools/test_hash_callsite_inventory.py`.
- `DEFAULT_HASHING_BUDGET` / `max_full_hashes_per_100_ticks` (`src/config/optimization_profiles.py`) lose their only consumer. Config is outside the lift and outside this ticket; left in place and recorded in the ledger.
- The harness's hand-written flat-hash copy is `CertificationHarness._write_full_evidence` (`harness.py:253-257`), not the two `compute_hash` call sites.
- 22 state classes cache `_canonical_cache`; the audit walks any dataclass graph, clears all caches, recomputes bottom-up and compares.
- Flat hash costs 0.41 ms against 0.05 ms for the fingerprint on a 6-entity state, so moving parity tests to the flat hash makes none of them newly slow.

## Decisions
- `DigestStatus` has `COMPUTED`, `NOT_COMPUTED_UNSANCTIONED_BOUNDARY` and `NOT_COMPUTED_LIVE_POLICY`. The last has no producer yet; it is the typed form of the kernel's `"SKIPPED"` for T03b. Defined only.
- `compute_hash` and `compute_digest` each call `CanonicalStateHasher.get_hash` directly (no delegation), so the inventory scanner resolves both call sites.
