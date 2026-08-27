# Compliance IDs: PERF-007, PERF-010
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional, Any, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, ResourceNodeState, BuildingState
    from src.core.dirty import DirtySet


class CacheInvalidationPolicy:
    """
    Determines whether spatial indices and caches must be rebuilt based on DirtySet.
    Logic ID: PERF-011 (Cache Invalidation Policy)
    """

    @staticmethod
    def invalidated_indexes(dirty: DirtySet) -> Set[str]:
        invalidated: Set[str] = set()
        if dirty.resource_node_ids:
            invalidated.add("active_resource_node_index")
        if dirty.building_ids:
            invalidated.add("building_kind_index")
        if dirty.movement_entities or dirty.lifecycle_entities:
            invalidated.add("entity_position_index")
            invalidated.add("occupancy_snapshot")
        if dirty.ground_item_ids:
            invalidated.add("ground_item_index")
        if dirty.corpse_ids:
            invalidated.add("corpse_index")
        if dirty.region_ids:
            invalidated.add("region_index")
        # PERF-010 (Semantic Entity Indexes): additive domains, distinctly named so they never
        # collide with the pre-existing "region_index" phantom-field bug above (WorldIndexes has
        # no region_index field and WorldIndexService never checks for it -- tracked separately,
        # not fixed here).
        if dirty.identity_entities:
            invalidated.add("semantic_identity_index")
        if dirty.region_ids:
            invalidated.add("semantic_region_index")
        if dirty.biological_entities:
            invalidated.add("semantic_needs_index")
        return invalidated

    @staticmethod
    def should_invalidate(domain: str, dirty: Optional[DirtySet]) -> bool:
        if dirty is None:
            return True
        idx = CacheInvalidationPolicy.invalidated_indexes(dirty)
        if domain == "resources":
            return "active_resource_node_index" in idx
        if domain == "buildings":
            return "building_kind_index" in idx
        if domain == "entities":
            return "entity_position_index" in idx
        if domain == "ground_items":
            return "ground_item_index" in idx
        if domain == "corpses":
            return "corpse_index" in idx
        if domain == "regions":
            return "region_index" in idx
        # PERF-010 (Semantic Entity Indexes): additive domains for SemanticEntityIndexService.
        if domain == "identity":
            return "semantic_identity_index" in idx
        if domain == "region":
            return "semantic_region_index" in idx
        if domain == "needs":
            return "semantic_needs_index" in idx
        if domain == "knowledge":
            # information_providers mutations carry no dedicated DirtySet tag today (out of scope
            # to invent one -- AC #3 only requires role/region/faction incremental invalidation).
            # Conservatively always invalidate rather than risk a stale knowledge_domain index.
            return True
        return True


@dataclass(frozen=True)
class SpatialIndex:
    """
    Spatial grid index chunking space into 20x20 tile buckets.
    """
    grid: Dict[Tuple[int, int], Tuple[int, ...]]


@dataclass(frozen=True)
class WorldIndexes:
    """
    Immutable spatial indices over world state for a single tick.
    Logic ID: PERF-010 (World Indexes)
    """
    tick: int
    active_resource_nodes: SpatialIndex
    buildings_by_kind: Dict[str, Tuple[int, ...]]
    entities_by_tile: Dict[Tuple[int, int], Tuple[int, ...]]
    ground_items_by_tile: Dict[Tuple[int, int], Tuple[int, ...]]
    corpses_by_tile: Dict[Tuple[int, int], Tuple[int, ...]]


