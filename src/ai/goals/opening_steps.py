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
from src.core.items import food_hunger_recovery
from src.core.state import AuthoritativeState, EntityState, ResourceNodeState
from src.engine.shop_sale import nearest_sale
from src.engine.work_shift import nearest_work


@dataclass(frozen=True)
class OpeningStep:
    """One way a need with no open way can be opened: its kind, whether it is open now, why not, and where it points."""
    kind: OpeningStepKind
    available: bool
    reason: str = ""
    target_id: Optional[str] = None
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
        distance = abs(node.position[0] - px) + abs(node.position[1] - py)
        if best is None or distance < best_distance:
            best, best_distance = node, distance
    if best is None:
        return OpeningStep(OpeningStepKind.FORAGE, False, "no food node with charges left")
    if not _has_room_for(entity, best.yields_item):
        return OpeningStep(OpeningStepKind.FORAGE, False, "no room to carry what it would gather")
    return OpeningStep(OpeningStepKind.FORAGE, True, target_id=str(best.id), target_pos=best.position)


def _earn_then_buy_step(entity: EntityState, state: AuthoritativeState) -> OpeningStep:
    """SELL (EXCH-02): open when the subject can spare goods a functional shop would buy (its purse covers at least one unit); its target is
    the nearest such shop. The sale happens on arrival (the SELL action), the coin comes out of the shop's own purse, and with the price of a
    meal the subject's hunger goal then points at the inn. Paid work (a wage) is not a step yet."""
    found = nearest_sale(state, entity)
    if found is not None:
        shop, _sale = found
        return OpeningStep(OpeningStepKind.EARN_THEN_BUY, True, target_id=str(shop.id), target_pos=tuple(shop.position))
    inn = nearest_work(state, entity)
    if inn is None:
        return OpeningStep(OpeningStepKind.EARN_THEN_BUY, False, "nothing to sell that a shop with coin in its purse would buy, and no inn that can pay a wage")
    return OpeningStep(OpeningStepKind.EARN_THEN_BUY, True, target_id=str(inn.id), target_pos=tuple(inn.position))


def _ask_step(entity: EntityState, state: AuthoritativeState) -> OpeningStep:
    return OpeningStep(OpeningStepKind.ASK, False, "no social path to ask along exists in code")


def opening_steps(entity: EntityState, state: AuthoritativeState) -> List[OpeningStep]:
    """Every opening step, in the order they are tried (forage, then earn-then-buy, then ask), each open or with its reason."""
    return [_forage_step(entity, state), _earn_then_buy_step(entity, state), _ask_step(entity, state)]


def first_open_step(entity: EntityState, state: AuthoritativeState) -> Optional[OpeningStep]:
    """The first opening step that is open now, in the order they are tried, or None."""
    return next((step for step in opening_steps(entity, state) if step.available), None)
