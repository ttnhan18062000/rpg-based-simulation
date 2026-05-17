# Compliance IDs: COMB-002, PERF-008
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Tuple, Optional
from src.core.enums import EntityRole

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState


@dataclass(frozen=True)
class OccupancySnapshot:
    """
    Stable per-tick read model for entity tile occupancy and tie-breaking priority.
    Logic ID: PERF-008 (Occupancy Snapshot)
    """
    tick: int
    occupancy_by_tile: Dict[Tuple[int, int], int]
    priority_by_entity: Dict[int, int]

    @classmethod
    def from_state(cls, state: AuthoritativeState) -> OccupancySnapshot:
        occ: Dict[Tuple[int, int], int] = {}
        prio: Dict[int, int] = {}

        for e_id, entity in state.entities.items():
            if entity.lifecycle.active and entity.combat.alive:
                pos = (int(entity.navigation.position[0]), int(entity.navigation.position[1]))
                occ[pos] = e_id

                base = 0
                if entity.identity.role == EntityRole.HERO:
                    base = 100
                elif entity.identity.role == EntityRole.MONSTER:
                    base = 50

                hp_ratio = (entity.combat.hp / entity.combat.max_hp) if entity.combat.max_hp > 0 else 1.0
                prio[e_id] = base + (100 if hp_ratio < 0.3 else 0)

        return cls(
            tick=state.tick,
            occupancy_by_tile=occ,
            priority_by_entity=prio,
        )

    def occupant_at(self, tile: Tuple[int, int]) -> Optional[int]:
        return self.occupancy_by_tile.get(tile)

    def is_occupied(self, tile: Tuple[int, int]) -> bool:
        return tile in self.occupancy_by_tile

    def get_priority(self, entity_id: int) -> int:
        return self.priority_by_entity.get(entity_id, 0)
