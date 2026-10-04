---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER
artifact_type: plan
tags: [mcp, live-map, testing]
---

# Plan — TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER

1. Commit the ticket start with the planner rulings, so HEAD is clean.
2. Run every M5 check on that clean HEAD (pytest, store audit/verify/gc/export-runtime, vitest, scoped eslint/tsc/build, 4-client pilot capture, old rehearsal capture) and name the commit.
3. Rewrite `surface_rehearsal_result.md` as a dated result with the 2026-10-03 text kept as history; draft the charter; dated notes in plans 06, 07 and the README (not plan 05).
4. Close the ticket and the epic in the last commit.
