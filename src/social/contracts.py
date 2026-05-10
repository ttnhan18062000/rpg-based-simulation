
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from src.core.strategic import ContractState, ContractKind, ContractStatus, RiskLevel, DirectiveKind, DirectivePriority
from src.core.updates import StrategicUpdate, SocialBondUpdate, EntityUpdate, StateUpdate, SocialUpdate
from dataclasses import replace

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState

class ContractService:
    """
    Manages the creation, acceptance, and termination of social contracts.
    """

    @staticmethod
    def create_loan_contract(
        contract_id: str,
        source_id: int,
        target_id: int,
        amount: int,
        interest_rate: float = 0.1,
        duration_ticks: int = 500,
        tick: int = 0
    ) -> ContractState:
        return ContractState(
            id=contract_id,
            kind=ContractKind.LOAN,
            source_id=source_id,
            target_id=target_id,
            terms={
                "amount": amount,
                "interest_rate": interest_rate,
                "total_due": int(amount * (1 + interest_rate)),
                "duration": duration_ticks
            },
            status=ContractStatus.OFFERED,
            created_tick=tick,
            expiry_tick=tick + 10 # Offers expire quickly
        )

    @staticmethod
    def create_recruitment_contract(
        contract_id: str,
        source_id: int,
        target_id: int,
        daily_pay: int = 10,
        duration_ticks: int = 100,
        risk_level: RiskLevel = RiskLevel.NORMAL,
        tick: int = 0
    ) -> ContractState:
        return ContractState(
            id=contract_id,
            kind=ContractKind.RECRUITMENT,
            source_id=source_id,
            target_id=target_id,
            terms={
                "daily_pay": daily_pay,
                "duration": duration_ticks,
                "risk_level": risk_level
            },
            status=ContractStatus.OFFERED,
            created_tick=tick,
            expiry_tick=tick + 10 # Offers expire quickly
        )

    @staticmethod
    def accept_contract(
        entity: EntityState,
        contract_id: str,
        tick: int
    ) -> StrategicUpdate:
        """
        Transition an OFFERED contract to ACTIVE.
        """
        from src.systems.social_contract import SocialContractSystem
        strat_up, _ = SocialContractSystem.transition_contract(
            entity, contract_id, ContractStatus.ACTIVE, tick
        )
        return strat_up

    @staticmethod
    def resolve_contract_outcome(
        entity: EntityState,
        contract_id: str,
        success: bool,
        betrayal: bool = False,
        betrayer_id: Optional[int] = None,
        tick: int = 0
    ) -> Tuple[StrategicUpdate, List[SocialUpdate]]:
        """
        Resolve an ACTIVE contract and update social relationships.
        Part 1 §Social: Breaking/honoring contracts has persistent consequences.
        """
        from src.systems.social_contract import SocialContractSystem
        
        contract = entity.strategic.contracts.get(contract_id)
        if not contract:
            return StrategicUpdate(), []

        status = ContractStatus.FULFILLED if success else ContractStatus.FAILED
        if betrayal:
            status = ContractStatus.BETRAYED
        strat_up, social_up = SocialContractSystem.transition_contract(entity, contract_id, status, tick)
        if not strat_up.contracts_add_or_update:
            # Transition rejected
            return StrategicUpdate(), []
            
        # Social Consequences (Emitted by System)
        if not social_up:
             return strat_up, []
             
        social_updates = [social_up]
        
        # Part 1 §Social: Both parties get updates
        other_id = contract.target_id if contract.source_id == entity.id else contract.source_id
        
        # If betrayal, victim gets a specialized update
        if betrayal and betrayer_id is not None:
            # We already have the update for 'entity' (which might be betrayer or victim)
            # If entity is betrayer, generate update for victim.
            # If entity is victim, generate update for betrayer.
            
            victim_id = contract.target_id if contract.source_id == betrayer_id else contract.source_id
            
            # The 'social_up' from transition_contract is tied to 'entity'.
            # We need to make sure 'notoriety_delta' and 'betrayal_increment' are only on betrayer.
            if entity.id == betrayer_id:
                # social_up is for betrayer. Keep notoriety and betrayal_increment.
                # Generate victim update.
                victim_social = SocialUpdate(
                    bond_updates=[SocialBondUpdate(target_id=betrayer_id, sentiment_delta=-1.0, familiarity_delta=0.1)],
                    notoriety_delta=0.1 # Victim notoriety from associated failure
                )
                social_updates = [social_up, victim_social]
            else:
                # entity is victim. social_up should NOT have betrayal_increment/high notoriety.
                # We need to fix social_up and generate betrayer update.
                victim_social = replace(social_up, notoriety_delta=0.1, betrayal_increment=0)
                betrayer_social = SocialUpdate(
                    bond_updates=[SocialBondUpdate(target_id=entity.id, sentiment_delta=-1.0, familiarity_delta=0.1)],
                    notoriety_delta=0.5,
                    betrayal_increment=1
                )
                social_updates = [victim_social, betrayer_social]
        else:
            # Normal success/failure: Both parties get similar bond updates
            other_id = contract.target_id if contract.source_id == entity.id else contract.source_id
            # Generate update for the OTHER party regarding 'entity'
            other_social = SocialUpdate(
                bond_updates=[SocialBondUpdate(
                    target_id=entity.id, 
                    sentiment_delta=0.2 if success else -0.1, 
                    familiarity_delta=0.1
                )]
            )
            social_updates = [social_up, other_social]
        
        # Strategic consequences (Betrayal -> Avenge Directive and Turning Point)
        if betrayal and betrayer_id:
            from src.core.strategic import DirectiveState, DirectiveKind, DirectivePriority, TurningPointState, TurningPointKind
            
            avenge_directive = DirectiveState(
                id=f"avenge_{contract.id}",
                kind=DirectiveKind.COMBAT,
                target=str(betrayer_id),
                priority=DirectivePriority.HIGH,
                salience=0.5
            )
            
            betrayal_tp = TurningPointState(
                id=f"betrayal_{contract.id}_{tick}",
                kind=TurningPointKind.BETRAYAL,
                subject_id=betrayer_id,
                salience=0.8,
                tick=tick
            )
            
            strat_up = replace(strat_up, 
                directives_add_or_update=[avenge_directive],
                turning_points_add=[betrayal_tp]
            )
        
        return strat_up, social_updates


    @staticmethod
    def process_active_contracts(
        state: AuthoritativeState,
        update: StateUpdate
    ) -> StateUpdate:
        """
        Processes ACTIVE contracts for expiration or completion.
        Part 1 §Social: Completed/failed contract dissolves party.
        """
        refined_entity_updates = dict(update.entity_updates)
        current_tick = state.tick
        
        for e_id, entity in state.entities.items():
            for c_id, contract in entity.strategic.contracts.items():
                if contract.status == ContractStatus.ACTIVE:
                    # Expiration check
                    if contract.expiry_tick != -1 and current_tick > contract.expiry_tick:
                        # Auto-complete or fail based on context (default: success if recruitment expires)
                        strat_up, bond_ups = ContractService.resolve_contract_outcome(entity, c_id, success=True, tick=current_tick)
                        
                        ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                        
                        # Merge strategic update
                        my_social_up = bond_ups[0] if bond_ups else SocialUpdate()
                        
                        # Merge updates
                        merged_strat = ent_upd.strategic.merge(strat_up) if ent_upd.strategic else strat_up
                        merged_social = ent_upd.social.merge(my_social_up) if ent_upd.social else my_social_up
                        
                        refined_entity_updates[e_id] = replace(ent_upd,
                            strategic=merged_strat,
                            social=merged_social
                        )
                        
        return replace(update, entity_updates=refined_entity_updates)
    @staticmethod
    def reap_expired_offers(
        state: AuthoritativeState,
        update: StateUpdate
    ) -> StateUpdate:
        """
        Reap any OFFERED contracts that have passed their expiry_tick.
        """
        refined_entity_updates = dict(update.entity_updates)
        current_tick = state.tick
        
        for e_id, entity in state.entities.items():
            expired_ids = []
            for c_id, contract in entity.strategic.contracts.items():
                if contract.status == ContractStatus.OFFERED and 0 < contract.expiry_tick <= current_tick:
                    expired_ids.append(c_id)
            
            if expired_ids:
                ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                strat_up = ent_upd.strategic or StrategicUpdate()
                
                # Mark as FAILED or remove
                # For now, we'll mark as FAILED to maintain history if needed, 
                # but the requirement says "cleanup".
                # We'll use contracts_remove for cleanup.
                refined_entity_updates[e_id] = replace(ent_upd,
                    strategic=replace(strat_up,
                        contracts_remove=list(strat_up.contracts_remove) + expired_ids
                    )
                )
                
        return replace(update, entity_updates=refined_entity_updates)


    @staticmethod
    def create_position_swap_contract(
        contract_id: str,
        source_id: int,
        target_id: int,
        source_from: tuple[float, float],
        target_from: tuple[float, float],
        tick: int = 0,
        expiry_ticks: int = 1,
    ) -> ContractState:
        """
        Create a short-lived contract asking another entity to swap adjacent tiles.

        LAW:
            Position swap is a consent-based movement contract. It allows two
            adjacent entities to exchange places atomically when normal corridor
            passing is impossible.

        Terms:
            source_from:
                Current position of the requester.
            source_to:
                Current position of the responder.
            target_from:
                Current position of the responder.
            target_to:
                Current position of the requester.

        The contract is intentionally short-lived because movement positions become
        stale quickly.
        """
        return ContractState(
            id=contract_id,
            kind=ContractKind.POSITION_SWAP,
            source_id=source_id,
            target_id=target_id,
            terms={
                "source_from": source_from,
                "source_to": target_from,
                "target_from": target_from,
                "target_to": source_from,
                "duration": expiry_ticks,
                "reason": "CORRIDOR_SWAP",
            },
            status=ContractStatus.OFFERED,
            created_tick=tick,
            expiry_tick=tick + expiry_ticks,
        )