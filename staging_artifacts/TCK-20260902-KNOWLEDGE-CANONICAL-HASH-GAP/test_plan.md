---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP
artifact_type: test_plan
tags: [cognition, determinism]
---

# Test Plan — TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP

**Normal flow:** two entities identical except for `source_trust` (or another newly-covered field)
produce different canonical hashes; two fully-identical entities produce the same hash.

**Edge cases:** empty/default `SourceTrustEntry` collections must still serialize distinctly from
populated ones — the same falsy-value trap named in the Social ticket's test plan applies here too.

**Failure modes:** a regression test specifically exercising `source_trust_bonus`-driven detour
selection (`belief_and_detour_contract.md`) should still pass unchanged — this ticket adds hash
coverage only, it must not alter `source_trust`'s actual scoring behavior.

**Regression-prone paths:** existing fixture `world_compile_report.json` `state_hash` values; existing
canonical-hash/replay determinism suite.

**Scope command (fill in exact path once located):**
`pytest tests/unit/core/ tests/unit/cognition/ -k "canonical or source_trust" -m "not slow"` (confirm
real test file paths during implementation — do not run the full suite).
