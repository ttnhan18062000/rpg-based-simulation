---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX
artifact_type: investigation
tags: [world, content]
---

# Investigation — TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX

## Current Behavior

### `CampService.process_camps()`'s raid-trigger branch discards its own computed raiders

`src/world/camp.py:102-118`:

```python
else:
    # Trigger a raid from this camp!
    from src.world.raid import RaidService
    # For now, we reuse RaidService logic but anchored here
    raid_update = RaidService.check_for_raid(state, generator)
    # Adjust positions to camp
    for mob in raid_update.entities_add:
        # We can't easily mutate the update list, so we just add them
        # but in a real system we'd pass the origin.
        # For now, let's just mark the last_raid_tick.
        pass

    camp_updates[c_id] = CampUpdate(
        id=c_id,
        maturity_delta=-20.0, # Cost of raiding
        last_raid_tick_set=state.tick
    )
```

`raid_update.entities_add` is computed by `RaidService.check_for_raid()` but never appended to
`process_camps()`'s own returned `entities_add` list (line 30, 151) — the `for mob in
raid_update.entities_add: ... pass` loop is a self-documented no-op stub. `camp_updates[c_id]`
still unconditionally applies the `-20.0` maturity cost and resets `last_raid_tick`. Confirmed via
a real 510-tick `Kernel.tick_once()` run against `data/worlds/camp_maturity_calibration_pilot/`
during `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE`: camp maturity drops by 20 at the expected
tick, no raider entity appears in `state.entities`.

### Second, independent blocker: `check_for_raid()`'s own internal cadence gate almost never aligns with the camp-triggered call's own cadence

`src/world/raid.py:24-31`:

```python
RAID_INTERVAL_DAYS = 5
TICKS_PER_DAY = 100
...
@staticmethod
def check_for_raid(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
    raid_interval_ticks = RaidService.RAID_INTERVAL_DAYS * RaidService.TICKS_PER_DAY  # = 500
    if state.tick % raid_interval_ticks != 0 or state.tick == 0:
        return StateUpdate()
    ...
```

`check_for_raid()` is gated on `state.tick % 500 == 0` — an absolute, global tick-cadence check
independent of any camp state. The camp-triggered call site (`camp.py:81-83`) is gated on a
DIFFERENT condition: `camp.maturity >= 80` AND `state.tick - camp.last_raid_tick >= 500`. These two
gates are not the same and there is no guarantee they align. Confirmed by direct reasoning from the
code (not yet re-run against a real long simulation, see Test Plan): once a camp becomes eligible
(`maturity>=80`, cooldown elapsed), it calls `check_for_raid()` on that exact tick — but unless that
tick happens to also be an exact multiple of 500, `check_for_raid()`'s own gate returns an empty
`StateUpdate()` regardless of the discard-bug fix. A camp reaching eligibility on, say, tick 1347
would get zero raiders from this call even after `entities_add` is correctly threaded through,
because `1347 % 500 != 0`.

**This means fixing only the discard bug (thread `raid_update.entities_add` into the return value)
would pass a narrow unit test calling `process_camps()` at a hand-picked `state.tick` that happens
to be a multiple of 500, but would fail in the overwhelming majority of real ticks a camp actually
becomes raid-eligible on.** This is a real, separate defect from the discard bug, not a restatement
of it.

### Raiders' hardcoded destination

`src/world/raid.py:60-64`:

```python
# Raiders target the town (0,0)
mob = replace(
    mob,
    navigation=replace(mob.navigation, target=(0, 0))
)
```

Every raider unconditionally gets `navigation.target=(0, 0)`, regardless of where the raid actually
spawned. This predates the Region/Place rebuild (`docs/mechanics/05_world_evolution.md` §6) and the
Campaign-mode `state.regions`/`.places` population fix (`TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY`,
landed PR #148) — at the time this code was written, worlds may have had no addressable
"settlement" concept beyond an assumed origin-anchored town. That assumption no longer holds: real
compiled worlds now have `state.places` populated with `PlaceKind.CITY`-kind entries representing
actual settlements (confirmed via `src/core/state.py:332-338`; `PlaceKind.CITY` is the only
settlement-equivalent kind — `CAMP`/`NEST`/`LAIR`/`RUIN`/`DUNGEON`/`LANDMARK` are the others).

Confirmed via the real calibration world built for the prior ticket
(`data/worlds/camp_maturity_calibration_pilot/resolved/world.resolved.yaml`): it has exactly one
`kind: CITY` place alongside its `CAMP` and `NEST` places — a real, ready-made test bed for
"nearest settlement" targeting that did not exist when `raid.py`'s `(0,0)` anchor was written.

No existing "nearest X" spatial-lookup helper was found reusable for this
(`grep -rn "nearest_settlement\|find_nearest\|closest_place" src/` returns only
`PositioningService.find_nearest_cover` in `src/engine/tactical.py`, which is combat-cover-specific
and not reusable here). A straightforward `min()` over `state.places.values()` filtered to
`kind == PlaceKind.CITY` by squared Euclidean distance from the raid's origin is the natural
approach, matching the distance-comparison pattern already used elsewhere in this file
(`camp.py`'s own `mobs_near` filter, `dist_sq` patterns in `combat_engagement/phase.py`).

### Doc/code mismatch on raid sizing (found during investigation, not part of the ticket's original filing)

`docs/world/raid_boss_camp_contract.md` §"Raid composition" states:

> `raid_size = 3 + camp.maturity` (integer — high-maturity camps send larger raids)

But the actual code (`raid.py:34`):

```python
raid_size = RaidService.RAID_BASE_SIZE + state.maturity
```

uses `state.maturity` — the single global world-maturity counter (`WorldCompiler`/`CalamityService`
level, not per-camp), which per `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN`'s own finding
requires ~50,000 ticks via a periodic counter to move meaningfully off its starting value. In any
practical simulation run today, `state.maturity` stays near 0, so `raid_size` is effectively always
`3 + 0 = 3` regardless of camp maturity — contradicting the doc's stated intent that high-maturity
camps send larger raids. This affects BOTH the global tick-cadence raid path and (once fixed) the
camp-triggered path equally, since both call the same `check_for_raid()` sizing logic today.
Whether to fix this as part of the present ticket (camp-triggered path uses `camp.maturity` instead)
or treat it as a separate, smaller doc-correction ticket is an open design question — see Plan.

## Related Precedent

- `TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY` (PR #148, merged `cb0b23b0`): the fix that made
  `state.places` reliably populated in Campaign mode specifically. Non-Campaign (standard
  single-episode) worlds already had `state.places` populated via the ordinary
  `WorldCompiler.compile()` path — that bug was Campaign-mode-orchestrator-specific, not a general
  gap. This ticket's target-selection fix benefits from, but does not depend on, that landed fix.
- `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE` (done): built `camp_maturity_calibration_pilot`,
  the world used to originally discover this bug and the natural test bed for this fix (has CAMP,
  NEST, and CITY places together).
- `docs/world/raid_boss_camp_contract.md` §"Known gap" and §"Extension rules" item 2 both already
  flag the `(0,0)` anchor as a known, documented gap predating this ticket.

## Open Questions for Plan

1. **Fallback when no `PlaceKind.CITY` place exists in `state.places`.** Not every real or test
   world is guaranteed to have a CITY place. Options: (a) skip the raid entirely that tick (no
   raiders spawned, camp keeps its maturity cost/cooldown reset as today — a raid that finds no
   target simply doesn't happen), (b) fall back to the old `(0,0)` behavior as a last resort. Routed
   to peer review before deciding — see Implementation Notes once resolved.
2. **`raid_size` sourcing for the camp-triggered path.** Use `camp.maturity` (matching the doc,
   diverging from the global path) or keep both paths uniform on `state.maturity` (matching current
   code, leaving the doc/code mismatch to a separate ticket)? Routed to peer review.
3. **Whether to refactor `check_for_raid()`'s own signature or add a parallel method.** Given
   Out of Scope excludes changing the global (non-camp) raid path's own observable behavior, the
   cleanest shape is extracting composition logic (spawn N raiders at an origin, target a
   destination) into a new method with no baked-in cadence gate, called by both
   `check_for_raid()` (after its own gate passes, preserving today's behavior for the global caller)
   and the camp-triggered site directly (bypassing that gate, since the camp's own cadence already
   governs eligibility).
