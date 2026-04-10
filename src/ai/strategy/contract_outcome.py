"""Service for applying social and reputational consequences for contract outcomes. [PHASE 4]"""

from __future__ import annotations
from typing import TYPE_CHECKING

from src.core.models.enums import StrategicStatus
from src.actions.base import SocialUpdate, ReputationUpdate
from src.core.logic.relationship_service import RelationshipService
from src.core.logic.reputation_service import ReputationService

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.core.models.world_state import WorldState
    from src.core.models.strategy import SocialContractRecord

class ContractOutcomeService:
    """Applies consequences to bonds and reputation based on contract success/failure."""

    @classmethod
    def resolve_contract(
        cls, 
        world: WorldState, 
        contract: SocialContractRecord, 
        outcome: StrategicStatus
    ) -> None:
        """Process the final outcome of a social contract."""
        if outcome not in (StrategicStatus.RESOLVED, StrategicStatus.ABANDONED):
            return

        founder = world.entities.get(contract.founder_id)
        if not founder: return

        # 1. Reputation Consequences for Founder
        if outcome == StrategicStatus.RESOLVED:
            # Succesful founder gains trust and heroism
            rep_update = ReputationUpdate(
                trustworthiness_delta=0.8,
                heroism_delta=0.5,
                tags_add=["Reliable"]
            )
            ReputationService.apply_update(founder, rep_update)
        else:
            # Failed founder loses trust
            rep_update = ReputationUpdate(
                trustworthiness_delta=-1.2,
                tags_add=["Unreliable"]
            )
            ReputationService.apply_update(founder, rep_update)

        # 2. Relationship Consequences between Members
        for mid in contract.member_ids:
            for other_id in contract.member_ids:
                if mid == other_id: continue
                
                if outcome == StrategicStatus.RESOLVED:
                    # Mutual success builds trust and loyalty
                    social_update = SocialUpdate(
                        source_id=mid,
                        target_id=other_id,
                        trust_delta=0.6,
                        loyalty_delta=0.4
                    )
                else:
                    # Failure breeds resentment and breaks trust
                    social_update = SocialUpdate(
                        source_id=mid,
                        target_id=other_id,
                        trust_delta=-0.8,
                        resentment_delta=0.5
                    )
                
                RelationshipService.apply_update(world.social_registry, social_update, world.tick)
        
        # 3. Update Contract State for all members
        for mid in contract.member_ids:
            m_ent = world.entities.get(mid)
            if m_ent:
                for m_ct in m_ent.mind.strategic.contracts:
                    if m_ct.contract_id == contract.contract_id:
                        m_ct.status = outcome
                        # Clear group linkage
                        m_ct.linked_group_id = None
                        
        if world.emit:
            label = "COMPLETED" if outcome == StrategicStatus.RESOLVED else "FAILED"
            world.emit("social", f"Contract {contract.contract_id} {label}", 
                       entity_ids=tuple(contract.member_ids))
