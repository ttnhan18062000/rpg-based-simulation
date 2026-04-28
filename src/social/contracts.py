
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.core.updates import StrategicUpdate, SocialBondUpdate

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
        risk_level: str = "NORMAL",
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
        entity_id: int,
        contract: ContractState,
        tick: int
    ) -> StrategicUpdate:
        """
        Transition an OFFERED contract to ACTIVE.
        """
        if contract.status != ContractStatus.OFFERED:
            return StrategicUpdate()
            
        new_contract = ContractState(
            id=contract.id,
            kind=contract.kind,
            source_id=contract.source_id,
            target_id=contract.target_id,
            terms=contract.terms,
            status=ContractStatus.ACTIVE,
            created_tick=tick,
            expiry_tick=tick + contract.terms.get("duration", 100) if contract.kind == ContractKind.RECRUITMENT else -1
        )
        
        return StrategicUpdate(
            contracts_add_or_update=[new_contract]
        )

    @staticmethod
    def resolve_contract_outcome(
        contract: ContractState,
        success: bool,
        betrayal: bool = False
    ) -> Tuple[StrategicUpdate, List[SocialBondUpdate]]:
        """
        Resolve an ACTIVE contract and update social relationships.
        """
        status = ContractStatus.COMPLETED if success else ContractStatus.FAILED
        if betrayal:
            status = ContractStatus.BETRAYED
            
        resolved_contract = ContractState(
            id=contract.id,
            kind=contract.kind,
            source_id=contract.source_id,
            target_id=contract.target_id,
            terms=contract.terms,
            status=status,
            created_tick=contract.created_tick,
            expiry_tick=contract.expiry_tick
        )
        
        # Social Consequences
        sentiment_delta = 0.1 if success else -0.1
        familiarity_delta = 0.05
        
        if betrayal:
            sentiment_delta = -1.0 # Immediate max distrust
            
        bond_updates = [
            SocialBondUpdate(target_id=contract.source_id, sentiment_delta=sentiment_delta, familiarity_delta=familiarity_delta),
            SocialBondUpdate(target_id=contract.target_id, sentiment_delta=sentiment_delta, familiarity_delta=familiarity_delta)
        ]
        
        return StrategicUpdate(contracts_add_or_update=[resolved_contract]), bond_updates
