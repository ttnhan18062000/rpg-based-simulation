---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES
phase: open
date: 2026-09-14
tags: [world]
---

# TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES

## Title
The one corpus world with a real `LAIR`-kind Place has its own region sitting at exactly `0.0`
`trauma_score` for a full 5000-tick run — no threshold value can open `check_for_lair_spawn()`'s
gate there, because that region records zero combat deaths at all, not because the threshold is
still too high

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Found while proving `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`'s gate-reachability
fix end to end. That ticket lowered `BossService.BOSS_SPAWN_THRESHOLD` (`50.0` → `2.0`) and added
`BossService.BOSS_SPAWN_TRAUMA_THRESHOLD` (`20.0` → `8.0`), and proved via a real 3000-tick run that
a `world_boss` now spawns correctly (`check_for_boss_spawn()`, region-scoped).

The sibling mechanism, `check_for_lair_spawn()` (place-scoped, spawns `dragonkin`), shares the
identical gate but was **not** proven reachable. `generated_frontier_3_42` is the only corpus world
found with a real `LAIR`-kind Place (`moon_cave_lair`, in region `moon_cave`). A real 5000-tick
`Kernel.tick_once()` run against that world found `moon_cave`'s own `region.trauma_score` at exactly
`0.0` for the entire run — no death was ever recorded in that region. `trauma_score` accrues `+1.0`
per real entity death in that death's own region (`src/engine/world_dynamics.py`'s "Death-triggered
Trauma" block); if zero deaths occur in `moon_cave` across 5000 real ticks, no threshold value —
however low — can open the gate there, short of `0.0` itself (which would defeat the point of a
"some danger has happened here" gate).

This is a different, region-specific defect from the one the sibling ticket fixed: not a wrong
number, but a region that structurally never accumulates the stat the gate checks. Likely cause:
`moon_cave` is a remote/magical region (per its own `RegionDef` framing in
`data/content/world/runtime_regions.yaml`, kind `("magical",)`) that entities rarely or never path
into for combat — but this is not confirmed, only hypothesized.

## Scope
- Confirm directly why `moon_cave` records zero deaths across a real run — check whether entities
  (heroes, monsters) ever path into or spawn within that region at all, whether its own hazard/
  monster-density configuration is simply too low to ever produce combat, or whether there's a
  separate routing/pathing defect keeping entities out of it entirely.
- Check whether other LAIR-kind Places in other worlds (if any get added later, or if this repo's
  world corpus grows) would have the same problem — is this specific to `moon_cave`, or does it
  reveal a general pattern that LAIR-kind Places tend to sit in low-combat regions by design
  (defeating their own occupant-spawn gate)?
- Propose a real fix: could be region content authoring (more monster density/hazard near lairs),
  a different trigger stat for Lair-occupant spawning specifically (not the same region-wide
  `trauma_score` a world boss's gate uses), or something else — bring findings + options to
  peer/user review before implementing, matching this week's established pattern for reachability
  defects.

## Out of Scope
- The world-boss side of the gate (`check_for_boss_spawn()`) — already fixed and proven reachable
  in the sibling ticket; this ticket is specifically about the Lair-occupant path.
- Any change to `BOSS_SPAWN_THRESHOLD`/`BOSS_SPAWN_TRAUMA_THRESHOLD` themselves — already resolved
  by the sibling ticket; this is about a region-specific trauma-accrual gap, not the threshold
  values.

## Acceptance Criteria
- [ ] A real, evidence-backed explanation for why `moon_cave` (or LAIR regions generally) never
      accumulate trauma_score.
- [ ] A proposed fix (not yet built without review) that would make at least one real LAIR-kind
      Place's occupant demonstrably spawnable within a realistic run length.
- [ ] Findings brought to peer/user review before implementation.

## Related Tickets
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (fixed the shared gate's threshold
  values and the tier-5/loot defects; this ticket covers the remaining region-specific gap)

## Related Docs
- `docs/plans/deferred_tuning_decisions_register.md` D-05 (records this as a known remaining gap)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/world/boss.py` (`BossService.check_for_lair_spawn()`)
- `src/engine/world_dynamics.py` (Death-triggered Trauma block, the real `trauma_score` producer)
- `data/content/world/runtime_regions.yaml` (`moon_cave`'s own region definition)
- `data/worlds/generated_frontier_3_42/` (the one corpus world with a real LAIR place)

## Assumptions / Open Questions
- Whether `moon_cave`'s zero-combat state is a content-authoring gap (too little threat placed
  there) or a routing/pathing defect (entities never go there) is the central open question.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
