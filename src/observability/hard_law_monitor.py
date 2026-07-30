from __future__ import annotations
import math
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from src.core.state import AuthoritativeState
from src.core.dirty import DirtySet
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.engine.kernel import Kernel

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HardLawViolation:
    """
    Standard schema for a hard simulation law violation.
    """
    law_id: str
    entity_id: int
    severity: str  # "ERROR" or "WARNING"
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


class HardLawViolationError(Exception):
    """
    Exception raised when hard law violations occur in fail-fast modes (DEBUG, CERTIFICATION).
    """
    def __init__(self, violations: List[HardLawViolation]):
        self.violations = violations
        violation_messages = [
            f"  - [{v.severity}] {v.law_id} on entity {v.entity_id}: {v.message} (details: {v.details})"
            for v in violations
        ]
        msg = "Hard Law Violations detected in authoritative state:\n" + "\n".join(violation_messages)
        super().__init__(msg)


class HardLawMonitor:
    """
    Performs lightweight, O(1)-efficient, DirtySet-scoped check execution at the end of each tick.
    """

    @staticmethod
    def check(state: AuthoritativeState, dirty_set: Optional[DirtySet]) -> List[HardLawViolation]:
        """
        Orchestrates entity state and occupancy collision checks.
        """
        violations: List[HardLawViolation] = []
        
        # 1. State Checks
        violations.extend(HardLawMonitor.check_entities(state, dirty_set))
        
        # 2. Occupancy Checks
        violations.extend(HardLawMonitor.check_occupancy(state, dirty_set))
        
        return violations

    @staticmethod
    def check_entities(state: AuthoritativeState, dirty_set: Optional[DirtySet]) -> List[HardLawViolation]:
        """
        Performs scoped attribute/property checks on dirty active and alive entities.
        """
        violations: List[HardLawViolation] = []
        if not dirty_set:
            return violations

        dirty_ids = dirty_set.all_dirty_entities
        for e_id in dirty_ids:
            entity = state.entities.get(e_id)
            if entity is None:
                continue

            # Only check if active and alive
            if not entity.lifecycle.active or not entity.combat.alive:
                continue

            # LAW-HP-NONNEGATIVE: HP must be non-negative
            if entity.combat is not None:
                if entity.combat.hp < 0:
                    violations.append(HardLawViolation(
                        law_id="LAW-HP-NONNEGATIVE",
                        entity_id=e_id,
                        severity="ERROR",
                        message=f"Entity {e_id} has negative HP: {entity.combat.hp}",
                        details={"hp": entity.combat.hp}
                    ))
                
                # LAW-READINESS-NONNEGATIVE: Readiness must be non-negative
                if entity.combat.readiness < 0:
                    violations.append(HardLawViolation(
                        law_id="LAW-READINESS-NONNEGATIVE",
                        entity_id=e_id,
                        severity="ERROR",
                        message=f"Entity {e_id} has negative readiness: {entity.combat.readiness}",
                        details={"readiness": entity.combat.readiness}
                    ))

            # LAW-GOLD-NONNEGATIVE: Gold must be non-negative
            if entity.inventory is not None:
                if entity.inventory.gold < 0:
                    violations.append(HardLawViolation(
                        law_id="LAW-GOLD-NONNEGATIVE",
                        entity_id=e_id,
                        severity="ERROR",
                        message=f"Entity {e_id} has negative gold: {entity.inventory.gold}",
                        details={"gold": entity.inventory.gold}
                    ))

            # LAW-STAMINA-NONNEGATIVE: Stamina must be non-negative
            if entity.stamina is not None:
                if entity.stamina.current < 0:
                    violations.append(HardLawViolation(
                        law_id="LAW-STAMINA-NONNEGATIVE",
                        entity_id=e_id,
                        severity="ERROR",
                        message=f"Entity {e_id} has negative stamina: {entity.stamina.current}",
                        details={"stamina": entity.stamina.current}
                    ))

            # LAW-POSITION-FINITE: Position must be finite coordinates
            if entity.navigation is not None:
                pos = entity.navigation.position
                if not (math.isfinite(pos[0]) and math.isfinite(pos[1])):
                    violations.append(HardLawViolation(
                        law_id="LAW-POSITION-FINITE",
                        entity_id=e_id,
                        severity="ERROR",
                        message=f"Entity {e_id} has non-finite position coordinates: {pos}",
                        details={"position": pos}
                    ))

        return violations

    @staticmethod
    def check_initial_placement(state: AuthoritativeState) -> List[HardLawViolation]:
        """
        Unconditional full-population placement-legality scan (entities + buildings +
        resource nodes), run once at Kernel.__init__. WorldCompiler.compile() never
        validates spawn positions, and check_occupancy() below only inspects entities
        that moved on the current tick, so nothing checks the compiled spawn state itself.

        Buildings self-register their own tile into state.blocked_tiles at compile time
        (src/worldbuilding/compiler.py), so calling verify_occupancy() against a
        building's own position always fails against itself. Buildings are therefore
        only covered by the multi-occupant tile scan below; entities and resource nodes
        carry no such self-registration and are checked directly against verify_occupancy.
        """
        from src.engine.legality import LegalityServiceV2

        objects: List[Tuple[str, int, Tuple[float, float]]] = []
        for e_id, entity in state.entities.items():
            if not entity.lifecycle.active or not entity.combat.alive:
                continue
            objects.append(("entity", e_id, entity.navigation.position))
        for b_id, building in state.buildings.items():
            objects.append(("building", b_id, building.position))
        for r_id, node in state.resource_nodes.items():
            objects.append(("resource_node", r_id, node.position))

        by_pos: Dict[Tuple[int, int], List[Tuple[str, int]]] = {}
        for kind, obj_id, pos in objects:
            tile = (int(pos[0]), int(pos[1]))
            by_pos.setdefault(tile, []).append((kind, obj_id))

        violations: List[HardLawViolation] = []
        reported_tiles: Set[Tuple[int, int]] = set()

        for tile, occupants in by_pos.items():
            if len(occupants) <= 1:
                continue
            (kind, obj_id), (other_kind, other_id) = occupants[0], occupants[1]
            reported_tiles.add(tile)
            violations.append(HardLawViolation(
                law_id="LAW-SPAWN-OCCUPANCY",
                entity_id=obj_id,
                severity="ERROR",
                message=(
                    f"Initial placement collision on tile {tile}: "
                    f"{kind} {obj_id} and {other_kind} {other_id} both occupy this space."
                ),
                details={
                    "object_kind": kind,
                    "tile": tile,
                    "colliding_object_kind": other_kind,
                    "colliding_object_id": other_id,
                }
            ))

        for kind, obj_id, pos in objects:
            if kind == "building":
                continue
            tile = (int(pos[0]), int(pos[1]))
            if tile in reported_tiles:
                continue
            ignore_id = obj_id if kind == "entity" else None
            legal, reason = LegalityServiceV2.verify_occupancy(pos, state, ignore_entity_id=ignore_id)
            if legal:
                continue
            reported_tiles.add(tile)
            violations.append(HardLawViolation(
                law_id="LAW-SPAWN-OCCUPANCY",
                entity_id=obj_id,
                severity="ERROR",
                message=f"Initial placement violation: {kind} {obj_id} at tile {tile} is illegally placed ({reason.name}).",
                details={"object_kind": kind, "tile": tile, "reason": reason.name}
            ))

        return violations

    @staticmethod
    def check_occupancy(state: AuthoritativeState, dirty_set: Optional[DirtySet]) -> List[HardLawViolation]:
        """
        Performs scoped tile collision checks on dirty moving entities.
        """
        violations: List[HardLawViolation] = []
        if not dirty_set or not dirty_set.movement_entities:
            return violations

        # Force fresh index rebuild to bypass cached start-of-tick positions
        if hasattr(state, "world_indexes"):
            try:
                delattr(state, "world_indexes")
            except AttributeError:
                pass

        # Query spatial grid index (O(1) cached lookup or quick O(N) rebuild scoped to current tick)
        indexes = Kernel.get_world_indexes(state, dirty_set)
        
        reported_tiles: Set[Tuple[int, int]] = set()
        
        for e_id in dirty_set.movement_entities:
            entity = state.entities.get(e_id)
            if entity is None or not entity.lifecycle.active or not entity.combat.alive:
                continue

            x, y = entity.navigation.position
            if not (math.isfinite(x) and math.isfinite(y)):
                continue

            pos = (int(x), int(y))
            if pos in reported_tiles:
                continue

            occupants = indexes.entities_by_tile.get(pos, ())
            if len(occupants) > 1:
                # Collision detected on this tile. Find the first other solid active alive entity.
                for occupant_id in occupants:
                    if occupant_id != e_id:
                        occ_ent = state.entities.get(occupant_id)
                        if occ_ent and occ_ent.lifecycle.active and occ_ent.combat.alive:
                            reported_tiles.add(pos)
                            violations.append(HardLawViolation(
                                law_id="LAW-OCCUPANCY-COLLISION",
                                entity_id=e_id,
                                severity="ERROR",
                                message=f"Occupancy collision on tile {pos}: entity {e_id} and entity {occupant_id} both occupy this space.",
                                details={"tile": pos, "colliding_entity_id": occupant_id}
                            ))
                            break
                            
        return violations
