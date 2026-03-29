"""HistorySystem records major world events into the narrative log."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class HistorySystem(System):
    """System that records major occurrences for world-wide narrative persistence."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Initialize subscriptions if not already done."""
        self._world = context.world
        if not context.world._history_subscribed:
            if hasattr(context.world, "event_bus") and context.world.event_bus:
                context.world.event_bus.subscribe_all(self._on_any_event)
                context.world._history_subscribed = True

    def _on_any_event(self, event: DomainEvent) -> None:
        """Handle any domain event and record if relevant."""
        from src.core.data.events import RenownEvent, WarEvent, ConquestEvent, QuestEvent
        
        # We only record high-level narrative events in the history
        if isinstance(event, (RenownEvent, WarEvent, ConquestEvent)):
            desc = getattr(event, "description", "")
            if isinstance(event, WarEvent):
                status = "DECLARED" if event.is_declared else "ENDED"
                desc = f"War {status} by Faction {event.faction_id} (Aggression: {event.aggression:.1f})"
            elif isinstance(event, ConquestEvent):
                type_str = "LIBERATED" if event.is_liberation else "CONQUERED"
                desc = f"Region {event.region_name} was {type_str}"

            self._record(desc, type(event).__name__, event.__dict__)

    def _record(self, description: str, event_type: str, metadata: dict) -> None:
        """Internal helper to append to world history."""
        if not hasattr(self, "_world"):
            return
            
        entry = {
            "tick": self._world.tick,
            "type": event_type,
            "desc": description,
            "meta": metadata
        }
        self._world.history.append(entry)
        
        logger.info("World History [%s]: %s", event_type, description)

    def record_event(self, context: SystemContext, tick: int, event_type: str, description: str, metadata: dict | None = None) -> None:
        """Manual injection for world events."""
        entry = {
            "tick": tick,
            "type": event_type,
            "desc": description,
            "meta": metadata or {}
        }
        context.world.history.append(entry)
        
        if context.emit:
            context.emit("history", f"WORLD RECORD: {description}",
                        metadata=entry)
        
        logger.info("World History [%s]: %s", event_type, description)
