from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING, Dict
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, WorldUpdate
from src.core.enums import Domain

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.systems.generator import EntityGenerator

class CalamityService:
    """
    Manages global world evolution, calamities, and macro threats.
    """
    
    MATURITY_INTERVAL = 1000
    CALAMITY_MIN_INTERVAL = 2000
    CALAMITY_RANDOM_CHANCE = 0.005
    CALAMITY_FORCE_INTERVAL = 5000
    
    @staticmethod
    def process_world_dynamics(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
        """
        Processes maturity, calamity spawns, and regional intensity shifts.
        """
        updates = StateUpdate()
        
        # 1. Maturity Advancement
        if state.tick % CalamityService.MATURITY_INTERVAL == 0 and state.tick > 0:
            updates = updates.replace(maturity_set=state.maturity + 1)
            
        # 2. Calamity Spawn Check
        should_spawn = False
        if state.tick - state.last_calamity_tick >= CalamityService.CALAMITY_MIN_INTERVAL:
            if state.tick % CalamityService.CALAMITY_FORCE_INTERVAL == 0 and state.tick > 0:
                should_spawn = True
            
        if should_spawn:
            # Find high intensity region
            high_intensity_regions = [r for r in state.regions.values() if r.calamity_intensity > 0.3]
            if high_intensity_regions:
                # Sort by intensity
                target_region = max(high_intensity_regions, key=lambda r: r.calamity_intensity)
                
                # Spawn a boss
                boss = generator.spawn_monster(
                    state=state,
                    kind="world_boss",
                    pos=target_region.center,
                    difficulty_tier=4
                )
                
                updates = updates.replace(
                    entities_add=[boss],
                    last_calamity_tick_set=state.tick
                )
            
        return updates

    @staticmethod
    def apply_calamity_consequences(state: AuthoritativeState, recent_deaths: List[EntityState]) -> StateUpdate:
        """
        Increases regional calamity intensity when significant entities die.
        """
        world_updates = {}
        for entity in recent_deaths:
            from src.engine.legality import LegalityServiceV2
            region = LegalityServiceV2.get_region_for_position(entity.position, state)
            if not region:
                continue
                
            # Calamity intensity increases on Hero death in high-hazard regions
            if entity.kind == "hero" and region.hazard_level > 0.5:
                intensity_delta = 0.05
                current_intensity = region.calamity_intensity
                world_updates[region.id] = WorldUpdate(
                    region_id=region.id,
                    calamity_intensity_set=min(1.0, current_intensity + intensity_delta)
                )
                
        return StateUpdate(world_updates=world_updates)
