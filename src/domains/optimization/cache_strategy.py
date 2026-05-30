from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass(frozen=True, slots=True)
class CacheKey:
    region_id: str
    query_type: str
    extra_param: Optional[str] = None

class CacheStrategy:
    """Manages local, bounded caches and event-driven invalidation."""
    def __init__(self, max_size: int = 100) -> None:
        self.max_size = max_size
        self._cache: Dict[CacheKey, Any] = {}
        self._keys_order: List[CacheKey] = []

    def get(self, key: CacheKey) -> Optional[Any]:
        if key in self._cache:
            # Move key to end for LRU policy
            self._keys_order.remove(key)
            self._keys_order.append(key)
            return self._cache[key]
        return None

    def put(self, key: CacheKey, value: Any) -> None:
        if key in self._cache:
            self._keys_order.remove(key)
        elif len(self._cache) >= self.max_size:
            # Evict oldest
            oldest = self._keys_order.pop(0)
            self._cache.pop(oldest, None)

        self._cache[key] = value
        self._keys_order.append(key)

    def invalidate(self, event_type: str, region_id: str) -> None:
        # Based on event_type and region_id, remove corresponding keys
        to_remove = []
        for key in self._cache.keys():
            if key.region_id == region_id:
                if event_type == "resource_depleted" and key.query_type in ("resource_nodes", "active_resources"):
                    to_remove.append(key)
                elif event_type == "shop_stock_changed" and key.query_type == "shop_stock":
                    to_remove.append(key)
                elif event_type == "service_unavailable" and key.query_type == "services":
                    to_remove.append(key)
                elif event_type == "region_pressure_changed" and key.query_type == "pressure":
                    to_remove.append(key)
                elif event_type in ("entity_moved", "knowledge_changed", "inventory_changed", "equipment_changed"):
                    to_remove.append(key)

        for key in to_remove:
            self._cache.pop(key, None)
            if key in self._keys_order:
                self._keys_order.remove(key)
