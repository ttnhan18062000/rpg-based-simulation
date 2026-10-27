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

# Plan: proof digest v3

1. `src/engine/checkpoint.py` only (rpg's lift, #593 issuecomment-6420451647): `PROOF_DIGEST_SCHEME = "flat-sha256-v3"`; add the six carried-state keys to `to_canonical_data`; remove `DIGEST_EXCLUDED_COMBAT_KEYS` and `_entity_digest_form` so `last_hit_tick` is hashed. No change to restore, replay or the payload shape.
2. `HashScheme.FLAT_SHA256_V3` in `src/perf/benchmark_record.py`; `SCHEMA_VERSION` unchanged.
3. Tests: `FIXTURE_DIGEST_V3`, the v3-minus-seven = v2 migration proof, seven positive controls, the flipped step-B test, scheme asserts.
4. Docs: schema, ledger row, hash_callsite_inventory (regenerated), PERF-D5 amendment, rpg-owned scheme citations, INFRA-429.
5. Proofs: cross-PYTHONHASHSEED determinism, `paired --neutral` (amended condition 2, option A), digest cost (PROVISIONAL).
