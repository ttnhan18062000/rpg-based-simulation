from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.core.updates import (
    EntityUpdate, NavigationUpdate, LifecycleUpdate, StaminaUpdate
)

if TYPE_CHECKING:
    from src.core.state import EntityState


class AoeActions:
    """
    Domain action handlers for area-of-effect attacks.
    """

    @staticmethod
    def execute_aoe_attack(
        entity: EntityState,
        payload: Optional[Dict[str, Any]] = None,
        current_tick: int = 0,
        neighbor_view: List[tuple[int, EntityState]] = None,
        context: Any = None
    ) -> Dict[int, EntityUpdate]:
        """
        Handle the AOE_ATTACK action.
        """
        from src.engine.combat import CombatResolutionSystem
        target_pos = payload.get("target_pos")
        radius = payload.get("radius", 1)
        
        # Identify primary target (if any) at that position
        defender = None
        if context and hasattr(context, "entities"):
            for eid, ent in context.entities.items():
                if ent.navigation.position == target_pos and ent.combat.alive:
                    defender = ent
                    break
        
        # resolve_aoe_attack returns Dict[int, CombatUpdate] for all affected entities
        combat_updates = CombatResolutionSystem.resolve_aoe_attack(
            entity, target_pos, radius, context, defender=defender
        )
        
        attacker_combat = combat_updates.get(entity.id)
        if attacker_combat and attacker_combat.outcome_kind == "REJECTED":
            return {entity.id: EntityUpdate(
                entity_id=entity.id, 
                readiness_delta=-10.0, 
                navigation=NavigationUpdate(failure_reason=attacker_combat.failure_reason)
            )}
        
        updates = {}
        attacker_q_updates = []
        
        for eid, c_up in combat_updates.items():
            if eid == entity.id:
                # Attacker Update: Readiness + Rewards
                updates[eid] = EntityUpdate(
                    entity_id=eid,
                    readiness_delta=-100.0,
                    combat=c_up, # Holds simultaneous_intents
                    resource_transfers=c_up.resource_transfers
                )
            else:
                # Victim Update: Damage + Mortality + Durability
                updates[eid] = EntityUpdate(
                    entity_id=eid,
                    combat=c_up,
                    wound_update=c_up.wound_update,
                    equipment=c_up.equipment_upd,
                    lifecycle=LifecycleUpdate(
                        generation_delta=c_up.generation_delta,
                        is_permadeath_set=c_up.is_permadeath_set
                    ) if (c_up.generation_delta != 0 or c_up.is_permadeath_set is not None) else None
                )
                
                # Check HUNT quests if target was killed
                if c_up.alive_set is False:
                    target = (
                        context.entities.get(eid)
                        if context and hasattr(context, "entities")
                        else None
                    )

                    if target:
                        from src.engine.quests import QuestResolutionSystem

                        q_updates = QuestResolutionSystem.evaluate_combat_victory(
                            entity,
                            target.kind,
                        )

                        if q_updates:
                            attacker_q_updates.extend(q_updates)
        
        # Merge all collected quest updates for the attacker
        if attacker_q_updates and entity.id in updates:
            merged_qu = attacker_q_updates[0]
            for i in range(1, len(attacker_q_updates)):
                merged_qu = merged_qu.merge(attacker_q_updates[i])
            updates[entity.id] = replace(updates[entity.id], quest=merged_qu)
        
        # Stamina drain on AOE attack
        stamina_cost = 10.0 # AOE cost
        if entity.id in updates:
            updates[entity.id] = replace(updates[entity.id], stamina_update=StaminaUpdate(current_delta=-stamina_cost))
        
        return updates
