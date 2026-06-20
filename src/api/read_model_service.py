from __future__ import annotations
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.api.engine_manager import V2EngineManager


class ReadModelService:
    """
    Unified presenter facade for all API read paths.
    All API responses must be shaped here — never expose raw AuthoritativeState.
    Routes and WebSocket handlers inject this service or call manager methods that
    already delegate to ReadModelCache → StatePresenter (both satisfy the contract).
    """

    def __init__(self, manager: "V2EngineManager") -> None:
        self._manager = manager

    def world_status(self) -> Dict[str, Any]:
        """Returns the minimal world summary (O(1), cache-backed)."""
        return self._manager.get_state()

    def world_full(self) -> Dict[str, Any]:
        """Returns the full world snapshot (O(N), use sparingly)."""
        return self._manager.get_full_snapshot()

    def entity_status(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """Returns the shaped entity DTO or None if the entity does not exist."""
        return self._manager.get_entity(entity_id)

    def entity_timeline(self, entity_id: int) -> List[Dict[str, Any]]:
        """Returns serialized timeline events for an entity, or [] if not found."""
        return self._manager.get_entity_timeline_events(entity_id)

    def entities_paged(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Returns a paged entity listing with total, offset, and limit metadata."""
        return self._manager.get_entities_paged(offset=offset, limit=limit)
