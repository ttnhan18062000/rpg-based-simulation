from __future__ import annotations
from typing import Dict, Any, List, Optional
from src.core.state import EntityState, AuthoritativeState
from src.core.updates import SocialUpdate

class SocialMemoryService:
    """
    Handles updates to persistent social and environmental memory.
    Domain 4 Hardening.
    """

    @staticmethod
    def tick_place_attachment(entity: EntityState, state: AuthoritativeState) -> Optional[SocialUpdate]:
        """
        Increments attachment to the current region based on presence.
        PH4 Law: Long-term presence creates 'Home' attachment.
        """
        # Find current region
        region_id = None
        ex, ey = entity.navigation.position
        for rid, region in state.regions.items():
            xmin, ymin, xmax, ymax = region.bounds
            if xmin <= ex <= xmax and ymin <= ey <= ymax:
                region_id = rid
                break
        
        if not region_id:
            return None
            
        # Passive increment: 0.001 per tick while in region
        # This means 1000 ticks (approx 10-15 mins of sim) gives 1.0 attachment.
        return SocialUpdate(place_attachment_delta={region_id: 0.001})

    @staticmethod
    def check_nemesis_promotion(entity: EntityState) -> Optional[SocialUpdate]:
        """
        Promotes enemies from grudge_history to nemesis_ids if hostility threshold met.
        PH4 Law: Significant history of harm creates a 'Nemesis'.
        """
        nemesis_to_add = []
        # Threshold: 3.0 grudge (e.g. 3 kills or heavy repeated harassment)
        for eid, grudge in entity.social.grudge_history.items():
            if eid not in entity.social.nemesis_ids and grudge >= 3.0:
                nemesis_to_add.append(eid)
        
        if not nemesis_to_add:
            return None
            
        return SocialUpdate(nemesis_promotion=nemesis_to_add)
