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

## Landing
**LANDING HOLD (planner correction 2026-10-26):** the landing slot is set by the owner-approved section 12.5 order (step B, step A, F4, D73). Code F4 and run the neutral proof as planned, but HOLD the PR until after step A, unless the owner rules to move it earlier (rpg-planner is asking).

**LANDING HOLD LIFTED (owner ruling, #715 issuecomment-6412087297, memo row 90, relayed by rpg-planner):** F4 lands as soon as it is ready. Opening the PR still needs the user's own yes.
**PR body requirement (lead-planner-u24):** the gate-world `--neutral` IDENTICAL only shows those worlds do not exercise F4; it is NOT behaviour coverage, and the PR body must say so in those words. The behaviour evidence is the constructed-WAR-state test, where a squad actually forms: it must check the F4 path (stable_int31 used for group_id) and run twice per hashseed, so it is also deterministic within a seed.

**OWNER RULING NOW CONDITIONAL (#715 6412199242, memo row 90 reworded; relayed by rpg-planner):** probe A0 was seed 42 only and `--neutral` is 3 worlds x seed 42 x 1000t, so neither covers the gate seeds 42-46. REQUIRED before any early landing: extend probe A0 to crowded_frontier, frontier_living_world, urban_political x seeds 43-46 x 5000t, checking every tick for a WAR pair or a FACTION_SQUAD group (probe: `/mnt/data/scratch-rpg-implementer-2/f4/probe_a0.py world seed ticks out.json`, PYTHONHASHSEED=0, from the f4 worktree; needs a host slot from rpg-planner, one process at a time). If none forms anywhere: F4 lands when ready with the neutral proof plus the constructed-state test. If any (world, seed) forms a squad: F4 waits until after step A and takes its own paired step against its parent. The PR body states exactly what was measured (worlds, seeds, ticks, hashseed), never "no world forms a squad".
