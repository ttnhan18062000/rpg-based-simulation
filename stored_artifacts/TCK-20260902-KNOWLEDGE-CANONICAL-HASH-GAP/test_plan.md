---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP
artifact_type: test_plan
tags: [cognition, determinism]
---

# Test Plan — TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP

**Normal flow:** two entities identical except for `source_trust` produce different `to_canonical_dict()`
output and different `CanonicalStateHasher.get_hash()` output.

**Edge cases:** each of the other 8 newly-covered fields independently changes the canonical dict when
diverged (tested via one parametrized-style loop, not 8 separate near-duplicate tests).

**Failure modes:** `profile` divergence must NOT change the canonical dict (regression guard on the
intentional exclusion — if this starts failing, the exclusion is no longer safe and needs re-review).

**Regression-prone paths:** full existing canonical-hash/replay/certification suite, since this is a
central, load-bearing hash used by the kernel's own per-tick audit.

**Scope command (used):**
`pytest tests/unit/core/ tests/unit/engine/test_hash_scheduler.py tests/unit/engine/test_resource_budget_gate.py tests/unit/kernel/ tests/certification/ -m "not slow"`
— 408 passed, 1 skipped (pre-existing, unrelated), 0 failed.
Also: `pytest tests/integration/kernel/test_determinism_suite.py tests/integration/kernel/test_checkpoint_reproducibility.py tests/integration/kernel/test_replay_fidelity.py -m "not slow"`
— 15 passed.
