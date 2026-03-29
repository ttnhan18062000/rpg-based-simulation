# Enhance 04: Mob Roaming Leash Distance

## Summary

Mobs should not roam too far from their spawn camp/region. Currently, entities in HUNT or WANDER state can chase or drift across the entire map. Popular RPGs use a "leash" mechanic where mobs return to their home area after moving too far.

## Current State

- Mobs have no concept of a "home position" or maximum roaming range
- HUNT state chases targets indefinitely across the map
- WANDER state drifts randomly with no boundary
- This leads to unrealistic behavior: goblins from a camp wandering into town, mobs chasing heroes across 50+ tiles

## Proposed Changes

### Leash Mechanic

1. **Home position** — store `home_x, home_y` on Entity (set at spawn time)
2. **Leash radius** — configurable per entity kind or per spawn camp (e.g., 15 tiles for goblins, 20 for wolves)
3. **Leash enforcement:**
   - During WANDER: if distance from home > leash_radius, switch to RETURN_HOME state
   - During HUNT: if distance from home > leash_radius × 1.5, abandon chase and return home
   - During FLEE: leash is ignored (survival takes priority)
4. **RETURN_HOME state** — new AI state that moves entity back toward home position, then resumes WANDER

### Chase Give-Up

- If a mob has been in HUNT for N ticks (e.g., 20) without closing distance, give up and return
- Prevents infinite chase loops

### Reference

Common in RPGs (WoW, FF14, Diablo): mobs chase for ~8–15 seconds then "reset" and walk back to their patrol area, regenerating HP.

## Affected Code

- `src/core/models.py` — add `home_x`, `home_y`, `leash_radius` to Entity
- `src/ai/states.py` — add RETURN_HOME handler, modify HUNT/WANDER with leash checks
- `src/core/enums.py` — add `RETURN_HOME` to AIState (if not already present)
- `src/systems/generator.py` — set home position at spawn
- `src/config.py` — default leash radius per entity kind

## Notes

> **Decision required from developer:** What leash radius values? Should mobs heal when returning home (like WoW evade reset)? Should heroes also have a leash to the town area?

## Labels

`enhance`, `ai`, `gameplay`, `needs-decision`
