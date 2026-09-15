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
            
        if action in ("ATTACK", "SKILL"):
            # TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION: re-check
            # combat_engagement's own risk assessment for this exact target HERE, not only at the
            # point TacticalDecisionSystem first decided to attack -- confirmed via direct
            # instrumentation that once an entity's task is set, the scheduler re-executes it on
            # every subsequent tick (src/engine/scheduler.py's own "already ENTITY_ACT" cadence
            # optimization) WITHOUT calling evaluate_entity_intent again, so a gate placed only in
            # tactical.py's own decision point is bypassed for the vast majority (93.7% measured
            # in the reference scenario) of real attacks -- they are repeat executions of an
            # already-made decision, not fresh ones. This is the actual per-attack checkpoint.
            # Policy: only risk-ACCEPTED postures (ENGAGE/PROBE/SKIRMISH/VENGEANCE_ENGAGE)
            # proceed; every risk-rejected posture (WATCH/AVOID/PANIC_FLEE/RETREAT) and an
            # explicit IGNORE verdict withhold the attack. Absence of any recorded posture for
            # this exact target does NOT withhold it -- combat_engagement never having run
            # against this pairing (flag off, or a cold-start tick) is not a verdict. An earlier
            # version of this gate lived in tactical.py's own decision point; it was removed
            # (not just superseded) once measurement showed it caught only 6.3% of real attacks,
            # to avoid two parallel implementations of the same policy.
            _RISK_ACCEPTED_POSTURES = ("engage", "probe", "skirmish", "vengeance_engage")
            _target_id = payload.get("target_id") if payload else None
            _posture = (
                entity.identity.properties.get("last_combat_posture")
                if entity.identity.properties.get("last_combat_posture_target") == _target_id
                else None
            )
            if _posture is not None and _posture not in _RISK_ACCEPTED_POSTURES:
                return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=0.0)}

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
