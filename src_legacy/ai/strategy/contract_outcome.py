"""Service for applying social and reputational consequences for contract outcomes. [PHASE 4]"""

from __future__ import annotations
from typing import TYPE_CHECKING

from src_legacy.core.models.strategy import StrategicStatus
from src_legacy.actions.base import SocialUpdate, ReputationUpdate
from src_legacy.core.logic.relationship_service import RelationshipService
from src_legacy.core.logic.reputation_service import ReputationService

if TYPE_CHECKING:
    from src_legacy.core.entities.entity import Entity
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.core.models.strategy import SocialContractRecord
    from src_legacy.actions.base import IntentUpdate

class ContractOutcomeService:
    """Side-effect-free service for generating consequences of contract success/failure."""

    @classmethod
    def resolve_contract(
        cls, 
        contract: SocialContractRecord, 
        outcome: StrategicStatus,
        tick: int
    ) -> dict[int, list[IntentUpdate]]:
        """Process the final outcome of a social contract and yield intent updates. [phase_3_task_2]"""
        from src_legacy.actions.base import SocialUpdate, ReputationUpdate, StrategicUpdate
        
        updates: dict[int, list[IntentUpdate]] = {}
        if outcome not in (StrategicStatus.RESOLVED, StrategicStatus.ABANDONED):
            return {}

        # 1. Reputation Consequences for Founder
        founder_updates = updates.setdefault(contract.founder_id, [])
        
        if outcome == StrategicStatus.RESOLVED:
            # Successful founder gains trust and heroism
            founder_updates.append(ReputationUpdate(
                trustworthiness_delta=0.8,
                heroism_delta=0.5,
                tags_add=["Reliable"]
            ))
        else:
            # Failed founder loses trust
            founder_updates.append(ReputationUpdate(
                trustworthiness_delta=-1.2,
                tags_add=["Unreliable"]
            ))

        # 2. Relationship Consequences between Members
        # All members (including founder) evaluate each other
        for mid in contract.member_ids:
            member_updates = updates.setdefault(mid, [])
            
            # Semantic Strategic Update (Mark contract as resolved in their mind)
            member_updates.append(StrategicUpdate(
                contracts_add_or_update=[contract.model_copy(update={"status": outcome, "party_id": None, "resolved_tick": tick})]
            ))
            
            for other_id in contract.member_ids:
                if mid == other_id: continue
                
                if outcome == StrategicStatus.RESOLVED:
                    # Mutual success builds trust and loyalty
                    member_updates.append(SocialUpdate(
                        source_id=mid,
                        target_id=other_id,
                        trust_delta=0.6,
                        loyalty_delta=0.4
                    ))
                else:
                    # Failure breeds resentment and breaks trust
                    member_updates.append(SocialUpdate(
                        source_id=mid,
                        target_id=other_id,
                        trust_delta=-0.8,
                        resentment_delta=0.5
                    ))

        return updates
