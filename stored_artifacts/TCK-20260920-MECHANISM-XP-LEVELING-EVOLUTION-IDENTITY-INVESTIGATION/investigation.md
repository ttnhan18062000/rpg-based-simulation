---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-XP-LEVELING-EVOLUTION-IDENTITY-INVESTIGATION
phase: done
date: 2026-09-20
tags: [architecture, schema]
---

# Investigation — TCK-20260920-MECHANISM-XP-LEVELING-EVOLUTION-IDENTITY-INVESTIGATION

## `EvolutionSystem.evaluate()`'s own real structure

Direct read of `src/engine/evolution.py::EvolutionSystem.evaluate()` found two structurally
distinct behaviors in one undivided pass:
1. **Level-up chain**: consolidate XP (with well-rested multiplier), evaluate threshold crossing via
   `LevelingService.get_xp_required()`, and on any `levels_gained > 0` grant stat/AP/skill growth
   (HERO: unspent AP + `LevelingService.get_unlocked_skills()`; non-HERO: vitality/strength/
   endurance attribute deltas). This is `xp_leveling`'s own registry claim.
2. **Species-kind transformation**: on `levels_gained > 0`, additionally check
   `old_level < threshold <= new_level` for `threshold in (10, 25, 50)` — only there does it call
   `_get_evolved_kind()` (changing `entity.kind`) and upgrade equipment slots. This is what
   `evolution`'s own name most naturally implies.

## What `evolution`'s own evidence actually tests

Its cited positive control: a goblin at `evolution_points=95`, level 1, crosses to level 2. This
never approaches threshold 10 — `evolved` is `False` for the entire scenario. The evidence tests
behavior (1) above, not behavior (2). `evolution`'s own name and its own supporting evidence
currently point at different things.

## Applying the identity rule's Merge test

§1's own test: "if two declared ids share one implementation and cannot independently succeed or
fail, they are one mechanism." Behavior (2) structurally requires behavior (1) to have already
fired repeatedly (crossing 10 levels requires crossing every level below it first). Real corpus
data (already measured in `xp_leveling`'s own entry): max 50 XP accumulated against a 100-XP
threshold in any tested world, zero entities crossing even one level in the busiest case. Level 10
is further from real corpus reach than level 2 already is. No evidence from either entry shows
behaviors (1) and (2) able to succeed/fail independently of each other in any tested world.

## Verdict

**Merge**, `xp_leveling` into `evolution`. Recorded in
`docs/plans/mechanism_identity_and_change_taxonomy.md` §8 and on `xp_leveling`'s own registry entry.
Not executed — deferred to review, matching this session's own established restraint for structural
registry changes regardless of which direction the evidence points.
