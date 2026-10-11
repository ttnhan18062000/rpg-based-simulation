"""
src/ai/goals/opening_steps.py
───────────────────────────────────────────────────────────────────────────────
TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT

Decision 27 (SURV-07 amendment): when none of a hungry subject's ways is open to it now, the pull goes to the step that opens
one: foraging or harvesting where its kind can, earning where it has paid work and then buying, or asking where a social path
exists. Only steps the subject can actually take count. Each provider returns an `OpeningStep` that says whether it is open and,
when it is not, why, so the funnel and the inspector never read meaning from a missing value.

FORAGE is real: the nearest food node (a resource node whose yield is food) with charges left, reachable by the ordinary harvest
path, when the subject has room to carry what it gathers. EARN_THEN_BUY and ASK report unavailable until their content exists
(the shop and blacksmith town paths, and a social path), each with the reason.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from src.ai.goals.base import OpeningStepKind
from src.content_semantics.faction import get_species_id_str
from src.core.items import food_hunger_recovery
from src.core.state import AuthoritativeState, EntityState, ResourceNodeState
from src.engine.appraisal import Relation, can_eat_item
from src.engine.hostility import relation
from src.engine.rpg_depth import LeashService
from src.engine.shop_sale import nearest_sale
from src.engine.spatial_query import SpatialQueryService
from src.engine.work_shift import nearest_work


@dataclass(frozen=True)
class OpeningStep:
    """One way a need with no open way can be opened: its kind, whether it is open now, why not, and where it points."""
    kind: OpeningStepKind
    available: bool
    reason: str = ""
    target_id: Optional[str] = None
    target_entity_id: Optional[int] = None
    target_pos: Optional[Tuple[float, float]] = None


def _has_room_for(entity: EntityState, item_id: str) -> bool:
    inventory = entity.inventory
    return len(inventory.items) < inventory.max_slots or any(s.item_id == item_id for s in inventory.items)


def _forage_step(entity: EntityState, state: AuthoritativeState) -> OpeningStep:
    px, py = entity.navigation.position
    best: Optional[ResourceNodeState] = None
    best_distance = 0.0
    for node in state.resource_nodes.values():  # insertion order of the node dict is deterministic; ties keep the first
        if node.remaining_charges <= 0 or node.cooldown_remaining > 0 or food_hunger_recovery(node.yields_item) <= 0.0:
            continue
        if not LeashService.way_in_range(entity, node.position):
            continue  # a range-bound subject forages inside its range only
        if not can_eat_item(entity, node.yields_item):
            continue  # decision 44: the diet gate; a meat-only body does not forage berries
        distance = abs(node.position[0] - px) + abs(node.position[1] - py)
        if best is None or distance < best_distance:
            best, best_distance = node, distance
    if best is None:
        return OpeningStep(OpeningStepKind.FORAGE, False, "no food node with charges left")
    if not _has_room_for(entity, best.yields_item):
        return OpeningStep(OpeningStepKind.FORAGE, False, "no room to carry what it would gather")
    return OpeningStep(OpeningStepKind.FORAGE, True, target_id=str(best.id), target_pos=best.position)


# Fiction reasons: a scavenger smells carrion from farther than a hunter can track living prey; a hunt is held to the radius an entity-targeted
# objective is held to (a target beyond it ends the objective), so the two cannot disagree.
SCAVENGE_RADIUS = 20.0
HUNT_RADIUS = 10.0


def _within(entity: EntityState, position: Tuple[float, float], radius: float) -> Optional[float]:
    """The Manhattan distance to ``position`` when it is within ``radius`` and inside the entity's leash, else None.

    A territorial animal hunts and scavenges within its own range: past its leash radius the tactical pass returns it home every tick
    (LEASH_RETURN) before any objective is pursued, so a target out there could never be reached."""
    nav = entity.navigation
    if nav.leash_radius and nav.leash_radius > 0 and nav.home_position is not None:
        if abs(position[0] - nav.home_position[0]) + abs(position[1] - nav.home_position[1]) > nav.leash_radius:
            return None
    distance = abs(position[0] - nav.position[0]) + abs(position[1] - nav.position[1])
    return distance if distance <= radius else None


def _scavenge_step(entity: EntityState, state: AuthoritativeState) -> OpeningStep:
    """Decision 44: a carcass within reach holding food the subject's diet can eat, never of its own species."""
    own_species = get_species_id_str(entity)
    best, best_distance = None, 0.0
    for corpse in state.corpses.values():
        distance = _within(entity, corpse.position, SCAVENGE_RADIUS)
        if distance is None or not any(s.quantity > 0 and can_eat_item(entity, s.item_id) for s in corpse.items):
            continue
        dead = state.entities.get(corpse.original_entity_id)
        if dead is not None and get_species_id_str(dead) == own_species:
            continue
        if best is None or distance < best_distance:
            best, best_distance = corpse, distance
    if best is None:
        return OpeningStep(OpeningStepKind.SCAVENGE, False, "no carcass within reach holding food its diet can eat")
    return OpeningStep(OpeningStepKind.SCAVENGE, True, target_id=str(best.id), target_pos=best.position)


