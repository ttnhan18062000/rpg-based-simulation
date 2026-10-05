---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK
artifact_type: plan
tags: [engine, determinism]
---

# Plan

1. Prove or refute the link first (strong-reference discriminator) and compare on bare `origin/main`.
2. Only then fix: remove the identity-keyed registry from `DirtySetBuilder` (marking is idempotent), keep no
   references, introduce no other allocation-dependent key.
3. Probe `get_frozen` and record the result either way.
4. Regression test that fails deterministically on the old keying by making every `id()` collide.
5. Correct `docs/engine/deterministic_execution.md` (the `audit_mode` sentence), add a parity-ledger entry.

Scope guards: no change to the canonical hash or its contract; no change to `executor.py` or `checkpoint.py`
(held, unused); the parked slow-regression root cause is not touched.
