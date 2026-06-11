from __future__ import annotations
from dataclasses import replace
from typing import Dict, List, Optional, TYPE_CHECKING
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, WorldUpdate
from src.core.enums import Faction
from src.content_semantics.faction import get_faction_id_str, get_faction_semantics_service

if TYPE_CHECKING:
    from src.systems.world_systems.generator import EntityGenerator


def _region_owner_faction_id_str(owner_int: Optional[int]) -> Optional[str]:
    """Convert stored Optional[int] region owner to faction_id string for semantics checks."""
    if owner_int is None:
        return None
    try:
        return Faction(owner_int).name.lower()
    except (ValueError, TypeError):
        return None


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
        semantics = get_faction_semantics_service()

        for entity in recent_deaths:
            from src.engine.legality import LegalityServiceV2
            region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state)
            if not region:
                continue

            faction_id = get_faction_id_str(entity)
            if semantics.is_protector(faction_id):
                delta = -FactionInfluenceService.DEATH_INFLUENCE_SHIFT
            elif semantics.is_invader(faction_id):
                delta = FactionInfluenceService.DEATH_INFLUENCE_SHIFT
            else:
                continue

            influence_deltas[region.id] = influence_deltas.get(region.id, 0.0) + delta
            
        world_updates = {}
        for r_id, delta in influence_deltas.items():
            region = state.regions[r_id]
            new_influence = max(-100.0, min(100.0, region.influence + delta))
            owner_fid = _region_owner_faction_id_str(region.owner_faction_id)

            w_upd_args = {"region_id": r_id, "influence_delta": delta}

            # Conquest Check
            if region.owner_faction_id is None and new_influence <= FactionInfluenceService.CONQUEST_THRESHOLD:
                w_upd_args["owner_faction_id_set"] = Faction.MONSTER_HORDE

            # Liberation Check
            elif owner_fid is not None and semantics.is_invader(owner_fid) and new_influence >= FactionInfluenceService.LIBERATION_THRESHOLD:
                w_upd_args["owner_faction_id_set"] = -1  # Sentinel for None

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
