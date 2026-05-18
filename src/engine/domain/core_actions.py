from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.core.updates import (
    BiologicalUpdate, EntityUpdate, IdentityUpdate, 
    InteractionUpdate, NavigationUpdate, StaminaUpdate
)

if TYPE_CHECKING:
    from src.core.state import EntityState


class CoreActions:
    """
    Domain action handlers for fundamental RPG actions.
    """

    @staticmethod
    def execute_survival(
        entity: EntityState,
        action: str,
        current_tick: int
    ) -> Dict[int, EntityUpdate]:
        if action == "SLEEP":
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0,
                biological=BiologicalUpdate(
                    sleep_debt_delta=-20.0,
                    rest_pressure_delta=-10.0,
                    last_sleep_tick_set=current_tick
                )
            )}
        elif action == "EAT":
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0,
                biological=BiologicalUpdate(
                    hunger_delta=-40.0,
                    last_meal_tick_set=current_tick
                )
            )}
        elif action == "REST":
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                readiness_delta=0.0,
                biological=BiologicalUpdate(
                    rest_pressure_delta=-30.0
                )
            )}
        return {}

    @staticmethod
    def execute_recruit(
        entity: EntityState,
        payload: Dict[str, Any],
        current_tick: int,
        neighbor_view: List[tuple[int, EntityState]],
        context: Any
    ) -> Dict[int, EntityUpdate]:
        target_id = payload.get("target_id")
        payout = payload.get("payout", 100)
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
                navigation=NavigationUpdate(failure_reason="TARGET_NOT_FOUND")
            )}
        
        from src.systems.social_systems.appraisal import SocialAppraisalSystem
        from src.core.strategic import ContractState, ContractKind, ContractStatus
        from src.core.updates import ResourceTransferIntent, SocialUpdate, StrategicUpdate
        
        # Evaluate offer using consolidated appraisal logic
        temp_contract = ContractState(
            id="temp_eval",
            kind=ContractKind.RECRUITMENT,
            source_id=entity.id,
            target_id=target.id,
            terms={"daily_pay": payout, "risk_level": "NORMAL"},
            status=ContractStatus.OFFERED,
            created_tick=current_tick
        )
        status, reason, _ = SocialAppraisalSystem.appraise_contract(target, temp_contract, context)
        
        if status == ContractStatus.ACCEPTED:
            contract_id = f"contract_recruit_{entity.id}_{target_id}_{current_tick}"
            contract = ContractState(
                id=contract_id,
                kind=ContractKind.RECRUITMENT,
                source_id=entity.id,
                target_id=target_id,
                status=ContractStatus.ACTIVE,
                terms={"payout": payout}
            )
            
            group_id = f"recruit_{entity.id}_{target_id}_{current_tick}"
            
            attacker_up = EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0,
                resource_transfers=[ResourceTransferIntent(
                    source_id=target_id,
                    source_kind="RECRUIT",
                    gold_delta=-payout,
                    group_id=group_id,
                    transfer_kind="RECRUITMENT",
                    strategic_upd=StrategicUpdate(contracts_add_or_update=[contract])
                )]
            )
            target_up = EntityUpdate(
                entity_id=target_id,
                social=SocialUpdate(last_offer_tick_set=current_tick),
                resource_transfers=[ResourceTransferIntent(
                    source_id=entity.id,
                    source_kind="RECRUIT",
                    gold_delta=payout,
                    group_id=group_id,
                    transfer_kind="RECRUITMENT",
                    strategic_upd=StrategicUpdate(contracts_add_or_update=[contract])
                )]
            )
            return {entity.id: attacker_up, target_id: target_up}
        else:
            attacker_up = EntityUpdate(
                entity_id=entity.id, 
                readiness_delta=-50.0, 
                task=replace(entity.task, payload={**payload, "outcome": "FAILURE", "reason": "REJECTED"})
            )
            target_up = EntityUpdate(
                entity_id=target_id,
                social=SocialUpdate(rejection_increment={entity.id: 1}, last_offer_tick_set=current_tick)
            )
            return {entity.id: attacker_up, target_id: target_up}

    @staticmethod
    def execute_allocate_ap(
        entity: EntityState,
        payload: Dict[str, Any]
    ) -> Dict[int, EntityUpdate]:
        attr_name = payload.get("attribute")
        amount = payload.get("amount", 1)
        
        if entity.identity.unspent_ap < amount:
            return {entity.id: EntityUpdate(
                entity_id=entity.id, 
                navigation=NavigationUpdate(failure_reason="INSUFFICIENT_AP")
            )}
        
        from src.core.updates import AttributeUpdate, CombatUpdate
        attr_up = AttributeUpdate()
        combat_up = CombatUpdate()
        
        if attr_name == "strength":
            attr_up = replace(attr_up, strength_delta=amount)
            combat_up = replace(combat_up, atk_delta=amount * 2)
        elif attr_name == "vitality":
            attr_up = replace(attr_up, vitality_delta=amount)
            combat_up = replace(combat_up, max_hp_delta=amount * 10, hp_delta=amount * 10)
        
        return {entity.id: EntityUpdate(
            entity_id=entity.id,
            identity=IdentityUpdate(unspent_ap_delta=-amount),
            attributes=attr_up,
            combat=combat_up
        )}

    @staticmethod
    def execute_train(
        entity: EntityState,
        payload: Dict[str, Any],
        current_tick: int
    ) -> Dict[int, EntityUpdate]:
        skill_id = payload.get("skill_id")
        if not skill_id:
            return {entity.id: EntityUpdate(
                entity_id=entity.id, 
                navigation=NavigationUpdate(failure_reason="MISSING_SKILL_ID")
            )}
        
        TRAIN_COST = 50
        from src.core.updates import ResourceTransferIntent, StrategicUpdate
        
        resolved_blockers = []
        for b_id, b in entity.strategic.blockers.items():
            if b.kind == "capability" and b.subject == skill_id:
                resolved_blockers.append(b_id)

        intent = ResourceTransferIntent(
            source_id="CLASS_HALL",
            source_kind="TOWN_SERVICE",
            gold_delta=-TRAIN_COST,
            transfer_kind="TRAIN",
            is_group_required=True,
            identity_upd=IdentityUpdate(recipes_learned=[skill_id]),
            strategic_upd=StrategicUpdate(blockers_remove=resolved_blockers)
        )
        
        return {entity.id: EntityUpdate(
            entity_id=entity.id,
            readiness_delta=-100.0,
            resource_transfers=[intent]
        )}

    @staticmethod
    def execute_repair(
        entity: EntityState,
        current_tick: int
    ) -> Dict[int, EntityUpdate]:
        total_cost = 0
        repair_deltas = {}
        for slot, dur in entity.equipment.durability.items():
            if dur < 100.0:
                cost = int((100.0 - dur) * 0.5)
                total_cost += cost
                repair_deltas[slot] = 100.0
        
        if not repair_deltas:
            return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-10.0)}
            
        from src.core.updates import EquipmentUpdate, ResourceTransferIntent
        intent = ResourceTransferIntent(
            source_id="BLACKSMITH",
            source_kind="TOWN_SERVICE",
            gold_delta=-total_cost,
            gold_cost=total_cost,
            transfer_kind="REPAIR",
            equipment_upd=EquipmentUpdate(durability_set=repair_deltas)
        )
        
        return {entity.id: EntityUpdate(
            entity_id=entity.id,
            readiness_delta=-100.0,
            resource_transfers=[intent]
        )}

    @staticmethod
    def execute_interact(
        entity: EntityState,
        payload: Dict[str, Any]
    ) -> Dict[int, EntityUpdate]:
        target_id = payload.get("target_id")
        return {entity.id: EntityUpdate(
            entity_id=entity.id,
            readiness_delta=-100.0,
            interaction=InteractionUpdate(target_node_id=target_id, progress_delta=1)
        )}
