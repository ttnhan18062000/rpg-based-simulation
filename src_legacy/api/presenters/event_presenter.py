from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from src_legacy.api.schemas import EventSchema

class EventPresenter:
    """Presenter for individual simulation events."""

    @staticmethod
    def to_schema(event_data: Any) -> "EventSchema":
        """
        Convert internal event (SimEvent or legacy tuple) to EventSchema.
        """
        from src_legacy.api.schemas import EventSchema
        from src_legacy.utils.event_log import SimEvent
        
        if isinstance(event_data, SimEvent):
            return EventSchema(
                tick=event_data.tick,
                category=event_data.category,
                message=event_data.message,
                entity_ids=list(event_data.entity_ids),
                metadata=event_data.metadata
            )

        # Legacy tuple Unpack with defaults
        category = "info"
        message = ""
        entity_ids = []
        metadata = None
        tick = 0
        
        if isinstance(event_data, (tuple, list)):
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
    def to_compact_list(event_data: Any) -> list[Any]:
        """Ordered list for WebSocket: [tick, category, message, entity_ids]"""
        from src_legacy.utils.event_log import SimEvent
        
        if isinstance(event_data, SimEvent):
            return [event_data.tick, event_data.category, event_data.message, list(event_data.entity_ids)]

        # Legacy tuple support
        if isinstance(event_data, (tuple, list)):
            tick = event_data[4] if len(event_data) >= 5 else 0
            category = event_data[0] if len(event_data) >= 1 else "info"
            message = event_data[1] if len(event_data) >= 2 else ""
            entity_ids = list(event_data[2]) if len(event_data) >= 3 and event_data[2] else []
            return [tick, category, message, entity_ids]
            
        return [0, "info", str(event_data), []]
