# Compliance IDs: WORLD-032, WORLD-033, WORLD-034
from __future__ import annotations
import math
from dataclasses import replace
from typing import Any, List, Optional, TYPE_CHECKING
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate
from src.core.enums import Faction, Domain
from src.platform.rng import DeterministicRNG

if TYPE_CHECKING:
    from src.systems.world_systems.generator import EntityGenerator

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
    # The camp-triggered path below is UNAFFECTED and is the surviving raid mechanic: it has real
    # provenance (a declared actor, its own origin and maturity gate) per ORG-03 / CAUSE-01.
    # If world-clock raids are ever wanted, they return as a declared feature with a
    # settlement-Place target and no coordinate fallback (PLACE-01: a bare coordinate is not a Place).

    @staticmethod
    def spawn_raid(
        state: AuthoritativeState,
        generator: EntityGenerator,
        origin: tuple,
        target: tuple,
        raid_size: int,
    ) -> StateUpdate:
        """
        Composes `raid_size` raiders anchored around `origin`, all targeting `target`. No cadence
        gate of its own -- callers decide when a raid is eligible to fire.
        """
        # Calculate spawn position at a distance from origin, scattered by angle.
        # Using stateless deterministic RNG.
        rng = DeterministicRNG(state.seed)
        angle = rng.get_float(Domain.CALAMITY, state.tick, 0) * 2 * math.pi
        dist = RaidService.SANCTUARY_RADIUS + 10

        spawn_pos = (
            origin[0] + int(math.cos(angle) * dist),
            origin[1] + int(math.sin(angle) * dist)
        )

        entities_add = []
        for i in range(raid_size):
            # Scatter coordinates in a small grid around the base spawn position to avoid overlap
            ox = spawn_pos[0] + (i % 3) - 1
            oy = spawn_pos[1] + (i // 3) - 1

            # Spawn raid mobs (Tier 3-4 difficulty)
            mob = generator.spawn_monster(
                state=state,
                kind="goblin_raider",
                pos=(ox, oy),
                difficulty_tier=4
            )
            # TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION: a raid mob's
            # target above is a raw navigation assignment with no accompanying strategic project
            # -- nothing marks "this entity is mid-raid" to the goal-scoring system, so any scorer
            # that later assigns this entity a real project (confirmed: GuildNeedScorer, once
            # ENABLE_GUILD_QUEST_GENERATION actually reached a real run for the first time) freely
            # overwrites this navigation.target with its own. Real mob factions elsewhere
            # (frontier_marches' own scout/sentinel/leader) legitimately DO run the generic
            # project/goal system, so gating GuildNeedScorer itself by faction was rejected --
            # it broke that live, intended behavior instead of fixing this one. A raid mob's own
            # entire purpose is the raid; it doesn't need or use the project system at all, so
            # max_active_projects=0 is the correct, narrow signal: every capacity-gated scorer
            # (GuildNeedScorer today, any future one) sees zero spare capacity and no-ops,
            # without touching any scorer's own logic or affecting non-raid monsters.
            mob = replace(
                mob,
                navigation=replace(mob.navigation, target=target),
                strategic=replace(
                    mob.strategic,
                    profile=replace(mob.strategic.profile, max_active_projects=0),
                ),
            )
            entities_add.append(mob)

        return StateUpdate(entities_add=entities_add)
