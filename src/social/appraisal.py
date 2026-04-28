
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Dict, Any
from src.core.strategic import ContractState, ContractKind, ContractStatus

if TYPE_CHECKING:
    from src.core.state import EntityState, AuthoritativeState

class SocialAppraisalSystem:
    """
    Evaluates social offers and contracts based on trust, risk, and utility.
    """

    @staticmethod
    def appraise_contract(
        entity: EntityState,
        contract: ContractState,
        state: AuthoritativeState
    ) -> Tuple[bool, str]:
        """
        Returns (should_accept, reason).
        """
        # 1. Trust Check
        source_id = contract.source_id
        bond = entity.social.bonds.get(source_id)
        trust_score = bond.sentiment if bond else 0.0
        
        # Base sentiment threshold
        if trust_score < -0.5:
            return False, "TOTAL_DISTRUST"

        # 2. Kind-Specific Appraisal
        if contract.kind == ContractKind.RECRUITMENT:
            return SocialAppraisalSystem._appraise_recruitment(entity, contract, trust_score)
        elif contract.kind == ContractKind.LOAN:
            return SocialAppraisalSystem._appraise_loan(entity, contract, trust_score)
            
        return False, "UNKNOWN_CONTRACT_KIND"

    @staticmethod
    def _appraise_recruitment(
        entity: EntityState,
        contract: ContractState,
        trust_score: float
    ) -> Tuple[bool, str]:
        pay = contract.terms.get("daily_pay", 0)
        risk = contract.terms.get("risk_level", "NORMAL")
        
        # Utility vs Risk
        utility = pay / 10.0 # 10 gold is base daily pay
        
        # If very high trust, skip strict utility check
        if trust_score > 0.8:
            return True, "LOYALTY_ACCEPTANCE"
            
        if risk == "HIGH" and entity.combat.hp < 50:
            return False, "TOO_DANGEROUS"
            
        if utility >= 1.0:
            return True, "FAIR_COMPENSATION"
            
        if utility + trust_score >= 1.0:
            return True, "TRUST_WEIGHTED_ACCEPTANCE"
            
        return False, "INSUFFICIENT_INCENTIVE"

    @staticmethod
    def _appraise_loan(
        entity: EntityState,
        contract: ContractState,
        trust_score: float
    ) -> Tuple[bool, str]:
        amount = contract.terms.get("amount", 0)
        interest = contract.terms.get("interest_rate", 0.0)
        
        if interest > 0.5: # Usury!
            return False, "USURY_REJECTION"
            
        # If in desperate need of gold
        if entity.inventory.gold < 5 and amount > 20:
            return True, "DESPERATION_ACCEPTANCE"
            
        if trust_score > 0.5 and interest <= 0.1:
            return True, "FRIENDLY_LOAN"
            
        return False, "UNNECESSARY_DEBT"
