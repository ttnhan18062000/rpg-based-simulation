---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-SOCIAL-CANONICAL-HASH-GAP
artifact_type: test_plan
tags: [social, determinism]
---

# Test Plan — TCK-20260902-SOCIAL-CANONICAL-HASH-GAP

**Normal flow:** two entities identical except for one newly-covered field produce different canonical
hashes; two fully-identical entities produce the same hash (no false positive from the change).

**Edge cases:** a field whose default value is falsy/empty (e.g. empty list/dict) must still serialize
distinctly from a populated one — a naive `if value:` guard in `to_canonical_dict()` would silently drop
it back into the same gap being fixed.

**Failure modes:** existing replay/determinism regression tests must not regress — run the full
canonical-hash test file, not just the new field-specific test.

**Regression-prone paths:** any existing fixture `world_compile_report.json` with a committed
`state_hash` — confirm each still matches, or explicitly document + regenerate.

**Scope command (fill in exact path once located):**
`pytest tests/unit/core/ -k "canonical" -m "not slow"` (confirm real test file path during
implementation — do not run the full suite).
