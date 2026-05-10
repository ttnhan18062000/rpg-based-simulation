from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.core.enums import ReasonCode
from src.core.updates import (
    EntityUpdate, NavigationUpdate, IdentityUpdate, 
    LifecycleUpdate, StaminaUpdate
)

if TYPE_CHECKING:
    from src.core.state import EntityState


class SkillActions:
    """
    Domain action handlers for skill usage.
    """

    @staticmethod
    def execute_skill(
        entity: EntityState,
        payload: Optional[Dict[str, Any]] = None,
        current_tick: int = 0,
        neighbor_view: List[tuple[int, EntityState]] = None,
        context: Any = None
    ) -> Dict[int, EntityUpdate]:
        """
        Handle the SKILL action.
        """
        from src.core.skills import SKILL_REGISTRY
        from src.engine.rpg_depth import StaminaService, SkillScalingService
        from src.engine.combat import CombatResolutionSystem
        
        skill_id = payload.get("skill_id")
        target_id = payload.get("target_id")
        skill = SKILL_REGISTRY.get(skill_id)
        
        # 1. Skill Exists and Known?
        if not skill or skill_id not in entity.identity.learned_skills:
             return {entity.id: EntityUpdate(
                 entity_id=entity.id, 
                 readiness_delta=-10.0, 
                 navigation=NavigationUpdate(failure_reason=ReasonCode.SKILL_NOT_LEARNED)
             )}
        
        # 2. Cooldown?
        if current_tick < entity.identity.cooldowns.get(skill_id, 0):
             return {entity.id: EntityUpdate(
                 entity_id=entity.id, 
                 readiness_delta=-10.0, 
                 navigation=NavigationUpdate(failure_reason=ReasonCode.SKILL_ON_COOLDOWN)
             )}
        
        # 3. Stamina?
        if not StaminaService.can_use_skill(entity.stamina, skill.cost):
             return {entity.id: EntityUpdate(
                 entity_id=entity.id, 
                 readiness_delta=-10.0, 
                 navigation=NavigationUpdate(failure_reason=ReasonCode.ACTION_EXHAUSTION)
             )}
             
        target = None
        if neighbor_view:
            for eid, ent in neighbor_view:
                if eid == target_id:
                    target = ent
                    break
        if not target and context and hasattr(context, "entities"):
            target = context.entities.get(target_id)
        
        if not target:
             return {entity.id: EntityUpdate(
                 entity_id=entity.id, 
                 readiness_delta=-10.0, 
                 navigation=NavigationUpdate(failure_reason="TARGET_NOT_FOUND")
             )}
        
        if not target.combat.alive:
             return {entity.id: EntityUpdate(
                 entity_id=entity.id, 
                 readiness_delta=-10.0, 
                 navigation=NavigationUpdate(failure_reason=ReasonCode.TARGET_INCAPACITATED)
             )}

        # 5. Resolve
        skill_dmg = SkillScalingService.calculate_skill_damage(
            skill.power, skill.category.name, entity.attributes, base_atk=entity.combat.atk
        )
        
        combat_up = CombatResolutionSystem.resolve_skill_usage(
            entity, target, context, skill_dmg
        )
        
        if combat_up.outcome_kind == "REJECTED":
            return {
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    readiness_delta=-10.0,
                    navigation=NavigationUpdate(
                        failure_reason=combat_up.failure_reason,
                    ),
                )
            }
        
        # 6. Apply Side Effects
        next_ready_tick = current_tick + skill.cooldown
        stamina_cost = StaminaService.drain_skill(entity.stamina, skill.cost)
        
        attacker_up = EntityUpdate(
            entity_id=entity.id,
            readiness_delta=-100.0,
            identity=IdentityUpdate(cooldown_updates={skill_id: next_ready_tick}),
            stamina_update=StaminaUpdate(current_delta=-stamina_cost),
            equipment=combat_up.attacker_equipment_upd,
            resource_transfers=combat_up.resource_transfers
        )
        
        defender_up = EntityUpdate(
            entity_id=target.id,
            combat=combat_up,
            wound_update=combat_up.wound_update,
            equipment=combat_up.equipment_upd,
            lifecycle=LifecycleUpdate(
                generation_delta=combat_up.generation_delta,
                is_permadeath_set=combat_up.is_permadeath_set
            ) if (combat_up.generation_delta != 0 or combat_up.is_permadeath_set is not None) else None
        )
        
        return {entity.id: attacker_up, target.id: defender_up}
