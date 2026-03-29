from __future__ import annotations
from typing import Any, TYPE_CHECKING
import msgpack
import json

if TYPE_CHECKING:
    from src.core.models.snapshot import Snapshot
    from src.core.entities.entity import Entity
    from src.core.data.events import Event

# --- Constants for Compact Protocol ---

# Order must match exactly in both backend and frontend
ENTITY_KEY_MAP = [
    "id", "x", "y", "hp", "state_id", "target_id", "loot_progress"
]

STATE_ENUM_MAP = {
    "IDLE": 0,
    "MOVE": 1,
    "COMBAT": 2,
    "LOOT": 3,
    "HARVEST": 4,
    "CRAFT": 5,
    "REST": 6,
    "DEAD": 7,
    "FLEE": 8,
    "WANDER": 9
}

class WorldStateEncoder:
    """Serializes simulation state into Rich (Dict) or Compact (List) formats."""

    @staticmethod
    def encode_entity(entity: Entity, mode: str = "rich") -> dict[str, Any] | list[Any]:
        """Encodes a single entity."""
        if mode == "compact":
            # [id, x, y, hp, state_id, target_id, loot_progress]
            state_name = entity.mind.ai_state.name.upper() if hasattr(entity, 'ai_state') else "IDLE"
            state_id = STATE_ENUM_MAP.get(state_name, 0)
            return [
                entity.id,
                int(entity.spatial.pos.x),
                int(entity.spatial.pos.y),
                entity.stats.combat.hp,
                state_id,
                entity.combat_target_id,
                entity.loot_progress
            ]
        else:
            # Traditional Rich Dict (matches EntitySlimSchema partially)
            return {
                "id": entity.id,
                "kind": entity.kind,
                "display_name": entity.identity.display_name,
                "x": int(entity.spatial.pos.x),
                "y": int(entity.spatial.pos.y),
                "hp": entity.stats.combat.hp,
                "max_hp": entity.stats.combat.max_hp,
                "state": entity.mind.ai_state.name.lower() if hasattr(entity, 'ai_state') else "idle",
                "level": entity.stats.progression.level,
                "faction": entity.identity.faction.name.lower() if hasattr(entity.identity.faction, 'name') else str(entity.identity.faction),
                "combat_target_id": entity.combat_target_id
            }

    @staticmethod
    def encode_event(event: Event, mode: str = "rich") -> dict[str, Any] | list[Any]:
        """Encodes a single domain event."""
        if mode == "compact":
            # [tick, category, message, entity_ids]
            return [
                event.tick,
                event.category,
                event.message,
                list(event.entity_ids)
            ]
        else:
            return {
                "tick": event.tick,
                "category": event.category,
                "message": event.message,
                "entity_ids": list(event.entity_ids),
                "metadata": event.metadata
            }

    @classmethod
    def encode_tick(cls, snapshot: Snapshot, events: list[Event], mode: str = "compact") -> Any:
        """Encodes an entire tick state."""
        entities = [
            cls.encode_entity(e, mode)
            for e in snapshot.entities.values()
            if e.combat.alive
        ]
        encoded_events = [
            cls.encode_event(ev, mode)
            for ev in events
        ]
        
        if mode == "compact":
            # [tick, entities, events]
            return [snapshot.tick, entities, encoded_events]
        else:
            return {
                "tick": snapshot.tick,
                "entities": entities,
                "events": encoded_events,
                "alive_count": len(entities)
            }

    @classmethod
    def serialize(cls, data: Any, format: str = "msgpack") -> bytes | str:
        """Final serialization to wire format."""
        if format == "msgpack":
            return msgpack.packb(data, use_bin_type=True)
        else:
            return json.dumps(data)
