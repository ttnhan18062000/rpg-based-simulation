"""Immutable snapshot of the world state for worker threads."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from src.core.buildings import Building
from src.core.grid import Grid
from src.core.items import TreasureChest
from src.core.models import Entity
from src.core.regions import Region
from src.core.resource_nodes import ResourceNode
from src.core.world_state import WorldState

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
    _spatial: dict = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_world(cls, world: WorldState) -> Snapshot:
        copied_entities = {eid: e.copy() for eid, e in world.entities.items()}
        copied_ground = {k: list(v) for k, v in world.ground_items.items()}
        # Build lightweight spatial index for fast neighbor queries
        spatial: dict[tuple[int, int], list[int]] = defaultdict(list)
        for eid, e in copied_entities.items():
            if e.stats.hp > 0 and e.kind != "generator":
                spatial[(e.pos.x // _SPATIAL_CELL, e.pos.y // _SPATIAL_CELL)].append(eid)
        return cls(
            tick=world.tick,
            seed=world.seed,
            entities=MappingProxyType(copied_entities),
            grid=world.grid,  # grid is immutable during tick processing
            ground_items=MappingProxyType(copied_ground),
            camps=tuple((c.x, c.y) for c in world.camps),
            buildings=tuple(world.buildings),
            resource_nodes=tuple(n.copy() for n in world.resource_nodes.values()),
            treasure_chests=tuple(c.copy() for c in world.treasure_chests.values()),
            regions=tuple(r.copy() for r in world.regions),
            _spatial=dict(spatial),
        )

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
