"""Strategic Event Interpreter — bridges narrative memory to strategic reprioritization. [PHASE 5]"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Optional

from src.actions.base import StrategicUpdate
from src.core.models.enums import InterpretedLifeEventKind
from src.core.models.life_events import InterpretedLifeEvent
from src.core.logic.strategic_consequence_service import StrategicConsequenceService

if TYPE_CHECKING:
    from src.ai.states import AIContext

logger = logging.getLogger(__name__)

class StrategicEventInterpreter:
    """Reflective service that evaluates recent narrative events for strategic meaning.
    
    This ensures that events which have social or emotional impact also 
    trigger the necessary strategic shifts (concerns, project suspensions, etc.).
    """

    @classmethod
    def interpret_recent_memory(cls, ctx: AIContext, updates: StrategicUpdate) -> None:
        """Scan narrative history for events since the last strategic interpretation."""
        actor = ctx.actor
        strat = actor.mind.strategic
        last_tick = strat.last_interpreted_event_tick
        
        # 1. Filter new events
        new_events = [m for m in actor.mind.narrative.memory_log if m.tick > last_tick]
        if not new_events:
            return

        # 1b. Find new turning points
        new_tps = {tp.event_id: tp for tp in actor.mind.narrative.turning_points if tp.tick > last_tick}

        for entry in new_events:
            # Skip if no semantic kind (e.g. generic discovery notes with low impact)
            if entry.life_event_kind is None and entry.impact < 5.0:
                continue
            
            # Reconstruct/Map to InterpretedLifeEvent
            kind = InterpretedLifeEventKind(entry.life_event_kind) if entry.life_event_kind is not None else InterpretedLifeEventKind.NEAR_DEATH
            
            # Map Narrative Details back to flat dict for Strategic logic
            # Narrative details might be CombatNarrative, social, etc. 
            details_dict = entry.details.model_dump() if hasattr(entry.details, "model_dump") else entry.details
            
            virtual_event = InterpretedLifeEvent(
                event_id=getattr(entry, 'event_id', f"ref-{entry.tick}-{entry.type}"), # Use ID if present
                kind=kind,
                tick=entry.tick,
                actor_id=actor.id,
                severity=entry.impact,
                location=actor.spatial.pos, # Fallback
                details=details_dict if isinstance(details_dict, dict) else {}
            )
            
            # 3. Process Strategic Consequences
            # We pass the corresponding TP if we found one
            tp = new_tps.get(virtual_event.event_id)
            
            StrategicConsequenceService.process_consequences(
                world=ctx.snapshot,
                entity=actor,
                event=virtual_event,
                tp=tp,
                rng=ctx.rng,
                updates=updates
            )
            
        # 4. Update the watermark in the intent
        max_tick = max(m.tick for m in new_events)
        updates.last_interpreted_event_tick = max_tick
        logger.debug("Entity %d interpreted %d events (max_tick=%d)", actor.id, len(new_events), max_tick)
