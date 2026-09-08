---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX
phase: open
date: 2026-09-08
tags: [world, content]
---

# TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX

## Title
CampService.process_camps()'s raid branch discards its own computed raiders — camps drain maturity for a raid that never spawns

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE`'s follow-up pass. `CampService.
process_camps()`'s raid-reuse code (`src/world/camp.py`, the `else:` branch under "Trigger a raid
from this camp!") calls `RaidService.check_for_raid(state, generator)` and receives a real
`raid_update` with computed raider entities in `raid_update.entities_add` — but a pre-existing,
self-documented incomplete stub then discards them:

```python
for mob in raid_update.entities_add:
    # We can't easily mutate the update list, so we just add them
    # but in a real system we'd pass the origin.
    # For now, let's just mark the last_raid_tick.
    pass
```

`camp_updates[c_id]` still unconditionally gets `maturity_delta=-20.0, last_raid_tick_set=state.tick`
— the internal bookkeeping proceeds exactly as if a raid happened, but **zero raiders are ever
actually spawned by this code path**, regardless of maturity or timing. Confirmed real via a
510-tick `Kernel.tick_once()` run against a dedicated calibration world
(`data/worlds/camp_maturity_calibration_pilot/`): both camps' maturity dropped by the raid cost at
the expected tick with no corresponding raider entity appearing anywhere in `state.entities`.

Separately, this camp-triggered call is *also* gated a second time by `RaidService.
check_for_raid()`'s own independent `state.tick % raid_interval_ticks == 0` condition
(`raid_interval_ticks = 500`, the same constant `src/engine/world_dynamics.py`'s own unrelated,
global, camp-agnostic periodic raid trigger uses) — a second, narrower compounding gate even once
the discard bug is fixed.

**User-visible symptom**: camps are silently charged a real maturity cost for a raid that never
occurs — draining camp maturity for zero gameplay effect, not just inert dead code.

## Scope
- Fix the raid-reuse code so `raid_update.entities_add`'s computed raiders are actually appended to
  `process_camps()`'s own returned `entities_add`, positioned/anchored at the triggering camp (per
  the existing comment's own stated intent — "in a real system we'd pass the origin").
- This likely needs `RaidService.check_for_raid()`'s own signature or return contract extended to
  accept/apply a real origin — investigate the minimal real change, not a rewrite of `RaidService`'s
  own targeting logic.
- Confirm the second compounding gate (`raid_interval_ticks` alignment) is intentional or also worth
  addressing in the same ticket — a real call to make during Investigate, not assumed here.
- Prove the fix with a real simulation run: a camp-triggered raid actually produces visible raider
  entities in `state.entities`, not just correct maturity bookkeeping.

## Out of Scope
- `RaidService`'s own global (non-camp) raid-trigger path (`src/engine/world_dynamics.py`) — already
  confirmed working correctly, not part of this bug.
- Any change to raid difficulty/reward balance — this ticket only makes the existing raid actually
  spawn, not tune it.
- The Camp/Nest/Lair content-authoring gap this bug was found alongside — already closed by
  `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE`.

## Acceptance Criteria
- [ ] A camp-triggered raid actually spawns real raider entities in `state.entities`, confirmed via
      a real simulation run (not a hand-constructed unit test alone).
- [ ] Camp maturity cost (`-20.0`) and `last_raid_tick_set` bookkeeping remain correct and only apply
      when a raid genuinely occurs.
- [ ] No regression in existing camp/raid test suites.

## Related Tickets
- `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE` (`tickets/done/` — found this bug during its own
  follow-up pass)

## Related Docs
- `docs/world/raid_boss_camp_contract.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/world/camp.py` (`CampService.process_camps()`)
- `src/world/raid.py` (`RaidService.check_for_raid()`)

## Assumptions / Open Questions
- Whether `RaidService.check_for_raid()`'s own signature should change to accept an origin
  parameter, or whether the fix belongs entirely in `camp.py`'s own post-processing of the returned
  update, is a real design call for this ticket's own Investigate/Plan phases — not resolved here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
