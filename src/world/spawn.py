# src/world/spawn.py
from __future__ import annotations
import math
from typing import TYPE_CHECKING, List, Dict
from src.core.updates import StateUpdate
from src.core.enums import Domain, EntityRole

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, RegionState
    from src.systems.generator import EntityGenerator

class SpawnService:
    """
    Handles regional monster replenishment and density management.
    """
    
    SPAWN_INTERVAL = 50 # Ticks between spawn checks
    
    @staticmethod
    def process_spawns(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
        """
        Check regional monster density and spawn new ones if needed.
        """
        if state.tick % SpawnService.SPAWN_INTERVAL != 0:
            return StateUpdate()
            
        from src.world.spawn_config import SPAWN_POOLS, BASE_MONSTER_DENSITY, DIFFICULTY_ZONES
        
        entities_add = []
        
        # 1. Count monsters per region
        region_monster_count: Dict[str, int] = {r_id: 0 for r_id in state.regions}
        for entity in state.entities.values():
            if entity.identity.role == EntityRole.MONSTER and entity.combat.alive:
                # Find region
                from src.engine.legality import LegalityServiceV2
                region = LegalityServiceV2.get_region_for_position(entity.position, state)
                if region and region.id in region_monster_count:
                    region_monster_count[region.id] += 1
        
        # 2. Check density and spawn
        generator._last_id = state.next_entity_id - 1
        for r_id, region in state.regions.items():
            pool = SPAWN_POOLS.get(region.kind, [])
            if not pool:
                continue
                
            # Calculate target count based on area and hazard
            # Simplified: (Width * Height / 10000) * BASE_DENSITY * (1 + hazard)
            xmin, ymin, xmax, ymax = region.bounds
            area = (xmax - xmin) * (ymax - ymin)
            target_count = int((area / 10000.0) * BASE_MONSTER_DENSITY * (1.0 + region.hazard_level))
            target_count = max(2, target_count) # Minimum 2 monsters per active region
            
            current_count = region_monster_count[r_id]
            if current_count < target_count:
                # Spawn one monster this interval
                kind = generator.rng.choice(Domain.SPAWN, state.tick, r_id, pool)
                
                # Get random position in bounds
                rx = generator.rng.get_float(Domain.SPAWN, state.tick, f"x_{r_id}") * (xmax - xmin) + xmin
                ry = generator.rng.get_float(Domain.SPAWN, state.tick, f"y_{r_id}") * (ymax - ymin) + ymin
                
                # Determine difficulty tier based on distance from (0,0)
                dist = math.sqrt(rx**2 + ry**2)
                tier = 1
                for d_limit, d_tier in DIFFICULTY_ZONES:
                    if dist <= d_limit:
                        tier = d_tier
                        break
                
                # Spawn!
                if kind == "goblin":
                    mob = generator.spawn_goblin((rx, ry), state, tier)
                else:
                    mob = generator.spawn_monster((rx, ry), state, kind, tier)
                    
                entities_add.append(mob)
                
        return StateUpdate(
            entities_add=entities_add,
            next_entity_id_set=generator._last_id + 1 if entities_add else None
        )
