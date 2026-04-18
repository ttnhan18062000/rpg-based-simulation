"""Mutable authoritative world state — only mutated by the WorldLoop."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .vectors import Vector2
from .world_objects import TreasureChest, CorpseNode
from .social import SocialRegistry
from .lived_structure import GroupRecord # [PHASE 3]
from .history import WorldHistoryRegistry # [PHASE 4]
from .households import HouseholdRecord # [PHASE 4]
from .local_scars import LocalScarRecord # [PHASE 4]
from .regions import RegionConsequenceRecord # [PHASE 4]
from .continuity import SuccessorRecord # [PHASE 4]
from .world_strategy import WorldStrategicRegistry # [PHASE 6]

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.core.gameplay.buildings import Building
    from src.core.world.grid import Grid
    from src.core.world.regions import Region
    from src.core.world.resource_nodes import ResourceNode
    from src.platform.spatial_hash import SpatialHash
    from .snapshot import Snapshot


class WorldState:
    """The single source of truth for the simulation."""

    __slots__ = ("world_age", "faction_aggression", "difficulty_modifier", "monuments", "tick", "seed", "entities", "grid", "spatial_index", "_next_entity_id", "ground_items", "camps", "buildings", "resource_nodes", "_next_node_id", "treasure_chests", "_next_chest_id", "regions", "maturity", "last_calamity_tick", "event_bus", "faction_deaths_per_region", "region_control", "war_status", "history", "_history_subscribed", "town_treasury", "corpse_nodes", "_next_corpse_id", "social_registry", "group_registry", "world_history", "household_registry", "scar_registry", "region_consequence_registry", "successor_registry", "strategic_registry", "_frozen")

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
        self.social_registry: SocialRegistry = SocialRegistry()
        self.group_registry: dict[str, GroupRecord] = {} # [PHASE 3]
        self.world_history: WorldHistoryRegistry = WorldHistoryRegistry() # [PHASE 4]
        self.household_registry: dict[str, HouseholdRecord] = {} # [PHASE 4]
        self.scar_registry: list[LocalScarRecord] = [] # [PHASE 4]
        self.region_consequence_registry: dict[str, RegionConsequenceRecord] = {} # [PHASE 4]
        self.successor_registry: dict[int, SuccessorRecord] = {} # [PHASE 4] Entity ID -> Record
        self.strategic_registry: WorldStrategicRegistry = WorldStrategicRegistry() # [PHASE 6]
        self.event_bus = None
        self._frozen: bool = False

    def _check_frozen(self, method_name: str) -> None:
        if self._frozen:
            raise RuntimeError(f"Cannot call {method_name} on frozen WorldState. Simulation is in a read-only phase.")

    def freeze(self) -> None:
        """Lock the world state and all its contents (Recursive)."""
        if self._frozen: return
        self._frozen = True
        for entity in self.entities.values():
            if hasattr(entity, "freeze"):
                entity.freeze()
        for node in self.resource_nodes.values():
            if hasattr(node, "freeze"):
                node.freeze()
        for chest in self.treasure_chests.values():
            if hasattr(chest, "freeze"):
                chest.freeze()
        for corpse in self.corpse_nodes.values():
            if hasattr(corpse, "freeze"):
                corpse.freeze()
        
        # Phase 4 registries
        self.world_history.freeze()
        for household in self.household_registry.values():
            household.freeze()
        for scar in self.scar_registry:
            scar.freeze()
        for region_con in self.region_consequence_registry.values():
            region_con.freeze()
        for successor in self.successor_registry.values():
            successor.freeze()
        self.strategic_registry.freeze()

    def allocate_entity_id(self) -> int:
        self._check_frozen("allocate_entity_id")
        eid = self._next_entity_id
        self._next_entity_id += 1
        return eid

    @property
    def world_day(self) -> int:
        return self.tick // 100

    def add_entity(self, entity: Entity) -> None:
        self._check_frozen("add_entity")
        self.entities[entity.id] = entity
        self.spatial_index.insert(entity.id, entity.spatial.pos)

    def remove_entity(self, entity_id: int) -> Entity | None:
        self._check_frozen("remove_entity")
        entity = self.entities.pop(entity_id, None)
        if entity is not None:
            self.spatial_index.remove(entity_id, entity.spatial.pos)
        return entity

    def move_entity(self, entity_id: int, new_pos: Vector2) -> None:
        self._check_frozen("move_entity")
        entity = self.entities.get(entity_id)
        if entity is None:
            return
        old_pos = entity.spatial.pos
        entity.spatial.pos = new_pos
        self.spatial_index.move(entity_id, old_pos, new_pos)

    def get_entity(self, entity_id: int) -> Entity | None:
        """Safe entity lookup by ID."""
        return self.entities.get(entity_id)

    def entities_at_radius(self, pos: Vector2, radius: int) -> list[Entity]:
        """Return all entities within *radius* of *pos*."""
        ids = self.spatial_index.query_radius(pos, radius)
        return [self.entities[eid] for eid in ids if eid in self.entities]

    def is_occupied(self, pos: Vector2) -> bool:
        """O(1) check if a position is occupied by a living entity using the spatial index."""
        return self.get_entity_at(pos) is not None

    def get_entity_at(self, pos: Vector2) -> int | None:
        """Returns the ID of the living entity at the given position, if any."""
        ids = self.spatial_index.query_cell(pos)
        for eid in ids:
            e = self.entities.get(eid)
            if e and e.combat.alive and e.spatial.pos.x == pos.x and e.spatial.pos.y == pos.y:
                return eid
        return None

    def drop_items(self, pos: Vector2, item_ids: list[str]) -> None:
        self._check_frozen("drop_items")
        """Place items on the ground at *pos*."""
        if not item_ids:
            return
        key = (pos.x, pos.y)
        if key not in self.ground_items:
            self.ground_items[key] = []
        self.ground_items[key].extend(item_ids)

    def pickup_items(self, pos: Vector2) -> list[str]:
        self._check_frozen("pickup_items")
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
    def from_snapshot(cls, snap: Snapshot, spatial_index: SpatialHash) -> WorldState:
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
        world.social_registry = snap.social_registry.copy()
        if hasattr(snap, "group_registry"):
             world.group_registry = {k: v.copy(deep=False) for k, v in snap.group_registry.items()}
        
        # Phase 4 registries recovery
        if hasattr(snap, "world_history"):
            world.world_history = snap.world_history.copy()
        if hasattr(snap, "household_registry"):
            world.household_registry = {k: v.copy(deep=False) for k, v in snap.household_registry.items()}
        if hasattr(snap, "scar_registry"):
            # AOA Stabilization: Shallow copy instead of deepcopy to avoid mappingproxy pickling errors [design-03]
            world.scar_registry = [v.copy(deep=False) for v in snap.scar_registry]
        if hasattr(snap, "region_consequence_registry"):
            world.region_consequence_registry = {k: v.copy(deep=False) for k, v in snap.region_consequence_registry.items()}
        if hasattr(snap, "successor_registry"):
            world.successor_registry = {k: v.copy(deep=False) for k, v in snap.successor_registry.items()}
        if hasattr(snap, "strategic_registry"):
            world.strategic_registry = snap.strategic_registry.copy()
            
        world.event_bus = None
        
        return world

    def compute_hash(self) -> str:
        """Compute a deterministic hash of the world state for validation (AOA Pillar 3)."""
        import hashlib
        import json
        
        # Capture strictly deterministic state components
        state_data = {
            "tick": self.tick,
            "seed": self.seed,
            "entities": sorted([
                (
                    e.id, 
                    round(e.spatial.pos.x, 2), 
                    round(e.spatial.pos.y, 2), 
                    int(e.combat.hp), 
                    int(e.progression.xp)
                )
                for e in self.entities.values()
            ]),
            "ground_items": sorted([
                (int(k[0]), int(k[1]), sorted(v)) 
                for k, v in self.ground_items.items() 
                if v
            ]),
            "resource_nodes": sorted([
                (n.node_id, int(n.remaining), bool(n.is_available))
                for n in self.resource_nodes.values()
            ])
        }
        
        # Use stable JSON serialization
        state_str = json.dumps(state_data, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()

    def shutdown(self) -> None:
        """Deep cleanup of world state collections to break circular references and free memory. [Harden 7]"""
        # Clear large dictionaries
        self.entities.clear()
        self.resource_nodes.clear()
        self.treasure_chests.clear()
        self.corpse_nodes.clear()
        self.ground_items.clear()
        self.group_registry.clear()
        self.household_registry.clear()
        self.region_consequence_registry.clear()
        self.successor_registry.clear()
        
        # Clear large lists
        self.camps.clear()
        self.buildings.clear()
        self.regions.clear()
        self.scar_registry.clear()
        self.history.clear()
        self.monuments.clear()
        
        # Shutdown sub-registries if they support it
        if hasattr(self.social_registry, "shutdown"):
            self.social_registry.shutdown()
        if hasattr(self.world_history, "clear"):
            self.world_history.clear()
        if hasattr(self.strategic_registry, "clear"):
            self.strategic_registry.clear()
            
        # Clear event bus to prevent lingering handler references
        self.event_bus = None
