---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER
phase: implement
date: 2026-10-06
tags: [performance, determinism, engine]
---

# TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER

## Title
PERF-M1-T03b: kernel and certification-harness digests go through CanonicalHashScheduler with a typed status, and HashMode is removed

## Status
INPROGRESS

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Released by the owner on 2026-10-06 (roadmap gate item 6). This is the carry-over from T03a,
`agent-working/tickets/done/TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE.md` ("Carry-over to
PERF-M1-T03b"). T03a built the `checkpoint.py` half of PERF-D5: scheme `flat-sha256-v1`,
`DigestStatus`, a frozen `ProofDigest`, and `CanonicalHashScheduler.compute_digest`. Two gated callers
were left.

- `src/engine/kernel.py` `_phase_persistence` (about line 1187): `tick_hash = "SKIPPED"`, otherwise
  `CanonicalStateHasher.get_hash(self._state)` when replay is allowed and (`audit_mode` or replay
  richness is `FULL`). Find the shutdown digest too.
- `src/certification/harness.py` about lines 185 and 310: a hand-written copy that calls
  `compute_hash(..., mode=HashMode.FULL, reason="certification")`.

## Scope
1. Kernel per-tick and shutdown digests go through `CanonicalHashScheduler.compute_digest`. The trace
   carries a `ProofDigest` (scheme, tick, status, value), not a bare string. When the policy does not
   hash, the status is `NOT_COMPUTED_LIVE_POLICY`, which gives that member its first producer.
   **Keep when hashing happens unchanged** (PERF-D5 point 4: Live hashing cadence is unchanged until
   Gate A). Hash values must not change.
2. Every consumer of the kernel trace's hash field (replay reader, replay verification, observability,
   API) reads the typed form. List each consumer in Implementation Notes. If a stored replay format
   changes, add a schema/version note (T03a deferred this to here).
3. `CertificationHarness._write_full_evidence` and the other copy call the scheduler. They no longer
   build the hash by hand.
4. Then remove `HashMode` and the `mode` parameter from `src/engine/checkpoint.py`, and from every
   caller and test.
5. Retire `DEFAULT_HASHING_BUDGET` and the `"hashing"` entry in `src/config/optimization_profiles.py`.
   They have had no consumer since T03a. Check readers in `tools/`, `tests/` and the docs first.
   Update parity ledger `INFRA-196`.
6. Regenerate the hash call-site inventory with `tools/perf/hash_callsite_inventory.py`, never by
   hand. Update `docs/engine/deterministic_execution.md` ("The canonical hash") and the PERF-D5 status
   line.

## Out of Scope
- When Live runs hash (PERF-D5 point 4), float rounding (point 5), incremental or tree hashing (point 7).
- The tick-budget throttle (sibling ticket).
- `src/core/state.py`, `src/engine/apply.py`, `src/engine/pipeline.py`.
- PERF-M1-T05 (the invalidation ledger), which consumes this ticket's result.

## Acceptance Criteria
1. No `"SKIPPED"` hash string is left in `kernel.py`. The trace carries a typed digest status, and a
   test covers both the computed and the not-computed status.
2. Hash values are unchanged. A test compares the kernel's digest for a fixed seed with
   `CanonicalStateHasher.get_hash` on the same state, and the existing cross-run parity tests pass.
3. The certification harness calls the scheduler. No hand-written hash copy remains.
4. `HashMode` and the `mode` parameter no longer exist (`grep` shows no hits in `src/`, `tests/` or
   `tools/`).
5. `DEFAULT_HASHING_BUDGET` and the `"hashing"` budget entry are removed, or kept with a recorded
   reason if a reader exists. `INFRA-196` is updated.
6. Every trace-hash consumer is listed, and each one is updated or shown unaffected. A replay schema
   note exists if the format changed.
7. The hash inventory `--check` passes, and the docs and parity ledger are updated.
8. `uv run make code-health` and `uv run make typecheck-py` report no new or worse finding.
9. Scoped tests pass: `tests/unit/kernel/`, `tests/certification/` (the parts that run within local
   limits; record any that cannot), and the replay and checkpoint tests T03a touched.

## Related Tickets
- `TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE` (T03a, done; its carry-over is this ticket)
- `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY` (same batch)
- PERF-M1-T05 (consumes this ticket's result)

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D5)
- `docs/engine/deterministic_execution.md` ("The canonical hash")
- `docs/plans/design_enhancement/performance_optimization/performance_m1_correctness_prerequisites_epic.md`
- `docs/performance/hash_callsite_inventory.md`

## Related Stored Artifacts
- T03a's stored artifacts under `agent-working/stored_artifacts/TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE/`

## Related Code Areas
- `src/engine/kernel.py` (`_phase_persistence`, shutdown)
- `src/engine/checkpoint.py`
- `src/certification/harness.py`
- `src/config/optimization_profiles.py`
- the replay reader and verifier (find them)

## Assumptions / Open Questions
- If a replay consumer outside the lifted files needs a change, the ticket stops and asks the planner.
  This applies to `src/engine/replay_manager.py`, for example: it is not one of the four core files, but
  check it against the lift before editing.

