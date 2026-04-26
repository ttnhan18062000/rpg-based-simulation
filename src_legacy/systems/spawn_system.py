from __future__ import annotations
import math
from dataclasses import replace
from typing import TYPE_CHECKING, List, Dict

if TYPE_CHECKING:
    from src_legacy.core.state import AuthoritativeState
    from src_legacy.core.updates import StateUpdate
    from src_legacy.systems.generator import EntityGenerator

class SpawnSystem:
    """
    Manages deterministic ambient spawning in regions.
    Law: Every region must maintain a population relative to its kind and stability.
    """

    SPAWN_INTERVAL = 100 # Check spawning every 100 ticks
    MAX_ENTITIES_PER_REGION = 10
    
    @staticmethod
    def resolve_ambient_spawns(state: AuthoritativeState, update: StateUpdate, generator: EntityGenerator) -> StateUpdate:
        """
        Check regional population and spawn entities if below target.
        """
        if state.tick % SpawnSystem.SPAWN_INTERVAL != 0:
            return update
            
        entities_add = list(update.entities_add)
        
        # 1. Map entities to regions
        from src_legacy.engine.legality import LegalityServiceV2
        region_counts: Dict[str, int] = {r_id: 0 for r_id in state.regions}
        
        for entity in state.entities.values():
            if not entity.active: continue
            region = LegalityServiceV2.get_region_for_position(entity.position, state)
            if region:
                region_counts[region.id] += 1
                
        # 2. Check each region
        for r_id, region in state.regions.items():
            count = region_counts[r_id]
            target = SpawnSystem._get_target_population(region, state)
            
            if count < target:
                # Spawn one entity
                new_ent = SpawnSystem._spawn_for_region(region, state, generator)
                if new_ent:
                    entities_add.append(new_ent)
                    
        return replace(update, entities_add=entities_add)

    @staticmethod
    def _get_target_population(region, state: AuthoritativeState) -> int:
        """
        Calculate target population based on region kind and maturity.
        """
        base = 5
        if region.kind == "TOWN":
            base = 8 + state.maturity
        elif region.kind == "FOREST":
            base = 5 + state.maturity // 2
        elif region.kind == "DESERT":
            base = 3
            
        return min(SpawnSystem.MAX_ENTITIES_PER_REGION, base)

    @staticmethod
    def _spawn_for_region(region, state: AuthoritativeState, generator: EntityGenerator):
        """
        Create an entity appropriate for the region.
        """
        from src_legacy.world.spawn_config import DIFFICULTY_ZONES
        
        # Determine tier by distance from center
        dist = math.sqrt(region.center[0]**2 + region.center[1]**2)
        tier = 1
        for threshold, t in DIFFICULTY_ZONES:
            if dist <= threshold:
                tier = t
                break
                
        # Determine kind
        if region.kind == "TOWN":
            if generator.rng.random() > 0.7:
                return generator.spawn_hero(region.center, state, difficulty_tier=tier)
            else:
                return generator.spawn_monster(region.center, state, kind="citizen", difficulty_tier=tier)
        else:
            # Look for camps in this region
            camps = [
                b for b in state.buildings.values() 
                if b.kind == "GOBLIN_CAMP" and 
                region.bounds[0] <= b.position[0] <= region.bounds[2] and
                region.bounds[1] <= b.position[1] <= region.bounds[3]
            ]
            
            if camps:
                camp = generator.rng.choice(camps)
                spawn_pos = (
                    camp.position[0] + generator.rng.uniform(-10, 10),
                    camp.position[1] + generator.rng.uniform(-10, 10)
                )
            else:
                spawn_pos = region.center
                
            return generator.spawn_monster(spawn_pos, state, kind="monster", difficulty_tier=tier)

