---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER
date: 2026-10-06
tags: [performance, determinism, engine, testing]
---

# Investigation: TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER

## Call sites (live code)
- `Kernel._phase_persistence`: `tick_hash = "SKIPPED"`, else `CanonicalStateHasher.get_hash` when replay is allowed and
  (`audit_mode` or `replay_richness == "FULL"`); emitted as `TICK_END` payload `{"hash": tick_hash}` only when replay is allowed.
- `Kernel.shutdown`: `final_hash = CanonicalStateHasher.get_hash(self._state)` (always computed); used for the log,
  the replay finalize `state_hash`, and `ShutdownResult.final_hash` (a string, read by `perf/long_run_harness.py`, tests).
- `CertificationHarness` lines ~185 and ~310: `compute_hash(..., mode=HashMode.FULL, reason="certification")`.
  (T03a's "hand-written copy" in `_write_full_evidence` was already pointed at by `test_proof_digest_contract.py`; re-read it.)
- `HashMode`: only `checkpoint.py`, the harness, `tests/unit/engine/test_hash_scheduler.py`.
- `DEFAULT_HASHING_BUDGET` / `"hashing"`: `src/config/optimization_profiles.py`; reader: `tests/unit/engine/test_resource_budget_gate.py`
  (expected subsystem set; non-None field check uses `max_full_hashes_per_100_ticks`).

## TICK_END hash consumers (AC 6)
No code in `src/`, `tools/` or `frontend/` reads the `TICK_END` payload hash (grep of TICK_END, payload["hash"], get("hash")).
Readers are documentation (`known_limitations.md` 2.4, `kernel.md` ~168, `deterministic_execution.md` ~94 and ~164,
`hash_callsite_inventory.md`, parity ledger) and tests: `tests/unit/engine/test_hash_scheduler.py` (asserts `"SKIPPED"`),
`tests/unit/kernel/test_verification_level.py` (scans the TICK_END trail, no hash read). Replays on disk carry
`"hash": "SKIPPED"` with no scheme or status; any future reader must treat that and the new None/NOT_COMPUTED_* as not computed.

## Design
Payload `{"hash": value-or-None, "scheme": PROOF_DIGEST_SCHEME, "digest_status": status.value}` (plain JSON; planner-approved
2026-10-06). Computed digests go through `CanonicalHashScheduler.compute_digest(state, tick, reason="replay")`
(sanctioned reason, so hashing happens exactly when it did before). Not computed under policy:
`ProofDigest(scheme, tick, NOT_COMPUTED_LIVE_POLICY)`. Shutdown uses `CanonicalHashScheduler(run_end_tick=tick).compute_digest`.
