from typing import TYPE_CHECKING
from src_legacy.api.schemas import SchedulerTimelineItemSchema

if TYPE_CHECKING:
    from src_legacy.core.models.world_state import WorldState

class SchedulerPresenter:
    """Provides a deterministic view of the upcoming simulation sequence."""

    @staticmethod
    def get_timeline(world: "WorldState", limit: int = 20) -> list[SchedulerTimelineItemSchema]:
        current_tick = world.tick
        entities = list(world.entities.values())
        
        # Sort by next_act_at (lowest first) then by ID for tie-breaking
        entities.sort(key=lambda e: (e.next_act_at, e.id))
        
        timeline = []
        for e in entities[:limit]:
            wait_ticks = max(0, int(e.next_act_at - current_tick))
            
            # Estimate action type (if available in decision state)
            action_type = "unknown"
            if e.mind.decision.ai_state.name:
                action_type = e.mind.decision.ai_state.name.lower()

            timeline.append(SchedulerTimelineItemSchema(
                entity_id=e.id,
                display_name=e.identity.display_name or f"Entity #{e.id}",
                next_act_tick=int(e.next_act_at),
                wait_ticks=wait_ticks,
                action_type=action_type
            ))
            
        return timeline
