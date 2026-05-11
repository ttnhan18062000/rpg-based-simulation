from __future__ import annotations
from dataclasses import replace
from typing import Dict, List, Optional, TYPE_CHECKING
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, WorldUpdate
from src.core.enums import Faction

if TYPE_CHECKING:
    from src.systems.world_systems.generator import EntityGenerator

class FactionInfluenceService:
    """
    Manages regional influence shifts and faction territory control.
    """
    
    DEATH_INFLUENCE_SHIFT = 5.0
    CONQUEST_THRESHOLD = -50.0
    LIBERATION_THRESHOLD = 50.0
    
    @staticmethod
    def process_influence_shift(state: AuthoritativeState, recent_deaths: List[EntityState]) -> StateUpdate:
        """
        Calculates influence deltas based on entity deaths.
        """
        influence_deltas: Dict[str, float] = {}
        
        for entity in recent_deaths:
            from src.engine.legality import LegalityServiceV2
            region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state)
            if not region:
                continue
                
            # Hero death decreases influence (Monster gain)
            if entity.identity.faction == Faction.HERO_GUILD:
                delta = -FactionInfluenceService.DEATH_INFLUENCE_SHIFT
            # Monster death increases influence (Hero gain)
            elif entity.identity.faction == Faction.MONSTER_HORDE:
                delta = FactionInfluenceService.DEATH_INFLUENCE_SHIFT
            else:
                continue
            
            influence_deltas[region.id] = influence_deltas.get(region.id, 0.0) + delta
            
        world_updates = {}
        for r_id, delta in influence_deltas.items():
            region = state.regions[r_id]
            new_influence = max(-100.0, min(100.0, region.influence + delta))
            
            w_upd_args = {"region_id": r_id, "influence_delta": delta}
            
            # Conquest Check
            if region.owner_faction_id is None and new_influence <= FactionInfluenceService.CONQUEST_THRESHOLD:
                w_upd_args["owner_faction_id_set"] = Faction.MONSTER_HORDE
                
            # Liberation Check
            elif region.owner_faction_id == Faction.MONSTER_HORDE and new_influence >= FactionInfluenceService.LIBERATION_THRESHOLD:
                w_upd_args["owner_faction_id_set"] = -1 # Sentinel for None
                
            world_updates[r_id] = WorldUpdate(**w_upd_args)
            
        return StateUpdate(world_updates=world_updates)

    @staticmethod
    def process_conquest_lifecycle(state: AuthoritativeState, update: StateUpdate, generator: EntityGenerator) -> StateUpdate:
        """
        Handles spawning/removing strongholds based on world updates.
        """
        entities_add = []
        entities_remove = []
        
        for r_id, w_upd in update.world_updates.items():
            region = state.regions[r_id]
            
            # 1. New Conquest -> Spawn Stronghold
            if w_upd.owner_faction_id_set == Faction.MONSTER_HORDE:
                # Center of region
                center = (
                    (region.bounds[0] + region.bounds[2]) / 2,
                    (region.bounds[1] + region.bounds[3]) / 2
                )
                stronghold = generator.spawn_stronghold(state, center)
                entities_add.append(stronghold)
                
            # 2. New Liberation -> Remove Stronghold
            elif w_upd.owner_faction_id_set == -1:
                # Find stronghold in this region
                for e_id, entity in state.entities.items():
                    if entity.kind == "stronghold":
                        from src.engine.legality import LegalityServiceV2
                        e_region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state)
                        if e_region and e_region.id == r_id:
                            entities_remove.append(e_id)
                            
        # Also check for stronghold destruction triggering liberation
        # (This would normally happen in a separate pass if we want destruction to BE the trigger)
        
        return update.replace(
            entities_add=list(update.entities_add) + entities_add,
            entities_remove=list(update.entities_remove) + entities_remove
        )
