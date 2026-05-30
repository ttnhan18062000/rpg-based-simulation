from typing import Dict, Set, Tuple, List

class DirtyWorkScheduler:
    """Schedules updates for entities and regions that have dirty/modified states."""
    def __init__(self) -> None:
        self._dirty_entities: Dict[int, Set[str]] = {}
        self._dirty_regions: Dict[str, Set[str]] = {}

    def mark_entity_dirty(self, entity_id: int, reason: str) -> None:
        if entity_id not in self._dirty_entities:
            self._dirty_entities[entity_id] = set()
        self._dirty_entities[entity_id].add(reason)

    def mark_region_dirty(self, region_id: str, reason: str) -> None:
        if region_id not in self._dirty_regions:
            self._dirty_regions[region_id] = set()
        self._dirty_regions[region_id].add(reason)

    def is_entity_dirty(self, entity_id: int) -> bool:
        return entity_id in self._dirty_entities

    def is_region_dirty(self, region_id: str) -> bool:
        return region_id in self._dirty_regions

    def get_dirty_entities(self) -> List[int]:
        return list(self._dirty_entities.keys())

    def get_dirty_regions(self) -> List[str]:
        return list(self._dirty_regions.keys())

    def next_entities(self, phase_name: str, count: int) -> Tuple[int, ...]:
        # Return entity IDs in sorted ascending order up to count for determinism
        sorted_ids = sorted(self._dirty_entities.keys())
        return tuple(sorted_ids[:count])

    def next_regions(self, phase_name: str, count: int) -> Tuple[str, ...]:
        sorted_ids = sorted(self._dirty_regions.keys())
        return tuple(sorted_ids[:count])

    def clear_processed_entities(self, entity_ids: Tuple[int, ...]) -> None:
        for eid in entity_ids:
            self._dirty_entities.pop(eid, None)

    def clear_processed_regions(self, region_ids: Tuple[str, ...]) -> None:
        for rid in region_ids:
            self._dirty_regions.pop(rid, None)

    def generate_report(self) -> Dict[int, Set[str]]:
        return {k: set(v) for k, v in self._dirty_entities.items()}
