---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT
artifact_type: test_plan
tags: [content, determinism]
---

# Test Plan — TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT

**Normal flow:** `unit_information_source` compiles to exactly 1 Region containing exactly 1
`Place(kind=CITY)`, `state_hash` byte-identical to baseline.

**Failure modes:** a hash change with no corresponding real content change is a bug in the migration
logic, not an acceptable outcome for this single-region/single-place world — it's the trivially
hand-verifiable case specifically because it should be lossless.

**Scope command:** compile `unit_information_source` via the standard world-compile entry point, diff
`world_compile_report.json`'s `state_hash` against the committed one. (Exact CLI invocation to confirm
during implementation.)
