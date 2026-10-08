"""CONFLICT-04 tactical emissions: the held swing between blows and the stalemate-break wander.

Pure builders of ``EntityUpdate``; they read the acting entity and the decision's already-chosen values and write nothing
(``docs/engine/contracts/tactical_contract.md`` section 5).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from src.core.movement_modes import MovementMode
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate
from src.engine.hostility import is_engaged
from src.engine.legality import LegalityServiceV2
from src.engine.tactical_destinations import retreat_destination

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState


def held_swing_update(
    state: "AuthoritativeState",
    entity: "EntityState",
    target: "EntityState",
    strat_up: Any,
    carried: Dict[str, Any],
) -> Optional[EntityUpdate]:
    """A queued ATTACK (reason ``HOLD_BETWEEN_BLOWS``) when the target is adjacent and only readiness is missing, else None.

    The scheduler skips a non-brain entity under 100 readiness, so the swing lands when readiness is back and the entity never
    steps off adjacency (no opportunity attack). Legality is checked with the readiness bypass so any other illegality still pursues.
    """
    if not LegalityServiceV2.is_adjacent(entity.navigation.position, target.navigation.position):
        return None
    if entity.combat.readiness >= 100.0:
        return None
    if not LegalityServiceV2.verify_attack_legality(entity, target, state, is_opportunity_attack=True)[0]:
        return None
    payload: Dict[str, Any] = {
        "action": "ATTACK",
        "reason": "HOLD_BETWEEN_BLOWS",
        "target_id": target.id,
        **carried,
        "stale_ticks": 0,  # the held swing is an ATTACK emission, an outcome (tactical contract section 5)
    }
    return EntityUpdate(
        entity_id=entity.id,
        strategic=strat_up,
        navigation=NavigationUpdate(target_clear=True),
        task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set=payload),
    )


def stalemate_break_update(entity: "EntityState", strat_up: Any, wander_to: Tuple[float, float]) -> EntityUpdate:
    """The STALEMATE_BREAK wander to an already-chosen, region-contained point."""
    return EntityUpdate(
        entity_id=entity.id,
        strategic=strat_up,
        navigation=NavigationUpdate(target_set=wander_to, movement_mode_set=MovementMode.WANDER),
        task=TaskUpdate(work_kind_set="ENTITY_MOVE", payload_set={"target_position": wander_to, "reason": "STALEMATE_BREAK"}),
    )


def notice_unengaged_hostile(
    state: "AuthoritativeState", entity: "EntityState", target: "EntityState", hostiles: List["EntityState"], strat_up: Any
) -> Optional[EntityUpdate]:
    """Decision 32 ("notice and decide"): the decision for an entity beside an orthogonally adjacent hostile it is not engaged with.

    It follows the entity's own combat-engagement verdict toward that target (``identity.properties["last_combat_posture"]``): ``ignore``
    keeps the walk, re-issued as an ``ENTITY_MOVE`` decision (``KEEP_WALKING``) when it has a stored target; ``avoid`` steps away
    (``AVOID_HOSTILE``, a decided flight). Any other verdict, or none, returns None and the tactical pass goes on to fight as it always has."""
    if is_engaged(entity, target) or not LegalityServiceV2.is_adjacent(entity.navigation.position, target.navigation.position):
        return None
    props = entity.identity.properties or {}
    if props.get("last_combat_posture_target") != target.id:
        return None
    posture = props.get("last_combat_posture")
    if posture == "ignore":
        goal = entity.navigation.target
        if goal is None:
            return EntityUpdate(entity_id=entity.id, strategic=strat_up)
        return EntityUpdate(
            entity_id=entity.id, strategic=strat_up,
            navigation=NavigationUpdate(target_set=goal, movement_mode_set=entity.navigation.movement_mode),
            task=TaskUpdate(work_kind_set="ENTITY_MOVE", payload_set={"target_position": goal, "reason": "KEEP_WALKING"}),
        )
    if posture == "avoid":
        away = retreat_destination(state, entity, hostiles)
        if away is None:
            return None
        return EntityUpdate(
            entity_id=entity.id, strategic=strat_up,
            navigation=NavigationUpdate(target_set=away, movement_mode_set=MovementMode.RETREAT),
            task=TaskUpdate(work_kind_set="ENTITY_MOVE", payload_set={"target_position": away, "reason": "AVOID_HOSTILE"}),
        )
    return None
