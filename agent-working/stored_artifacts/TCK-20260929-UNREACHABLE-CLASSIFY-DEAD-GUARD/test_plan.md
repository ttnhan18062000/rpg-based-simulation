---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD
artifact_type: test_plan
tags: [investigation, root-cause, corpus, world]
---

# Test Plan — TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD

No repo test change. Verification: greps and code reads at HEAD; one existing scenario file re-run
(`tests/mechanic_scenarios/test_cognition_capacity_fatigue_lead_trim.py`, 3 passed); two uncommitted scratchpad kernel probes
(over-cap scan over 1,500 ticks; influence-shift call count over 1,500 ticks). No regression pin added — the influence defect's
fix ticket is where a test for `DEFEAT` counting as a death belongs.
