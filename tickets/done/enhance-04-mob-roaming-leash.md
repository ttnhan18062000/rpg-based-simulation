---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: enhance-04-mob-roaming-leash
phase: done
date: unknown
tags: [enhance, mob, roaming, leash]
---

# Enhance 04: Mob Roaming Leash Distance

## Summary
Mobs should not roam too far from their spawn camp/region. Currently, entities in HUNT or WANDER state can chase or drift across the entire map. Popular RPGs use a "leash" mechanic where mobs return to their home area after moving too far.

## Current State
- Mobs have no concept of a "home position" or maximum roaming range
- HUNT state chases targets indefinitely across the map
- WANDER state drifts randomly with no boundary
- This leads to unrealistic behavior: goblins from a camp wandering into town, mobs chasing heroes across 50+ tiles

## Status
DONE

## Final Status
**DONE**: Implemented the Leash mechanic including `home_pos` on Entity and `mob_leash_radius` in `config.py`. Added `beyond_leash` utility in `src/ai/states/base.py` and integrated leash checks into `HUNT` and `WANDER` states in `src/ai/states/combat.py`. Mobs now correctly return home and heal when the leash is exceeded.

**Tier:** standard
**Type:** chore
**Priority:** P1
