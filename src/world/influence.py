from __future__ import annotations
from dataclasses import replace
from typing import Dict, List, Optional
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, WorldUpdate, NO_OWNER_SENTINEL
from src.core.enums import Faction
from src.content_semantics.faction import get_faction_id_str, get_faction_semantics_service


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
                w_upd_args["owner_faction_id_set"] = NO_OWNER_SENTINEL

            world_updates[r_id] = WorldUpdate(**w_upd_args)
            
        return StateUpdate(world_updates=world_updates)
