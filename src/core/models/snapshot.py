from __future__ import annotations

from collections import defaultdict
from typing import Mapping, TYPE_CHECKING, Any
from pydantic import Field, PrivateAttr

if TYPE_CHECKING:
    from src.core.gameplay.buildings import Building
    from src.core.world.grid import Grid
    from src.core.entities.entity import Entity
    from src.core.models.world_objects import TreasureChest
    from src.core.world.regions import Region
    from src.core.world.resource_nodes import ResourceNode
    from src.core.models.world_state import WorldState

from src.core.models.base import SimulationModel

_SPATIAL_CELL = 16  # cell size for snapshot spatial index

class Snapshot(SimulationModel):
    """Read-only view of the world, safe to share across threads.

    Enforces immutability at runtime through the SimulationModel base.
    """

    tick: int
    seed: int
    entities: Mapping[int, Entity]
    grid: Grid
    ground_items: Mapping[tuple[int, int], list[str]]
    camps: tuple[tuple[int, int], ...]
    buildings: tuple[Building, ...]
    resource_nodes: tuple[ResourceNode, ...]
    treasure_chests: tuple[TreasureChest, ...]
    regions: tuple[Region, ...]
    
    # Strategic State
    region_control: Mapping[str, float] = Field(default_factory=dict)
    war_status: Mapping[int, bool] = Field(default_factory=dict)
    faction_aggression: Mapping[int, float] = Field(default_factory=dict)
    
    # Internal spatial caches (not serialized)
    _spatial: dict = PrivateAttr(default_factory=dict)
    _spatial_ground: dict = PrivateAttr(default_factory=dict)

    @property
    def world_day(self) -> int:
        return self.tick // 100

    @classmethod
    def from_world(cls, world: WorldState) -> Snapshot:
        copied_entities = {}
        for eid, e in world.entities.items():
            # AOA Pillar 1: Isolation. Each entity in the snapshot must be 
            # a deep copy of the live state to ensure thread-safety and zero-mutation.
            ent = e.copy()
            ent.freeze()
            copied_entities[eid] = ent
        
        # Build spatial index
        spatial = defaultdict(list)
        for eid, e in copied_entities.items():
            if e.combat.hp > 0 and e.kind != "generator":
                spatial[(e.spatial.pos.x // _SPATIAL_CELL, e.spatial.pos.y // _SPATIAL_CELL)].append(eid)
                
        spatial_ground = defaultdict(list)
        for pos_key, items in world.ground_items.items():
            if items:
                spatial_ground[(pos_key[0] // _SPATIAL_CELL, pos_key[1] // _SPATIAL_CELL)].append(pos_key)
                
        snap = cls(
            tick=world.tick,
            seed=world.seed,
            entities=copied_entities,
            # CRITICAL: Must copy the grid! Otherwise snap.freeze() will freeze the live world grid.
            grid=world.grid.copy(),
            ground_items={k: list(v) for k, v in world.ground_items.items()},
            camps=tuple((c.x, c.y) for c in world.camps),
            buildings=tuple(b.copy() for b in world.buildings),
            resource_nodes=tuple(n.copy() for n in world.resource_nodes.values()),
            treasure_chests=tuple(c.copy() for c in world.treasure_chests.values()),
            regions=tuple(r.copy() for r in world.regions),
            region_control=dict(world.region_control),
            war_status=dict(world.war_status),
            faction_aggression=dict(world.faction_aggression),
        )
        
        # Manually set private attrs
        snap._spatial = dict(spatial)
        snap._spatial_ground = dict(spatial_ground)
        
        # Recursive freeze
        snap.freeze()
        return snap

    def nearby_entity_ids(self, x: int, y: int, radius: int) -> list[int]:
        """Return entity IDs in cells overlapping the Manhattan-radius neighborhood."""
        cx, cy = x // _SPATIAL_CELL, y // _SPATIAL_CELL
        r = (radius // _SPATIAL_CELL) + 1
        result: list[int] = []
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                bucket = self._spatial.get((cx + dx, cy + dy))
                if bucket:
                    result.extend(bucket)
        return result

    def nearby_ground_positions(self, x: int, y: int, radius: int) -> list[tuple[int, int]]:
        """Return ground item positions (gx, gy) in neighboring spatial cells."""
        cx, cy = x // _SPATIAL_CELL, y // _SPATIAL_CELL
        r = (radius // _SPATIAL_CELL) + 1
        result: list[tuple[int, int]] = []
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                bucket = self._spatial_ground.get((cx + dx, cy + dy))
                if bucket:
                    result.extend(bucket)
        return result


# --- AOA Stabilization: Pydantic Rebuild ---
# Resolve forward references for Snapshot once dependencies are defined.
# Restore eager rebuild now that circular dependency is broken.
from src.core.entities.entity import Entity
from src.core.world.grid import Grid
from src.core.gameplay.buildings import Building
from src.core.models.world_objects import TreasureChest
from src.core.world.resource_nodes import ResourceNode
from src.core.world.regions import Region
from src.core.models.vectors import Vector2, FloatVector2
from src.core.models.enums import Faction, HeroClass, AIState, ActionType, EmotionType, GoalType

Snapshot.model_rebuild()
