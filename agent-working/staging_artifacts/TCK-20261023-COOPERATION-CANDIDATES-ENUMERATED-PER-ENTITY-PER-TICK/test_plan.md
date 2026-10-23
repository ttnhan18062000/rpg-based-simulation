---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261023-COOPERATION-CANDIDATES-ENUMERATED-PER-ENTITY-PER-TICK
artifact_type: test_plan
date: 2026-10-23
tags: [performance, cooperation]
---

# Test plan
- Differential: verbatim old scan vs index, random states (shuffled insertion order, dead/inactive, role 1, mixed factions, boundary and negative positions, trust 0.7/0.71), several radii and caps; plus stale-radius index fallback.
- Existing cooperation and hostility-sweep tests.
- NEUTRAL proof (hash x3 worlds, paired.py --neutral) and phase timing run on the planner's "host free".
