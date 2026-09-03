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
    def execute_team_up(
        entity: EntityState,
        payload: Dict[str, Any],
        current_tick: int,
        neighbor_view: List[tuple[int, EntityState]],
        context: Any
    ) -> Dict[int, EntityUpdate]:
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
                navigation=NavigationUpdate(failure_reason="TARGET_NOT_FOUND")
            )}

        from src.systems.social_systems.appraisal import SocialAppraisalSystem
        from src.core.strategic import ContractState, ContractKind, ContractStatus
        from src.core.updates import SocialUpdate, StrategicUpdate

        temp_contract = ContractState(
            id="temp_eval",
            kind=ContractKind.TEAM_UP,
            source_id=entity.id,
            target_id=target.id,
            terms={"risk_level": payload.get("risk_level", "NORMAL")},
            status=ContractStatus.OFFERED,
            created_tick=current_tick
        )
        status, reason, _ = SocialAppraisalSystem.appraise_contract(target, temp_contract, context)

        if status == ContractStatus.ACCEPTED:
            contract_id = f"contract_team_up_{entity.id}_{target_id}_{current_tick}"
            contract = ContractState(
                id=contract_id,
                kind=ContractKind.TEAM_UP,
                source_id=entity.id,
                target_id=target_id,
                status=ContractStatus.ACTIVE,
                terms={"risk_level": payload.get("risk_level", "NORMAL")}
            )

            attacker_up = EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0,
                strategic=StrategicUpdate(contracts_add_or_update=[contract])
            )
            target_up = EntityUpdate(
                entity_id=target_id,
                social=SocialUpdate(last_offer_tick_set=current_tick),
                strategic=StrategicUpdate(contracts_add_or_update=[contract])
            )
            return {entity.id: attacker_up, target_id: target_up}
        else:
            attacker_up = EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-50.0,
                task=replace(entity.task, payload={**payload, "outcome": "FAILURE", "reason": status.value})
            )
            target_up = EntityUpdate(
                entity_id=target_id,
                social=SocialUpdate(rejection_increment={entity.id: 1}, last_offer_tick_set=current_tick)
            )
            return {entity.id: attacker_up, target_id: target_up}

    @staticmethod
    def execute_trade(
        entity: EntityState,
        payload: Dict[str, Any],
        current_tick: int,
        neighbor_view: List[tuple[int, EntityState]],
        context: Any
    ) -> Dict[int, EntityUpdate]:
        target_id = payload.get("target_id")
        price = payload.get("price", 0)
        item_value = payload.get("item_value", price)
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
        from src.core.updates import SocialUpdate, StrategicUpdate

        temp_contract = ContractState(
            id="temp_eval",
            kind=ContractKind.MERCHANT,
            source_id=entity.id,
            target_id=target.id,
            terms={"price": price, "item_value": item_value},
            status=ContractStatus.OFFERED,
            created_tick=current_tick
        )
        status, reason, _ = SocialAppraisalSystem.appraise_contract(target, temp_contract, context)

        if status == ContractStatus.ACCEPTED:
            contract_id = f"contract_trade_{entity.id}_{target_id}_{current_tick}"
            contract = ContractState(
                id=contract_id,
                kind=ContractKind.MERCHANT,
                source_id=entity.id,
                target_id=target_id,
                status=ContractStatus.ACTIVE,
                terms={"price": price, "item_value": item_value}
            )

            attacker_up = EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0,
                strategic=StrategicUpdate(contracts_add_or_update=[contract])
            )
            target_up = EntityUpdate(
                entity_id=target_id,
                social=SocialUpdate(last_offer_tick_set=current_tick),
                strategic=StrategicUpdate(contracts_add_or_update=[contract])
            )
            return {entity.id: attacker_up, target_id: target_up}
        else:
            attacker_up = EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-50.0,
                task=replace(entity.task, payload={**payload, "outcome": "FAILURE", "reason": status.value})
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
        current_tick: int,
        neighbor_view: List[tuple[int, EntityState]],
        context: Any
    ) -> Dict[int, EntityUpdate]:
        skill_id = payload.get("skill_id")
        if not skill_id:
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(failure_reason="MISSING_SKILL_ID")
            )}

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
                navigation=NavigationUpdate(failure_reason="TARGET_NOT_FOUND")
            )}

        from src.systems.social_systems.appraisal import SocialAppraisalSystem
        from src.core.strategic import ContractState, ContractKind, ContractStatus
        from src.core.updates import SocialUpdate, StrategicUpdate

        temp_contract = ContractState(
            id="temp_eval",
            kind=ContractKind.TEACH,
            source_id=entity.id,
            target_id=target.id,
            terms={},
            status=ContractStatus.OFFERED,
            created_tick=current_tick
        )
        status, reason, _ = SocialAppraisalSystem.appraise_contract(target, temp_contract, context)

        if status == ContractStatus.ACCEPTED:
            resolved_blockers = []
            for b_id, b in target.strategic.blockers.items():
                if b.kind == "capability" and b.subject == skill_id:
                    resolved_blockers.append(b_id)

            teacher_up = EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0
            )
            student_up = EntityUpdate(
                entity_id=target_id,
                identity=IdentityUpdate(recipes_learned=[skill_id]),
                strategic=StrategicUpdate(blockers_remove=resolved_blockers)
            )
            return {entity.id: teacher_up, target_id: student_up}
        else:
            attacker_up = EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-50.0,
                task=replace(entity.task, payload={**payload, "outcome": "FAILURE", "reason": status.value})
            )
            target_up = EntityUpdate(
                entity_id=target_id,
                social=SocialUpdate(rejection_increment={entity.id: 1}, last_offer_tick_set=current_tick)
            )
            return {entity.id: attacker_up, target_id: target_up}

    @staticmethod
    def execute_propose_marriage(
        entity: EntityState,
        payload: Dict[str, Any],
        current_tick: int,
        neighbor_view: List[tuple[int, EntityState]],
        context: Any
    ) -> Dict[int, EntityUpdate]:
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
                navigation=NavigationUpdate(failure_reason="TARGET_NOT_FOUND")
            )}

        from src.systems.social_systems.appraisal import SocialAppraisalSystem
        from src.core.strategic import ContractState, ContractKind, ContractStatus, MarriageState, MarriageStatus
        from src.core.updates import SocialUpdate, StrategicUpdate

        temp_contract = ContractState(
            id="temp_eval",
            kind=ContractKind.MARRIAGE,
            source_id=entity.id,
            target_id=target.id,
            terms={},
            status=ContractStatus.OFFERED,
            created_tick=current_tick
        )
        status, reason, _ = SocialAppraisalSystem.appraise_contract(target, temp_contract, context)

        if status == ContractStatus.ACCEPTED:
            marriage_record = MarriageState(
                id=f"marriage_{entity.id}_{target_id}_{current_tick}",
                proposer_entity_id=entity.id,
                target_entity_id=target_id,
                status=MarriageStatus.ACCEPTED,
                married_tick=current_tick
            )
            proposer_up = EntityUpdate(
                entity_id=entity.id,
                strategic=StrategicUpdate(marriages_add_or_update=[marriage_record])
            )
            target_up = EntityUpdate(
                entity_id=target_id,
                strategic=StrategicUpdate(marriages_add_or_update=[marriage_record])
            )
            return {entity.id: proposer_up, target_id: target_up}
        else:
            proposer_up = EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-50.0,
                task=replace(entity.task, payload={**payload, "outcome": "FAILURE", "reason": status.value})
            )
            target_up = EntityUpdate(
                entity_id=target_id,
                social=SocialUpdate(rejection_increment={entity.id: 1}, last_offer_tick_set=current_tick)
            )
            return {entity.id: proposer_up, target_id: target_up}

    @staticmethod
    def execute_join_clan(
        entity: EntityState,
        payload: Dict[str, Any],
        current_tick: int,
        neighbor_view: List[tuple[int, EntityState]],
        context: Any
    ) -> Dict[int, EntityUpdate]:
        """
        Decides whether a join offer is ACCEPTED via appraise_contract() (the
        target Clan's leader appraises the joining entity -- same "target
        appraises source" direction as execute_propose_marriage). The durable
        membership write does NOT happen here: ActionRouter.execute_action is
        contractually locked to Dict[int, EntityUpdate], which cannot carry a
        registry-level ClanUpdate. ClanLifecyclePhase (a separate pipeline
        phase, run after action_routing) reads this handler's SUCCESS/FAILURE
        outcome -- annotated automatically onto task.payload_set by
        ActionRoutingPhase.route() -- and performs the actual ClanUpdate write.
        """
        clan_id = payload.get("clan_id")
        clan = context.clans.get(clan_id) if context and hasattr(context, "clans") else None
        if not clan or clan.dissolved_tick is not None:
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(failure_reason="TARGET_NOT_FOUND")
            )}
        if entity.id in clan.member_entity_ids:
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(failure_reason="ALREADY_MEMBER")
            )}

        leader = context.entities.get(clan.leader_entity_id) if clan.leader_entity_id is not None else None
        if leader is None:
            from src.core.enums import ReasonCode
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(failure_reason=ReasonCode.TARGET_INVALID.value)
            )}

        from src.systems.social_systems.appraisal import SocialAppraisalSystem
        from src.core.strategic import ContractState, ContractKind, ContractStatus

        temp_contract = ContractState(
            id=f"clan_join_{entity.id}_{clan_id}_{current_tick}",
            kind=ContractKind.CLAN,
            source_id=entity.id,
            target_id=leader.id,
            terms={"clan_id": clan_id},
            status=ContractStatus.OFFERED,
            created_tick=current_tick,
        )
        status, reason, _ = SocialAppraisalSystem.appraise_contract(leader, temp_contract, context)

        if status == ContractStatus.ACCEPTED:
            return {entity.id: EntityUpdate(entity_id=entity.id)}

        return {entity.id: EntityUpdate(
            entity_id=entity.id,
            navigation=NavigationUpdate(failure_reason=reason.value)
        )}

    @staticmethod
    def execute_leave_clan(
        entity: EntityState,
        payload: Dict[str, Any],
        current_tick: int,
        neighbor_view: List[tuple[int, EntityState]],
        context: Any
    ) -> Dict[int, EntityUpdate]:
        """
        No appraisal gate -- leaving a Clan is unconditional. As with
        execute_join_clan, the durable ClanUpdate write happens in
        ClanLifecyclePhase, not here.
        """
        clan_id = payload.get("clan_id")
        clan = context.clans.get(clan_id) if context and hasattr(context, "clans") else None
        if not clan or entity.id not in clan.member_entity_ids:
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(failure_reason="NOT_A_MEMBER")
            )}

        return {entity.id: EntityUpdate(entity_id=entity.id)}

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
