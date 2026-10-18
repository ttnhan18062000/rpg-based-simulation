# Compliance IDs: WORLD-032, WORLD-033, WORLD-034
from __future__ import annotations

class RaidService:
    """
    Orchestrates faction raids against the town.
    """
    
    RAID_INTERVAL_DAYS = 5
    TICKS_PER_DAY = 100
    RAID_BASE_SIZE = 3
    SANCTUARY_RADIUS = 15
    
    # TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION:
    # `check_for_raid()` -- the global world-clock raid, fired on a tick % 500 cadence -- is
    # RETIRED, not re-anchored. It passed origin=(0,0), target=(0,0) literally, so every raider
    # spawned on the radius-25 ring around the world origin, outside every region, and sat there.
    # Measured over 2 corpus worlds / 4 raid events: 12/12 raiders off-region, and in the world
    # where they never drifted into one, zero raider combat and bit-identical regional influence.
    # It had never once produced a raid.
    #
    # Retiring it is the hard-bug fix (it stops creating regionless, inert entities). Re-anchoring
    # it on a real settlement was implemented, measured, and withdrawn: that would ACTIVATE a
    # behaviour the world has never had, which is a gameplay change with a balance footprint, and
    # `owner_decision_memo.md` row 7 parks feature work. It also would not have worked --
    # `src/engine/tactical.py:141` PANIC_RETREAT overwrites a raider's target with the same
    # hardcoded (0.0, 0.0) within 15-38 ticks of spawn, so the raid is swallowed on the flight path
    # even once the spawn path is correct (TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN).
    #
    # The camp-triggered raid (`spawn_raid`) is retired too (owner ruling D70, TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70): it
    # conjured 3 + maturity raiders at a camp for a maturity cost, with no off-map origin and no existing members. A camp raids again only when a
    # later rule lets its existing members set out together. If raids are ever wanted they return as a declared feature with a
    # settlement-Place target and no coordinate fallback (PLACE-01: a bare coordinate is not a Place).
