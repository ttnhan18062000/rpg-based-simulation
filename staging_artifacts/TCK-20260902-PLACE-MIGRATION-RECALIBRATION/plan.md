---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-RECALIBRATION
artifact_type: plan
tags: [content, determinism]
---

# Plan — TCK-20260902-PLACE-MIGRATION-RECALIBRATION

1. For each of the 21 worlds as it lands via the rollout ticket: diff recompiled `state_hash` against the
   committed baseline.
2. Unchanged hash → record as lossless, no further action.
3. Changed hash → run `grade_anchors.json`, manually triage every grade shift: real regression vs.
   compile-shape noise. Record the triage note per world.
4. Any real regression found → file its own hotfix ticket referencing this one, do not fix inline here.
5. Final summary: N/21 lossless, M/21 noise-triaged, K/21 real regressions (with their ticket links).
