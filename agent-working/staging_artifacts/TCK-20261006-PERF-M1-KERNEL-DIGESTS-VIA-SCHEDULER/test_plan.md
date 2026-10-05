---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER
date: 2026-10-06
tags: [performance, determinism, engine, testing]
---

# Test plan: TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER

- Kernel TICK_END payload computed: value equals `CanonicalStateHasher.get_hash` of the same state, scheme `flat-sha256-v1`, status `computed`.
- DEGRADED without audit: payload hash None, status `not_computed_live_policy`; no "SKIPPED" string anywhere.
- SURVIVAL: no TICK_END.
- Shutdown digest equals `get_hash`; `ShutdownResult.final_hash` unchanged.
- Harness: both digests via the scheduler; `HashMode` has no hits.
- Existing parity: `tests/unit/engine/test_proof_digest_contract.py`, cross-run parity, `tests/unit/kernel/`, `tests/certification/` (within local limits).
