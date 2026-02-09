"""Immutable snapshot of the world state for worker threads."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from src.core.buildings import Building
from src.core.grid import Grid
from src.core.items import TreasureChest
from src.core.models import Entity
from src.core.resource_nodes import ResourceNode
from src.core.world_state import WorldState


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

    @classmethod
    def from_world(cls, world: WorldState) -> Snapshot:
        copied_entities = {eid: e.copy() for eid, e in world.entities.items()}
        copied_ground = {k: list(v) for k, v in world.ground_items.items()}
        return cls(
            tick=world.tick,
            seed=world.seed,
            entities=MappingProxyType(copied_entities),
            grid=world.grid.copy(),
            ground_items=MappingProxyType(copied_ground),
            camps=tuple((c.x, c.y) for c in world.camps),
            buildings=tuple(world.buildings),
            resource_nodes=tuple(n.copy() for n in world.resource_nodes.values()),
            treasure_chests=tuple(c.copy() for c in world.treasure_chests.values()),
        )
