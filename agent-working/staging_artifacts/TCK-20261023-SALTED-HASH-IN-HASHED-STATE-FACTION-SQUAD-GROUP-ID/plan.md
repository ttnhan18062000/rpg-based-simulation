---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID
artifact_type: plan
tags: []
---

# Plan

1. One helper `stable_int31(*parts)` (blake2b of a canonical encoding of the parts, first 8 bytes, modulo 2**31) in `src/core/` next to other id helpers; `military_conflict.py:339` uses it with `(contested_region_id, attacker_id, state.tick)`. `perception/filter.py:88,97` use it for non-int ids (latent hazard, no live effect).
2. Test (no simulation world): build a state with two factions at WAR, a defender region and 3 GUARD entities; run `MilitaryConflictPhase.execute` plus apply in subprocesses with `PYTHONHASHSEED=0` and `1`; assert equal squad `group_id` and equal `CanonicalStateHasher` hash. Plus a unit test that the digest is stable across calls and distinct for distinct tuples. If the owner wants an end-to-end world, add a `mechanic_scenario_*` world instead (declared as a test scenario).
3. Hash impact: the gate worlds and the four probed worlds form no squad in 5000 ticks, so their hashes and trajectories are unchanged (A0). Ordering by group_id exists (groups.py:74, :366) so a world that does form a squad may reorder group updates: that world's hash moves and a paired step is needed. None of the shipped worlds is such a world. **Planner ruling 2026-10-26: A0 negative, so F4 is hash-neutral on the gate worlds and has no paired step of its own; `paired --neutral` IDENTICAL is the proof and it lands whenever ready. AC amended to the constructed state.**
4. Verification: scoped tests (military conflict, groups, perception filter); a `--neutral` run on the gate worlds (expected IDENTICAL by A0) after the host is free; no paired step beyond that unless a squad world appears.
