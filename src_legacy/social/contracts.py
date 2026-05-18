from __future__ import annotations
from typing import Dict, Any, List
from src_legacy.core.strategic import ContractState, ContractKind

class ContractService:
    """
    Manages the creation and evaluation of social contracts.
    """

    @staticmethod
    def create_recruitment_contract(
        contract_id: str,
        source_id: int,
        target_id: int,
        daily_pay: int = 10,
        duration_ticks: int = 100
    ) -> ContractState:
        return ContractState(
            id=contract_id,
            kind=ContractKind.RECRUITMENT,
            source_id=source_id,
            target_id=target_id,
            terms={
                "daily_pay": daily_pay,
                "duration": duration_ticks
            }
        )

    @staticmethod
    def create_loan_contract(
        contract_id: str,
        source_id: int,
        target_id: int,
        amount: int,
        interest_rate: float = 0.1
    ) -> ContractState:
        return ContractState(
            id=contract_id,
            kind=ContractKind.LOAN,
            source_id=source_id,
            target_id=target_id,
            terms={
                "amount": amount,
                "interest_rate": interest_rate,
                "total_due": int(amount * (1.0 + interest_rate))
            }
        )
