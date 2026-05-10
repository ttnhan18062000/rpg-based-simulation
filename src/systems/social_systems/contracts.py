from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import replace
from src.core.strategic import ContractState, ContractKind, ContractStatus, RiskLevel, DirectiveKind, DirectivePriority
from src.core.updates import StrategicUpdate, SocialBondUpdate, EntityUpdate, StateUpdate, SocialUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState

class SocialContractSystem:
    """
    Manages the authoritative lifecycle of social contracts.
    """

    @staticmethod
    def transition_contract(
        entity: EntityState,
        contract_id: str,
        new_status: ContractStatus,
        tick: int
    ) -> Tuple[StrategicUpdate, SocialUpdate]:
        """
        Validates and applies a state transition for a contract.
        """
        contract = entity.strategic.contracts.get(contract_id)
        if not contract:
            return StrategicUpdate(), SocialUpdate()

        # 1. Validate Transition
        if not SocialContractSystem._is_valid_transition(contract.status, new_status):
            return StrategicUpdate(), SocialUpdate()

        # 2. Apply Update
        duration = contract.terms.get("duration", 0)
        updated_contract = replace(contract, status=new_status)
        if new_status == ContractStatus.ACTIVE and duration > 0:
             updated_contract = replace(updated_contract, expiry_tick=tick + duration)

        # 3. Special side-effects
        social_upd = SocialUpdate()
        if new_status == ContractStatus.FULFILLED:
             social_upd = SocialUpdate(heroism_delta=0.05)

        return StrategicUpdate(contracts_add_or_update=[updated_contract]), social_upd

    @staticmethod
    def _is_valid_transition(old: ContractStatus, new: ContractStatus) -> bool:
        """Strict state machine for contracts."""
        rules = {
            # Added ACTIVE to OFFERED and COUNTERED as shortcuts used by ContractService
            ContractStatus.OFFERED: [ContractStatus.ACCEPTED, ContractStatus.ACTIVE, ContractStatus.CANCELLED, ContractStatus.COUNTERED, ContractStatus.EXPIRED],
            ContractStatus.COUNTERED: [ContractStatus.ACCEPTED, ContractStatus.ACTIVE, ContractStatus.CANCELLED, ContractStatus.EXPIRED],
            ContractStatus.ACCEPTED: [ContractStatus.ACTIVE, ContractStatus.CANCELLED],
            ContractStatus.ACTIVE: [ContractStatus.FULFILLED, ContractStatus.FAILED, ContractStatus.BETRAYED, ContractStatus.EXPIRED],
            ContractStatus.FULFILLED: [], # Terminal
            ContractStatus.FAILED: [],    # Terminal
            ContractStatus.BETRAYED: [],  # Terminal
            ContractStatus.EXPIRED: [],   # Terminal
            ContractStatus.CANCELLED: []  # Terminal
        }
        return new in rules.get(old, [])

    @staticmethod
    def check_expirations(entity: EntityState, current_tick: int) -> StrategicUpdate:
        """Auto-expire contracts that reached their tick limit."""
        to_update = []
        for contract in entity.strategic.contracts.values():
            if contract.status in (ContractStatus.OFFERED, ContractStatus.ACTIVE, ContractStatus.COUNTERED):
                if contract.expiry_tick != -1 and current_tick >= contract.expiry_tick:
                    to_update.append(replace(contract, status=ContractStatus.EXPIRED))
        
        if not to_update:
            return StrategicUpdate()
            
        return StrategicUpdate(contracts_add_or_update=to_update)

class ContractService:
    """
    Manages the creation, acceptance, and termination of social contracts.
    Merged with SocialContractSystem logic for unified social domain management.
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
        First returned SocialUpdate is for the entity passed as argument.
        """
        contract = entity.strategic.contracts.get(contract_id)
        if not contract:
            return StrategicUpdate(), []

        status = ContractStatus.FULFILLED if success else ContractStatus.FAILED
        if betrayal:
            status = ContractStatus.BETRAYED
            
        strat_up, _ = SocialContractSystem.transition_contract(entity, contract_id, status, tick)
        if not strat_up.contracts_add_or_update:
            # Transition rejected
            return StrategicUpdate(), []
            
        # Social Consequences
        sentiment_delta = 0.2 if success else -0.2
        familiarity_delta = 0.1
        
        if betrayal:
            sentiment_delta = -1.0 # Immediate max distrust
            
        bond_updates_source = [
            SocialBondUpdate(target_id=contract.target_id, sentiment_delta=sentiment_delta, familiarity_delta=familiarity_delta)
        ]
        bond_updates_target = [
            SocialBondUpdate(target_id=contract.source_id, sentiment_delta=sentiment_delta, familiarity_delta=familiarity_delta)
        ]
        
        # Reputation impact
        heroism_delta = 0.05 if success else 0.0
        notoriety_delta = 0.0 if success else 0.1
        
        source_up = SocialUpdate(bond_updates=bond_updates_source, heroism_delta=heroism_delta, notoriety_delta=notoriety_delta)
        target_up = SocialUpdate(bond_updates=bond_updates_target, heroism_delta=heroism_delta, notoriety_delta=notoriety_delta)

        if betrayal and betrayer_id:
             if betrayer_id == contract.source_id:
                  source_up = replace(source_up, notoriety_delta=0.5, betrayal_increment=1)
             elif betrayer_id == contract.target_id:
                  target_up = replace(target_up, notoriety_delta=0.5, betrayal_increment=1)

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
        
        # Order: [entity_up, other_up]
        if entity.id == contract.source_id:
             return strat_up, [source_up, target_up]
        else:
             return strat_up, [target_up, source_up]

    @staticmethod
    def process_active_contracts(
        state: AuthoritativeState,
        update: StateUpdate
    ) -> StateUpdate:
        """
        Processes ACTIVE contracts for expiration or completion.
        """
        refined_entity_updates = dict(update.entity_updates)
        current_tick = state.tick
        
        for e_id, entity in state.entities.items():
            for c_id, contract in entity.strategic.contracts.items():
                if contract.status == ContractStatus.ACTIVE:
                    if contract.expiry_tick != -1 and current_tick > contract.expiry_tick:
                        strat_up, bond_ups = ContractService.resolve_contract_outcome(entity, c_id, success=True, tick=current_tick)
                        
                        ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                        
                        # Merge strategic update
                        base_strat = ent_upd.strategic or StrategicUpdate()
                        merged_strat = replace(base_strat,
                            contracts_add_or_update=list(base_strat.contracts_add_or_update) + list(strat_up.contracts_add_or_update),
                            directives_add_or_update=list(base_strat.directives_add_or_update) + list(strat_up.directives_add_or_update)
                        )
                        
                        # Apply relevant SocialUpdate (resolve_contract_outcome returns [entity_up, other_up])
                        my_social_up = bond_ups[0]
                        
                        base_social = ent_upd.social or SocialUpdate()
                        merged_social = replace(base_social,
                            bond_updates=list(base_social.bond_updates) + list(my_social_up.bond_updates),
                            heroism_delta=base_social.heroism_delta + my_social_up.heroism_delta,
                            notoriety_delta=base_social.notoriety_delta + my_social_up.notoriety_delta
                        )
                        
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
                
                refined_entity_updates[e_id] = replace(ent_upd,
                    strategic=replace(strat_up,
                        contracts_remove=list(strat_up.contracts_remove) + expired_ids
                    )
                )
                
        return replace(update, entity_updates=refined_entity_updates)