import logging
from typing import TYPE_CHECKING
from src.core.aspects.mind import InterpretedEvent

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

logger = logging.getLogger(__name__)

class MemorySalienceService:
    """Intelligent narrative pruning using Impact x Recency weighting. [PHASE 0 FIX]"""

    @staticmethod
    def calculate_weighted_impact(event: InterpretedEvent, current_tick: int, decay_per_tick: float = 0.001) -> float:
        """Calculate salience given event impact and age."""
        age = current_tick - event.tick
        # Linear decay: Weight = |Impact| * (1.0 - (Age * Decay))
        # Clamp weight at 10% of original impact (minimum legacy value)
        multiplier = max(0.1, 1.0 - (age * decay_per_tick))
        return abs(event.impact) * multiplier

    @classmethod
    def prune(cls, entity: "Entity", current_tick: int, max_entries: int = 50) -> None:
        """Authoritatively prune an entity's memory log based on weighted salience."""
        log = entity.mind.narrative.memory_log
        if len(log) <= max_entries:
            return

        # Sort by weighted impact descending (salience)
        # We use a slightly higher decay for pruning to favor recent meaningful events
        sorted_log = sorted(
            log, 
            key=lambda e: cls.calculate_weighted_impact(e, current_tick, decay_per_tick=0.002), 
            reverse=True
        )

        # Keep the top entries
        entity.mind.narrative.memory_log = sorted_log[:max_entries]
        # Re-sort chronologically for the inspector/AI
        entity.mind.narrative.memory_log.sort(key=lambda e: e.tick)
        
        logger.debug("Pruned memories for entity %d to %d entries.", entity.id, max_entries)
