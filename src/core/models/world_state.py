"""Mutable authoritative world state — only mutated by the WorldLoop."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.gameplay.buildings import Building
from src.core.world.grid import Grid
from src.core.entities.entity import Entity
from .vectors import Vector2
from .world_objects import TreasureChest
from src.core.world.regions import Region
from src.core.world.resource_nodes import ResourceNode

if TYPE_CHECKING:
    from src.platform.spatial_hash import SpatialHash


class WorldState:
    """The single source of truth for the simulation."""

    __slots__ = ("world_age", "faction_aggression", "difficulty_modifier", "monuments", "tick", "seed", "entities", "grid", "spatial_index", "_next_entity_id", "ground_items", "camps", "buildings", "resource_nodes", "_next_node_id", "treasure_chests", "_next_chest_id", "regions", "maturity", "last_calamity_tick", "event_bus", "faction_deaths_per_region", "region_control", "war_status", "history", "_history_subscribed", "town_treasury", "corpse_nodes", "_next_corpse_id")

    def __init__(
        self,
        seed: int,
        grid: Grid,
        spatial_index: SpatialHash,
    ) -> None:
        self.tick: int = 0
        self.seed: int = seed
        self.world_age: int = 0
        self.maturity: int = 0
        self.last_calamity_tick: int = 0
        self.faction_aggression: dict[int, float] = {}
        self.faction_deaths_per_region: dict[tuple[int, int], int] = {} # (faction_id, region_id) -> count
        self.region_control: dict[str, float] = {} # region_id -> influence (-100 to 100)
        self.war_status: dict[int, bool] = {} # faction_id -> is_at_war
        self.history: list[dict] = []
        self._history_subscribed: bool = False
        self.difficulty_modifier: float = 1.0
        self.monuments: list = []
        self.entities: dict[int, Entity] = {}
        self.grid: Grid = grid
        self.spatial_index: SpatialHash = spatial_index
        self._next_entity_id: int = 1
        self.ground_items: dict[tuple[int, int], list[str]] = {}
        self.camps: list[Vector2] = []
        self.buildings: list[Building] = []
        self.resource_nodes: dict[int, ResourceNode] = {}
        self._next_node_id: int = 1
        self.treasure_chests: dict[int, TreasureChest] = {}
        self._next_chest_id: int = 1
        self.regions: list[Region] = []
        self.town_treasury: int = 0
        self.corpse_nodes: dict[int, CorpseNode] = {}
        self._next_corpse_id: int = 1
        self.event_bus = None

    def allocate_entity_id(self) -> int:
        eid = self._next_entity_id
        self._next_entity_id += 1
        return eid

    @property
    def world_day(self) -> int:
        return self.tick // 100

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity
        self.spatial_index.insert(entity.id, entity.spatial.pos)

    def remove_entity(self, entity_id: int) -> Entity | None:
        entity = self.entities.pop(entity_id, None)
        if entity is not None:
            self.spatial_index.remove(entity_id, entity.spatial.pos)
        return entity

    def move_entity(self, entity_id: int, new_pos: Vector2) -> None:
        entity = self.entities.get(entity_id)
        if entity is None:
            return
        old_pos = entity.spatial.pos
        entity.spatial.pos = new_pos
        self.spatial_index.move(entity_id, old_pos, new_pos)

    def entities_at_radius(self, pos: Vector2, radius: int) -> list[Entity]:
        """Return all entities within *radius* of *pos*."""
        ids = self.spatial_index.query_radius(pos, radius)
        return [self.entities[eid] for eid in ids if eid in self.entities]

    def drop_items(self, pos: Vector2, item_ids: list[str]) -> None:
        """Place items on the ground at *pos*."""
        if not item_ids:
            return
        key = (pos.x, pos.y)
        if key not in self.ground_items:
            self.ground_items[key] = []
        self.ground_items[key].extend(item_ids)

    def pickup_items(self, pos: Vector2) -> list[str]:
        """Remove and return all ground items at *pos*."""
        key = (pos.x, pos.y)
        return self.ground_items.pop(key, [])

    def add_resource_node(self, node: ResourceNode) -> None:
        self.resource_nodes[node.node_id] = node

    def allocate_node_id(self) -> int:
        nid = self._next_node_id
        self._next_node_id += 1
        return nid

    def resource_at(self, pos: Vector2) -> ResourceNode | None:
        """Return the resource node at *pos*, if any."""
        for node in self.resource_nodes.values():
            if node.spatial.pos == pos:
                return node
        return None

    @classmethod
    def from_snapshot(cls, snap: 'Snapshot', spatial_index: SpatialHash) -> WorldState:
        """Reconstruct a mutable WorldState from a serialized Snapshot."""
        world = cls(seed=snap.seed, grid=snap.grid, spatial_index=spatial_index)
        world.tick = snap.tick
        
        for eid, entity in snap.entities.items():
            world.add_entity(entity.copy())
            world._next_entity_id = max(world._next_entity_id, eid + 1)
            
        world.ground_items = {k: list(v) for k, v in snap.ground_items.items()}
        world.camps = [Vector2(x, y) for x, y in snap.camps]
        world.buildings = list(snap.buildings)
        
        for node in snap.resource_nodes:
            world.add_resource_node(node.copy())
            world._next_node_id = max(world._next_node_id, node.node_id + 1)
            
        for chest in snap.treasure_chests:
            world.treasure_chests[chest.chest_id] = chest.copy()
            world._next_chest_id = max(world._next_chest_id, chest.chest_id + 1)
            
        world.regions = [r.copy() for r in snap.regions]
        world.event_bus = None
        
        return world
