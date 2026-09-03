---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-SOCIAL-CANONICAL-HASH-GAP
artifact_type: test_plan
tags: [social, determinism]
---

# Test Plan — TCK-20260902-SOCIAL-CANONICAL-HASH-GAP

**Normal flow:** each of the 7 newly-covered fields independently changes `to_canonical_dict()` output
when it diverges from default; `nemesis_ids` specifically confirmed end-to-end via
`CanonicalStateHasher.get_hash()`.

**Edge cases:** `nemesis_ids` (a `Set`, not a `Dict`/`List`) needs distinct serialization handling
(`sorted(...)`) — covered explicitly since it's structurally different from the other 6 fields.

**Failure modes:** existing determinism/social-domain regression tests must not regress.

**Regression-prone paths:** full existing canonical-hash/replay/certification suite, plus the social
domain's own test suite (contracts, bonds, memory, lifecycle) since this touches shared social state
construction paths.

**Scope command (used):**
`pytest tests/unit/core/ tests/unit/engine/test_hash_scheduler.py tests/unit/engine/test_resource_budget_gate.py tests/unit/kernel/ tests/certification/ -m "not slow"`
— 405 passed, 1 skipped (pre-existing, unrelated), 0 failed.
Also: `pytest tests/unit/social/ tests/unit/strategic/test_strategic_social_contracts.py tests/unit/strategic/test_social_contract_materialization.py -m "not slow"`
— 259 passed.