## Implementation Notes
- **Kernel.** `_phase_persistence` takes the per-tick digest with `CanonicalHashScheduler().compute_digest(state, tick,
  reason="replay")` under the same condition as before (replay allowed and (`audit_mode` or richness FULL)), so when hashing
  happens is unchanged. Otherwise it builds the record with the new `CanonicalHashScheduler.not_computed_by_policy(tick)`
  (`NOT_COMPUTED_LIVE_POLICY`, first producer). `shutdown` takes its digest at the run-end boundary
  (`CanonicalHashScheduler(run_end_tick).compute_digest(...).require_value()`); `ShutdownResult.final_hash` stays a string.
  `ProofDigest.require_value()` is new: it returns the value or raises if it was not computed.
- **TICK_END payload** (planner-approved 2026-10-06): `{"hash": value-or-null, "scheme": "flat-sha256-v1", "digest_status":
  "<enum value>"}`. Plain JSON. Schema note (old vs new shape and the rule for readers) is in `deterministic_execution.md`
  ("The canonical hash").
- **Trace-hash consumers (AC 6).** None in code: grep of `TICK_END`, `payload["hash"]`, `get("hash")` over `src/`, `tools/`,
  `frontend/src/` finds only the producer (`kernel.py`). `src/replay/fingerprint.py`, `perf/long_run_harness.py` and the
  certification code read `ShutdownResult.final_hash` / `state_hash`, not the trace (unchanged). Readers that exist are
  documentation (`known_limitations.md` 2.4, `kernel.md`, `deterministic_execution.md`, `hash_callsite_inventory.md`, parity
  ledger; updated) and two tests: `tests/unit/engine/test_hash_scheduler.py` (asserted `"SKIPPED"`; now asserts the typed
  status) and `tests/unit/kernel/test_verification_level.py` (scans the TICK_END trail, never the hash; unaffected, passes).
  Replays on disk carry `"hash": "SKIPPED"` with no scheme or status; the schema note says a reader treats that and the new
  `null` as "not computed" and never as equal evidence. No replay consumer outside the lifted files needed an edit.
- **Harness.** One helper, `CertificationHarness._certification_digest(state)`, calls `compute_digest(..., reason="certification")`.
  All three sites use it: the secondary-run hash, `_get_baseline_hash`, and `_write_full_evidence` (which no longer hashes the
  compact JSON by hand, and `hashlib` is no longer imported there).
- **Removed.** `HashMode` and the `mode` parameter (no hits in `src/`, `tests/`, `tools/` outside the test that asserts they
  are gone). `DEFAULT_HASHING_BUDGET`, the `"hashing"` entries (production and debug) and the `max_full_hashes_per_100_ticks`
  field: the field had no reader except the budget-gate test once the entry went, so I removed it too (a small step past the
  ticket text; say if it should come back). `INFRA-196` updated, `INFRA-197` updated, new `INFRA-424`.
- **Hash values unchanged:** a test compares the kernel's computed digest, the shutdown digest and the harness digest with
  `CanonicalStateHasher.get_hash`, and `test_proof_digest_contract.py` (fixed-fixture digest) and the cross-run parity tests pass.

## Test Summary
- New `tests/unit/engine/test_kernel_digest_via_scheduler.py` (10 tests): computed and not-computed payloads, audit mode, no
  `"SKIPPED"` or direct `get_hash` in `kernel.py`, shutdown through the scheduler, harness through the scheduler,
  `HashMode` gone, no `mode` parameter. Written first; the ones about the typed payload, the missing `"SKIPPED"`, the scheduler calls and `HashMode` failed before the change.
- Updated: `test_hash_scheduler.py` (DEGRADED typed status, `HashMode` tests removed), `test_proof_digest_contract.py`
  (wording), `test_resource_budget_gate.py` (hashing budget removed), `test_hash_callsite_inventory.py` (kernel now maps to
  `compute_digest`).
- Run: `tests/unit/engine`, `tests/unit/kernel`, the three inventory tests: 378 passed, 1 skipped. `tests/certification` minus
  `test_cert_long_run_stability.py`: 71 passed, 1 skipped. `tests/integration/kernel` (not slow) plus the signal tests: 134 passed.
- Not run locally: `tests/certification/test_cert_long_run_stability.py` (60 s conftest limit, known local gap; CI is the check).
- `make code-health`: 0 new, 0 worse, 11 improved. `make typecheck-py`: no new error. `hash_callsite_inventory --check` and
  `wall_clock_inventory --check` pass.

## Files Changed
- `src/engine/kernel.py`, `src/engine/checkpoint.py`, `src/certification/harness.py`, `src/config/optimization_profiles.py`
- `tests/unit/engine/test_kernel_digest_via_scheduler.py` (new), `test_hash_scheduler.py`, `test_proof_digest_contract.py`,
  `test_resource_budget_gate.py`, `tests/tools/test_hash_callsite_inventory.py`
- `docs/engine/deterministic_execution.md`, `known_limitations.md`, `kernel.md`, `docs/architecture/performance_optimization_decisions.md`,
  `docs/parity_ledger/infrastructure.yaml` (INFRA-196, 197, 424), `docs/performance/hash_callsite_inventory.{json,md}` (regenerated)

## Completion Summary
