---
status: historical
layer: testing
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261028-N15-KNOWN-V3-STARVATIONS-RECHECK-ON-THE-GATE-AFTER-STEP-A
phase: done
date: 2026-10-28
tags: [benchmarking]
---

# investigation

- Run 40653115297: stale_known_entries lists crowded_frontier/46/38, frontier_living_world/44/2 (and urban_political/44/28) as no longer failing.
- Earlier runs 40490584465 (2afdba653) and 40314093440 (3533fde71), both before #769, list the same three as stale: step A did not clear them.
- Unowned fails in 40653115297: V6 fls s45 and V3 crowded_frontier s42 leader 30 were present in both earlier runs; V3 fls s43 merchant 38 t2518 is absent in both (new since 2afdba653), reported to rpg-planner.
