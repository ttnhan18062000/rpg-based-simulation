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
    ) -> StrategicUpdate:
        """
        Validates and applies a state transition for a contract.
        """
        contract = entity.strategic.contracts.get(contract_id)
        if not contract:
            return StrategicUpdate()

        # 1. Validate Transition
        if not SocialContractSystem._is_valid_transition(contract.status, new_status):
            return StrategicUpdate()

        # 2. Apply Update
        updated_contract = replace(contract, status=new_status)
        
        # 3. Special side-effects
        party_upd = None
        if new_status == ContractStatus.ACCEPTED and contract.kind == ContractKind.RECRUITMENT:
             # Recruitment acceptance might trigger party formation
             pass

        return StrategicUpdate(contracts_add_or_update=[updated_contract])

    @staticmethod
    def _is_valid_transition(old: ContractStatus, new: ContractStatus) -> bool:
        """Strict state machine for contracts."""
        rules = {
            ContractStatus.OFFERED: [ContractStatus.ACCEPTED, ContractStatus.CANCELLED, ContractStatus.COUNTERED, ContractStatus.EXPIRED],
            ContractStatus.COUNTERED: [ContractStatus.ACCEPTED, ContractStatus.CANCELLED, ContractStatus.EXPIRED],
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
