---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS
date: 2026-10-27
tags: [performance, determinism]
---

# Test plan

Unit: `tests/unit/engine/test_proof_digest_contract.py` (v3 pin, v2 migration proof, 7 positive controls), `test_acting_hostile_is_an_act_not_a_state.py` (flipped), `test_hash_scheduler.py`, `tests/unit/perf/test_benchmark_record.py`, `test_long_run_record.py`; `tests/tools/test_hash_callsite_inventory.py`, `test_perf_inventories_committed_in_sync.py`.
Integration: cross-PYTHONHASHSEED (seeds 1 and 12345, 3 worlds x 300 ticks); `paired --neutral` 3 worlds x s42 x 1000 ticks.

## Proof Plan
level: unit plus integration; proof kind: byte-pinned digests and paired outcome comparison; oracle source: FIXTURE_DIGEST_V2 (unchanged) and the base arm's cached outcomes; expected effect: only digests move; selected commands: see Test Summary.
