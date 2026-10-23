---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261023-COOPERATION-CANDIDATES-ENUMERATED-PER-ENTITY-PER-TICK
artifact_type: investigation
date: 2026-10-23
tags: [performance, cooperation]
---

# Investigation
The old scan visited every entity per requester and called are_entities_hostile first. The keep rule is `dist <= radius or trust > 0.7` (Euclid; the bbox pre-check is a subset test), so the candidate set is {within radius} ∪ {trusted ids}. Ties in the final sort keep `state.entities` iteration order, so the index sorts by that rank. Nothing in the phase loop changes position, liveness or activity (updates are deferred), so one index per tick is valid. Pending-offer lookup was fixed earlier the same way (#394 pattern).
