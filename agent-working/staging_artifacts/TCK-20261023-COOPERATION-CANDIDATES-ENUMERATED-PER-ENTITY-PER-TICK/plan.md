---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261023-COOPERATION-CANDIDATES-ENUMERATED-PER-ENTITY-PER-TICK
artifact_type: plan
date: 2026-10-23
tags: [performance, cooperation]
---

# Plan
1. `PartnerCandidateIndex` (providers.py): active+alive entities in `state.entities` order (rank) plus a grid with cell = spatial radius; requester's candidates = 3x3 cells ∪ ids with trust > 0.7, sorted by rank.
2. `get_candidates(..., index=None)`: builds a one-off index when none is passed (or radius differs). Hostility is checked after the distance/trust filter (hostility only removes, so the result is unchanged; far entities no longer cost a catalog call). Hostility semantics untouched (H1).
3. `CooperationPhase.execute` builds the index once per tick next to the pending-offer index.
Files: src/domains/cooperation/{providers,phase}.py + tests only.