class WorldIndexService:
    """
    Authoritative builder for reusable spatial indices over world state.
    Logic ID: PERF-010 (World Index Service)
    """

    @staticmethod
    def get_indexes(state: AuthoritativeState, dirty: Optional[DirtySet] = None) -> WorldIndexes:
        existing: Optional[WorldIndexes] = getattr(state, "world_indexes", None)
        
        if existing is not None and existing.tick == state.tick:
            try:
                object.__setattr__(state, "_index_hits", getattr(state, "_index_hits", 0) + 1)
            except AttributeError:
                pass
            return existing

        # Rebuild or reuse based on CacheInvalidationPolicy
        res_index = existing.active_resource_nodes if existing and not CacheInvalidationPolicy.should_invalidate("resources", dirty) else WorldIndexService._build_resource_index(state)
        bldg_index = existing.buildings_by_kind if existing and not CacheInvalidationPolicy.should_invalidate("buildings", dirty) else WorldIndexService._build_building_index(state)
        ent_index = existing.entities_by_tile if existing and not CacheInvalidationPolicy.should_invalidate("entities", dirty) else WorldIndexService._build_entity_index(state)
        item_index = existing.ground_items_by_tile if existing and not CacheInvalidationPolicy.should_invalidate("ground_items", dirty) else WorldIndexService._build_ground_item_index(state)
        corpse_index = existing.corpses_by_tile if existing and not CacheInvalidationPolicy.should_invalidate("corpses", dirty) else WorldIndexService._build_corpse_index(state)

        new_indexes = WorldIndexes(
            tick=state.tick,
            active_resource_nodes=res_index,
            buildings_by_kind=bldg_index,
            entities_by_tile=ent_index,
            ground_items_by_tile=item_index,
            corpses_by_tile=corpse_index
        )
        
        try:
            object.__setattr__(state, "world_indexes", new_indexes)
            object.__setattr__(state, "_index_misses", getattr(state, "_index_misses", 0) + 1)
        except AttributeError:
            pass
            
        return new_indexes

    @staticmethod
    def _build_resource_index(state: AuthoritativeState) -> SpatialIndex:
        buckets: Dict[Tuple[int, int], List[int]] = {}
        for n_id, n in state.resource_nodes.items():
            if n.remaining_charges > 0 and n.cooldown_remaining <= 0:
                cx, cy = int(n.position[0] // 20), int(n.position[1] // 20)
                buckets.setdefault((cx, cy), []).append(n_id)
        
        return SpatialIndex(grid={k: tuple(v) for k, v in buckets.items()})

    @staticmethod
    def _build_building_index(state: AuthoritativeState) -> Dict[str, Tuple[int, ...]]:
        kinds: Dict[str, List[int]] = {}
        for b_id, b in state.buildings.items():
            kinds.setdefault(b.kind, []).append(b_id)
        return {k: tuple(v) for k, v in kinds.items()}

    @staticmethod
    def _build_entity_index(state: AuthoritativeState) -> Dict[Tuple[int, int], Tuple[int, ...]]:
        import math
        tiles: Dict[Tuple[int, int], List[int]] = {}
        for e_id, e in state.entities.items():
            if e.lifecycle.active and e.combat.alive:
                x, y = e.navigation.position
                if math.isfinite(x) and math.isfinite(y):
                    pos = (int(x), int(y))
                    tiles.setdefault(pos, []).append(e_id)
        return {k: tuple(v) for k, v in tiles.items()}

    @staticmethod
    def _build_ground_item_index(state: AuthoritativeState) -> Dict[Tuple[int, int], Tuple[int, ...]]:
        tiles: Dict[Tuple[int, int], List[int]] = {}
        for g_id, g in state.ground_items.items():
            pos = (int(g.position[0]), int(g.position[1]))
            tiles.setdefault(pos, []).append(g_id)
        return {k: tuple(v) for k, v in tiles.items()}

    @staticmethod
    def _build_corpse_index(state: AuthoritativeState) -> Dict[Tuple[int, int], Tuple[int, ...]]:
        tiles: Dict[Tuple[int, int], List[int]] = {}
        for c_id, c in state.corpses.items():
            pos = (int(c.position[0]), int(c.position[1]))
            tiles.setdefault(pos, []).append(c_id)
        return {k: tuple(v) for k, v in tiles.items()}
