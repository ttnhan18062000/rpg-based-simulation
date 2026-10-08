"""CONFLICT-04 tactical emissions: the held swing between blows and the stalemate-break wander.

Pure builders of ``EntityUpdate``; they read the acting entity and the decision's already-chosen values and write nothing
(``docs/engine/contracts/tactical_contract.md`` section 5).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from src.core.movement_modes import MovementMode
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate
from src.engine.legality import LegalityServiceV2

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
