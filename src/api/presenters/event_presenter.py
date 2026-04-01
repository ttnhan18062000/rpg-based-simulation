from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from src.api.schemas import EventSchema

class EventPresenter:
    """Presenter for individual simulation events."""

    @staticmethod
    def to_schema(event_data: tuple) -> "EventSchema":
        """
        Convert internal event tuple to EventSchema.
        Internal event format (usually from context.emit):
        (category, message, entity_ids, metadata, tick)
        """
        from src.api.schemas import EventSchema
        
        # Unpack with defaults
        category = "info"
        message = ""
        entity_ids = []
        metadata = None
        tick = 0
        
        if len(event_data) >= 2:
            category = event_data[0]
            message = event_data[1]
        if len(event_data) >= 3:
            entity_ids = list(event_data[2]) if event_data[2] else []
        if len(event_data) >= 4:
            metadata = event_data[3]
        if len(event_data) >= 5:
            tick = event_data[4]
            
        return EventSchema(
            tick=tick,
            category=category,
            message=message,
            entity_ids=entity_ids,
            metadata=metadata
        )

    @staticmethod
    def to_compact_list(event_data: tuple) -> list[Any]:
        """Ordered list for WebSocket: [tick, category, message, entity_ids]"""
        category = event_data[0] if len(event_data) >= 1 else "info"
        message = event_data[1] if len(event_data) >= 2 else ""
        entity_ids = list(event_data[2]) if len(event_data) >= 3 and event_data[2] else []
        tick = event_data[4] if len(event_data) >= 5 else 0
        return [tick, category, message, entity_ids]
