from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.core.updates import (
    EntityUpdate, NavigationUpdate, CombatUpdate, 
    LifecycleUpdate, SocialUpdate, StaminaUpdate
)

if TYPE_CHECKING:
    from src.core.state import EntityState


class CombatActions:
    """
    Domain action handlers for direct combat attacks.
    """

    @staticmethod
    def execute_attack(
        entity: EntityState,
        payload: Optional[Dict[str, Any]] = None,
        current_tick: int = 0,
        neighbor_view: List[tuple[int, EntityState]] = None,
        context: Any = None
    ) -> Dict[int, EntityUpdate]:
        """
        Handle the ATTACK action.
        """
        target_id = payload.get("target_id")
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
        
        if context:
            from src.engine.legality import LegalityServiceV2
            is_legal, reason = LegalityServiceV2.verify_attack_legality(entity, target, context)
            if not is_legal:
                return {entity.id: EntityUpdate(
                    entity_id=entity.id, 
                    readiness_delta=-50.0, 
                    navigation=NavigationUpdate(failure_reason=reason)
                )}
            
            from src.engine.combat import CombatResolutionSystem
            combat_up = CombatResolutionSystem.resolve_attack(entity, target, context)
            
            # Attacker Update: Cost + Rewards
            attacker_up = EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0,
                equipment=combat_up.attacker_equipment_upd,
                resource_transfers=combat_up.resource_transfers
            )
            
            # Check HUNT quests if target was killed
            if combat_up.alive_set is False:
                from src.engine.quests import QuestResolutionSystem
                q_updates = QuestResolutionSystem.evaluate_combat_victory(entity, target.kind, victim_entity=target)
                if q_updates:
                    merged_qu = q_updates[0]
                    for i in range(1, len(q_updates)):
                        merged_qu = merged_qu.merge(q_updates[i])
                    attacker_up = replace(attacker_up, quest=merged_qu)

            # Defender Update: Damage + Mortality
            # Phase 7: Social Consequences & Betrayal Check
            from src.core.updates import StrategicUpdate
            social_up = combat_up.social_upd or SocialUpdate()
            strat_up = StrategicUpdate()
            group_dissolve_upd = None
            
            if entity.identity.group_id is not None and entity.identity.group_id == target.identity.group_id:
                from src.systems.social_systems.appraisal import SocialAppraisalSystem
                s_up, st_up = SocialAppraisalSystem.process_betrayal(
                    target, entity.id, salience=0.8, current_tick=current_tick
                )
                # Merge s_up with social_up
                social_up = social_up.merge(s_up)
                strat_up = st_up
                group_dissolve_upd = -1 # None/Reset
            
            defender_up = EntityUpdate(
                entity_id=target.id,
                combat=combat_up,
                wound_update=combat_up.wound_update,
                social=social_up,
                strategic=strat_up if strat_up.directives_add_or_update else None,
                group_id_set=group_dissolve_upd,
                lifecycle=LifecycleUpdate(
                    age_delta=0,
                    generation_delta=combat_up.generation_delta,
                    is_permadeath_set=combat_up.is_permadeath_set
                ) if (combat_up.generation_delta != 0 or combat_up.is_permadeath_set is not None) else None
            )

            # Stamina drain on attack (Checklist Part 6 Section E)
            stamina_cost = 5.0 # Standard attack cost
            attacker_up = replace(attacker_up, stamina_update=StaminaUpdate(current_delta=-stamina_cost))

            # TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER (Sec 13.5a): combat is a real,
            # second information source, better than passive observation -- both real participants
            # of this exchange update their own OpponentModel from the real outcome, per the
            # declared mapping (docs/mechanics/04_strategic_cognition.md Sec 13.5a). Neither read
            # depends on the other having run first (order-independent by construction).
            from src.domains.combat_engagement.learning_outcome import apply_combat_learning
            new_attacker_cognition, new_defender_cognition = apply_combat_learning(
                entity, target, combat_up.outcome_kind, combat_up.damage_taken, current_tick,
            )
            if new_attacker_cognition is not None:
                attacker_up = replace(attacker_up, cognition_bundle_set=new_attacker_cognition)
            if new_defender_cognition is not None:
                defender_up = replace(defender_up, cognition_bundle_set=new_defender_cognition)

            return {entity.id: attacker_up, target.id: defender_up}
            
        return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=0.0)}
