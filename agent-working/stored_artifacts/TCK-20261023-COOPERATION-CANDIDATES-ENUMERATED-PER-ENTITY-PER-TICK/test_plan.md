---
status: historical
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

## Proof Plan
- level: unit differential plus whole-run neutrality
- proof kind: differential (old scan vs index), canonical-hash equality, paired neutral run
- oracle source: the verbatim pre-change scan kept in the test; base commit 6c1373951 hashes
- expected effect: identical candidate tuples and identical hashes; lower cooperation phase cost
- selected commands: pytest tests/unit/domains/cooperation; hash_run x3 worlds; python -m tools.rpg_measure.paired --neutral; tools/perf/profile_tick.py --contract pinned
