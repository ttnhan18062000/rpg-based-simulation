from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

from src.core.models.strategy import CandidateZoneRecord, ObjectiveRecord
from src.core.models.vectors import Vector2
from src.core.models.enums import Domain

if TYPE_CHECKING:
    from src.ai.states.base import AIContext

class SearchNarrowingService:
    """Handles the narrowing of search spaces and hypothesis verification. [phase_3_task_8]
    
    Ensures that searching is a dynamic process of elimination rather than a 
    single-point visit.
    """

    @staticmethod
    def update_search_history(ctx: AIContext) -> StrategicUpdate | None:
        """Tracks the current position as 'visited' in active candidate zones."""
        from src.actions.base import StrategicUpdate
        actor, snapshot = ctx.actor, ctx.snapshot
        pos_tuple = (actor.spatial.pos.x, actor.spatial.pos.y)
        
        # Find candidate zones relevant to the current region
        relevant_zones = []
        for zone in actor.mind.strategic.candidate_zones:
            # If the actor is in the region tied to this zone
            if zone.region_id == actor.spatial.current_region_id:
                if pos_tuple not in zone.visited_tiles:
                    # Narrowing: The more tiles we visit, the higher our contradiction potential 
                    # if the target isn't here.
                    new_zone = zone.model_copy(update={
                        "visited_tiles": zone.visited_tiles + [pos_tuple],
                        "last_search_tick": snapshot.tick
                    })
                    relevant_zones.append(new_zone)
        
        if relevant_zones:
            return StrategicUpdate(
                target_id=actor.id,
                candidate_zones_add_or_update=relevant_zones
            )
        return None

    @staticmethod
    def select_next_search_tile(ctx: AIContext, zone_id: str) -> Vector2 | None:
        """Suggests a new search target within a candidate zone that hasn't been visited."""
        actor, snapshot = ctx.actor, ctx.snapshot
        zone = next((z for z in actor.mind.strategic.candidate_zones if z.zone_id == zone_id), None)
        if not zone:
            return None
            
        # Optimization: Use existing frontier logic but potentially bias it
        from src.ai.perception import Perception
        rng_val = ctx.rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 999)
        
        # Find a frontier tile
        target = Perception.find_frontier_target(actor, snapshot, rng_val)
        
        # Only return if it's in the same region (to keep search localized)
        if target:
             from src.core.world.regions import find_region_at
             reg = find_region_at(target, snapshot.regions)
             if reg and reg.region_id == zone.region_id:
                  return target
                  
        return None
