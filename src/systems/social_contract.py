from __future__ import annotations
from dataclasses import replace
from typing import Optional, Dict, Any, List

from src.core.state import EntityState, AuthoritativeState
from src.core.strategic import ContractState, ContractStatus, ContractKind
from src.core.updates import StrategicUpdate, SocialUpdate

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
    ) -> tuple[StrategicUpdate, Optional[SocialUpdate]]:
        """
        Validates and applies a state transition for a contract.
        """
        contract = entity.strategic.contracts.get(contract_id)
        if not contract or not SocialContractSystem._is_valid_transition(contract.status, new_status):
            return StrategicUpdate(), None

        # 1. Validate Transition
        if not SocialContractSystem._is_valid_transition(contract.status, new_status):
            return StrategicUpdate(), None

        # 2. Apply Update
        expiry_tick = contract.expiry_tick
        if new_status == ContractStatus.ACTIVE:
             duration = contract.terms.get("duration", 0)
             if duration > 0:
                 expiry_tick = tick + duration
                 
        updated_contract = replace(contract, status=new_status, expiry_tick=expiry_tick)
        
        # 3. Special side-effects
        social_upd = None
        
        # Bond/Reputation consequences
        if new_status in (ContractStatus.FULFILLED, ContractStatus.FAILED, ContractStatus.BETRAYED):
             from src.core.updates import SocialBondUpdate, SocialUpdate
             
             sentiment_delta = 0.0
             notoriety_delta = 0.0
             heroism_delta = 0.0
             
             if new_status == ContractStatus.FULFILLED:
                 sentiment_delta = 0.2
                 heroism_delta = 0.05
             elif new_status == ContractStatus.FAILED:
                 sentiment_delta = -0.1
                 notoriety_delta = 0.05
             elif new_status == ContractStatus.BETRAYED:
                 sentiment_delta = -1.0
                 notoriety_delta = 0.5
             
             other_id = contract.target_id if contract.source_id == entity.id else contract.source_id
             social_upd = SocialUpdate(
                 bond_updates=[SocialBondUpdate(target_id=other_id, sentiment_delta=sentiment_delta, familiarity_delta=0.1)],
                 heroism_delta=heroism_delta,
                 notoriety_delta=notoriety_delta,
                 betrayal_increment=1 if new_status == ContractStatus.BETRAYED else 0
             )

        return StrategicUpdate(contracts_add_or_update=[updated_contract]), social_upd

    @staticmethod
    def _is_valid_transition(old: ContractStatus, new: ContractStatus) -> bool:
        """Strict state machine for contracts."""
        rules = {
            ContractStatus.OFFERED: [ContractStatus.ACCEPTED, ContractStatus.ACTIVE, ContractStatus.CANCELLED, ContractStatus.COUNTERED, ContractStatus.EXPIRED],
            ContractStatus.COUNTERED: [ContractStatus.ACCEPTED, ContractStatus.CANCELLED, ContractStatus.EXPIRED],
            ContractStatus.ACCEPTED: [ContractStatus.ACTIVE, ContractStatus.FULFILLED, ContractStatus.CANCELLED],
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
