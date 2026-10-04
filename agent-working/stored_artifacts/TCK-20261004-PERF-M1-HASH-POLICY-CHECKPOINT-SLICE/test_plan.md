---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE
date: 2026-10-04
tags: [performance, determinism, testing]
---

# Test plan: TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE

| AC | Test | Proof |
|---|---|---|
| 1 | `test_flat_hash_of_fixed_fixture_is_unchanged_from_main` | digest pinned from `origin/main`'s own `checkpoint.py` |
| 1 | `TestProofDigest` | scheme, tick, status, value; never stale; value set iff computed; immutable |
| 2 | `git grep` | no `BudgetedCanonicalHasher` or `HashMode.LIGHT` in `src/`, `tests/`, `tools/` |
| 3 | per-test table in the ticket | each fingerprint equality test moved or relabelled |
| 4 | `test_certification_harness_digest_equals_get_hash`, `test_no_cached_canonical_dict_is_stale_after_a_real_run`, `test_audit_detects_a_cached_dict_mutated_in_place` | mutation proof |
| 5 | `hash_callsite_inventory.py --check`; `git diff --stat` | exit 0; only `checkpoint.py` under `src/` |
| 6 | timing of flat hash vs fingerprint | no test newly slow |
