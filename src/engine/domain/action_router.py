from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.core.updates import EntityUpdate, NavigationUpdate
from src.engine.domain.combat_actions import CombatActions
from src.engine.domain.skill_actions import SkillActions
from src.engine.domain.aoe_actions import AoeActions
from src.engine.domain.core_actions import CoreActions

if TYPE_CHECKING:
    from src.core.state import EntityState


class ActionRouter:
    """
    Routes action payloads to specific domain handlers.
    """

    @staticmethod
    def execute_action(
        entity: EntityState,
        payload: Optional[Dict[str, Any]] = None,
        current_tick: int = 0,
        neighbor_view: List[tuple[int, EntityState]] = None,
        context: Any = None
    ) -> Dict[int, EntityUpdate]:
        """
        Routes the action to the correct handler.
        """
        action = payload.get("action") if payload else None

        # Survival actions (biological necessities) bypass combat readiness.
        if action in ("SLEEP", "EAT", "REST"):
            return CoreActions.execute_survival(entity, action, current_tick)

        # 0. Readiness Check (combat/skill actions only)
        from src.engine.legality import LegalityServiceV2
        ready, r_reason = LegalityServiceV2.verify_readiness(entity)
        if not ready:
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(failure_reason=r_reason)
            )}

        if action == "RECRUIT":
            return CoreActions.execute_recruit(entity, payload, current_tick, neighbor_view, context)

        if action == "TEAM_UP":
            return CoreActions.execute_team_up(entity, payload, current_tick, neighbor_view, context)

        if action == "TRADE":
            return CoreActions.execute_trade(entity, payload, current_tick, neighbor_view, context)

        if action == "ALLOCATE_AP":
            return CoreActions.execute_allocate_ap(entity, payload)
            
        if action == "TRAIN":
            return CoreActions.execute_train(entity, payload, current_tick, neighbor_view, context)

        if action == "PROPOSE_MARRIAGE":
            return CoreActions.execute_propose_marriage(entity, payload, current_tick, neighbor_view, context)

        if action == "JOIN_CLAN":
            return CoreActions.execute_join_clan(entity, payload, current_tick, neighbor_view, context)

        if action == "LEAVE_CLAN":
            return CoreActions.execute_leave_clan(entity, payload, current_tick, neighbor_view, context)

        if action == "REPAIR":
            return CoreActions.execute_repair(entity, current_tick)
            
        if action == "INTERACT":
            return CoreActions.execute_interact(entity, payload)
            
        if action == "ATTACK":
            return CombatActions.execute_attack(entity, payload, current_tick, neighbor_view, context)
            
        if action == "SKILL":
            return SkillActions.execute_skill(entity, payload, current_tick, neighbor_view, context)
            
        if action == "AOE_ATTACK":
            return AoeActions.execute_aoe_attack(entity, payload, current_tick, neighbor_view, context)
            
        return {entity.id: EntityUpdate(
            entity_id=entity.id,
            readiness_delta=0.0
        )}
