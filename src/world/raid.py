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
        Checks if a raid should spawn and returns the update.
        """
        raid_interval_ticks = RaidService.RAID_INTERVAL_DAYS * RaidService.TICKS_PER_DAY
        if state.tick % raid_interval_ticks != 0 or state.tick == 0:
            return StateUpdate()
            
        # Raid size scales with maturity
        raid_size = RaidService.RAID_BASE_SIZE + state.maturity
        
        # Calculate spawn position far from town center (0,0)
        # Using stateless deterministic RNG
        rng = DeterministicRNG(state.seed)
        angle = rng.get_float(Domain.CALAMITY, state.tick, 0) * 2 * math.pi
        dist = RaidService.SANCTUARY_RADIUS + 10
        
        spawn_pos = (
            int(math.cos(angle) * dist),
            int(math.sin(angle) * dist)
        )
        
        entities_add = []
        for i in range(raid_size):
            # Spawn raid mobs (Tier 3-4 difficulty)
            mob = generator.spawn_monster(
                state=state,
                kind="goblin_raider",
                pos=spawn_pos,
                difficulty_tier=4
            )
            # Raiders target the town (0,0)
            mob = replace(
                mob,
                navigation=replace(mob.navigation, target=(0, 0))
            )
            entities_add.append(mob)
            
        return StateUpdate(entities_add=entities_add)
