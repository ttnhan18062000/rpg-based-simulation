"""Immutable snapshot of the world state for worker threads."""

from __future__ import annotations

from collections import defaultdict
from types import MappingProxyType
from dataclasses import dataclass, field
from typing import Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.gameplay.buildings import Building
    from src.core.world.grid import Grid
    from src.core.entities.entity import Entity
    from src.core.models.world_objects import TreasureChest
    from src.core.world.regions import Region
    from src.core.world.resource_nodes import ResourceNode
    from src.core.models.world_state import WorldState

_SPATIAL_CELL = 16  # cell size for snapshot spatial index


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Read-only view of the world, safe to share across threads.

    Uses deep-copied entities and a MappingProxyType for the entity dict
    to enforce immutability at runtime.
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
    # Strategic State (Milestone 11)
    region_control: Mapping[str, float] = field(default_factory=dict)
    war_status: Mapping[int, bool] = field(default_factory=dict)
    faction_aggression: Mapping[int, float] = field(default_factory=dict)
    _spatial: dict = field(default_factory=dict, repr=False, compare=False)
    _spatial_ground: dict = field(default_factory=dict, repr=False, compare=False)

    @property
    def world_day(self) -> int:
        return self.tick // 100

    @classmethod
    def from_world(cls, world: WorldState) -> Snapshot:
        copied_entities = {eid: e.copy() for eid, e in world.entities.items()}
        copied_ground = {k: list(v) for k, v in world.ground_items.items()}
        
        # Build lightweight spatial index for fast neighbor queries
        spatial: dict[tuple[int, int], list[int]] = defaultdict(list)
        for eid, e in copied_entities.items():
            if e.combat.hp > 0 and e.kind != "generator":
                spatial[(e.spatial.pos.x // _SPATIAL_CELL, e.spatial.pos.y // _SPATIAL_CELL)].append(eid)
                
        # NEW: Spatial index for ground items to avoid O(N_ground) scans
        spatial_ground: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
        for pos_key, items in copied_ground.items():
            if items:
                # Key is (gx, gy)
                spatial_ground[(pos_key[0] // _SPATIAL_CELL, pos_key[1] // _SPATIAL_CELL)].append(pos_key)
                
        return cls(
            tick=world.tick,
            seed=world.seed,
            entities=copied_entities,
            grid=world.grid,
            ground_items=copied_ground,
            camps=tuple((c.x, c.y) for c in world.camps),
            buildings=tuple(world.buildings),
            resource_nodes=tuple(n.copy() for n in world.resource_nodes.values()),
            treasure_chests=tuple(c.copy() for c in world.treasure_chests.values()),
            regions=tuple(r.copy() for r in world.regions),
            region_control=dict(world.region_control),
            war_status=dict(world.war_status),
            faction_aggression=dict(world.faction_aggression),
            _spatial=dict(spatial),
            _spatial_ground=dict(spatial_ground),
        )

    def __post_init__(self):
        """Finalize immutability by wrapping collections (AOA Phase 5)."""
        object.__setattr__(self, 'entities', MappingProxyType(dict(self.entities)))
        object.__setattr__(self, 'ground_items', MappingProxyType(dict(self.ground_items)))
        object.__setattr__(self, 'region_control', MappingProxyType(dict(self.region_control)))
        object.__setattr__(self, 'war_status', MappingProxyType(dict(self.war_status)))
        object.__setattr__(self, 'faction_aggression', MappingProxyType(dict(self.faction_aggression)))

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