def _hunt_step(entity: EntityState, state: AuthoritativeState) -> OpeningStep:
    """Decision 44: the nearest living creature the subject appraises as PREDATION. Nothing is stored: the objective ends with its target, and the
    relation is read again at every decision, so a subject that is fed or no longer perceives the target stops hunting."""
    best, best_distance = None, 0.0
    for other_id in sorted(SpatialQueryService.nearby_entities(state, entity.navigation.position, HUNT_RADIUS)):
        other = state.entities.get(other_id)
        if other is None or other.id == entity.id or not other.combat.alive:
            continue
        if relation(entity, other) is not Relation.PREDATION:
            continue
        distance = _within(entity, other.navigation.position, HUNT_RADIUS)
        if distance is not None and (best is None or distance < best_distance):
            best, best_distance = other, distance
    if best is None:
        return OpeningStep(OpeningStepKind.HUNT, False, "no creature it can eat and believes it can overcome within reach")
    return OpeningStep(OpeningStepKind.HUNT, True, target_id=str(best.id), target_pos=best.navigation.position, target_entity_id=best.id)


def _earn_then_buy_step(entity: EntityState, state: AuthoritativeState) -> OpeningStep:
    """SELL (EXCH-02): open when the subject can spare goods a functional shop would buy (its purse covers at least one unit); its target is
    the nearest such shop. The sale happens on arrival (the SELL action), the coin comes out of the shop's own purse, and with the price of a
    meal the subject's hunger goal then points at the inn. Paid work (a wage) is not a step yet."""
    found = nearest_sale(state, entity)
    if found is not None and not LeashService.way_in_range(entity, tuple(found[0].position)):
        found = None
    if found is not None:
        shop, _sale = found
        return OpeningStep(OpeningStepKind.EARN_THEN_BUY, True, target_id=str(shop.id), target_pos=tuple(shop.position))
    inn = nearest_work(state, entity)
    if inn is not None and not LeashService.way_in_range(entity, tuple(inn.position)):
        inn = None
    if inn is None:
        return OpeningStep(OpeningStepKind.EARN_THEN_BUY, False, "nothing to sell that a shop with coin in its purse would buy, and no inn that can pay a wage")
    return OpeningStep(OpeningStepKind.EARN_THEN_BUY, True, target_id=str(inn.id), target_pos=tuple(inn.position))


def _ask_step(entity: EntityState, state: AuthoritativeState) -> OpeningStep:
    return OpeningStep(OpeningStepKind.ASK, False, "no social path to ask along exists in code")


def opening_steps(entity: EntityState, state: AuthoritativeState) -> List[OpeningStep]:
    """Every opening step, in the order they are tried (forage, scavenge, hunt, then earn-then-buy, then ask), each open or with its reason."""
    return [_forage_step(entity, state), _scavenge_step(entity, state), _hunt_step(entity, state),
            _earn_then_buy_step(entity, state), _ask_step(entity, state)]


def first_open_step(entity: EntityState, state: AuthoritativeState) -> Optional[OpeningStep]:
    """The first opening step that is open now, in the order they are tried, or None."""
    return next((step for step in opening_steps(entity, state) if step.available), None)
