# Compliance IDs: WORLD-032, WORLD-033, WORLD-034
from __future__ import annotations
import math
from dataclasses import replace
from typing import List, Optional, TYPE_CHECKING
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
    
    @staticmethod
    def check_for_raid(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
        """
        Checks if the global (non-camp) tick-cadence raid should spawn and returns the update.

        TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX: this method's own gate/output are unchanged --
        it delegates to spawn_raid() with the same (0,0)-anchored origin/target it always used,
        so this caller's behavior is byte-identical to before the extraction. The camp-triggered
        raid path (src/world/camp.py) calls spawn_raid() directly with a real origin/target and
        its own (different) cadence gate, since this method's tick%raid_interval_ticks check does
        not apply to that call site.
        """
        raid_interval_ticks = RaidService.RAID_INTERVAL_DAYS * RaidService.TICKS_PER_DAY
        if state.tick % raid_interval_ticks != 0 or state.tick == 0:
            return StateUpdate()

        raid_size = RaidService.RAID_BASE_SIZE + state.maturity
        return RaidService.spawn_raid(state, generator, origin=(0, 0), target=(0, 0), raid_size=raid_size)

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
