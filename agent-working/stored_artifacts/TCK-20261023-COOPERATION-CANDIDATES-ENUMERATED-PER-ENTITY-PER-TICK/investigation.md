---
status: historical
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

## Evidence (2026-10-24, one host, base 6c1373951 vs new e8b8e0bb3)
- Hash: 3 worlds x seed 42 x 5000t, PYTHONHASHSEED=0, audit_mode (tools.test_architecture.rpg_gate_run kernel): start and final canonical hash equal to base on crowded_frontier (5d840881d7e1...), frontier_living_world (6d5b6a88ed07...), urban_political (4c912b13e14f...).
- `paired.py --neutral` (3 worlds, seed 42, 1000t): IDENTICAL x3, NEUTRAL PASS.
- Cooperation phase, `profile_tick.py --contract pinned --profile PROD_LARGE --sampler none --warmup 3 --ticks 30 --seed 42`, 5 alternating base/new fresh-process runs, median:
  | scenario | cooperation base -> new | tick base -> new |
  |---|---|---|
  | strategic_100 | 164.4 -> 59.6 ms (-64 %) | 267.1 -> 163.6 ms |
  | corpus frontier_marches | 21.6 -> 3.2 ms (-85 %) | 60.1 -> 42.3 ms |
  Per-run cooperation: strategic base 164.9/164.3/163.5/168.4/164.4, new 58.6/60.2/59.9/59.6/59.1; marches base 21.6/22.3/21.6/22.6/21.4, new 3.3/3.2/3.2/3.2/3.2.
- Why filter-before-hostility is safe: hostility only removes candidates, so the order of the two filters cannot change the result; the differential test (old scan vs index, 24 random states x 2 caps + radius fallback) proves the tuple identical.
