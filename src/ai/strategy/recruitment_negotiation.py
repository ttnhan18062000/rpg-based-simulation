"""Service for generating and evaluating social contract offers. [PHASE 4]"""

from __future__ import annotations
import uuid
from typing import TYPE_CHECKING

from src.core.models.enums import OfferStatus, ContractKind
from src.core.models.strategy import RecruitmentOfferRecord, ContractTermRecord

if TYPE_CHECKING:
    from src.ai.states.base import AIContext
    from src.core.entities.entity import Entity
    from src.core.models.strategy import ProjectRecord

class RecruitmentNegotiationService:
    """Handles the async offer lifecycle: generation, appraisal, and response."""

    @classmethod
    def create_offer(
        cls, 
        ctx: AIContext, 
        candidate_id: int, 
        project: ProjectRecord,
        kind: ContractKind = ContractKind.EXPEDITION
    ) -> RecruitmentOfferRecord:
        """Founder generates an initial recruitment offer for a candidate."""
        actor = ctx.actor
        
        # 1. Define Terms based on project needs and personality
        terms = []
        
        # Reward Split (Greed affects how much we keep)
        greed = actor.mind.decision.personality.greed
        share = max(0.1, min(0.5, 0.5 - (greed * 0.4))) # Offer between 10% and 50%
        
        terms.append(ContractTermRecord(
            term_type="payout",
            label="Payout Share",
            params={"value": share, "is_negotiable": True}
        ))
        
        # Role Expectation
        role = "vanguard" if project and project.metadata.get("risk", 0) < 0.5 else "support"
        terms.append(ContractTermRecord(
            term_type="behavior",
            label="Preferred Role",
            params={"role": role, "is_negotiable": True}
        ))

        # 2. Package the offer
        return RecruitmentOfferRecord(
            offer_id=f"off_{uuid.uuid4().hex[:8]}",
            recruiter_id=actor.id,
            candidate_id=candidate_id,
            contract_kind=kind,
            project_id=project.project_id if project else None,
            status=OfferStatus.PENDING,
            proposed_terms=terms,
            expires_tick=ctx.snapshot.tick + 100 
        )

    @classmethod
    def evaluate_offer(
        cls, 
        ctx: AIContext, 
        offer: RecruitmentOfferRecord
    ) -> bool:
        """Candidate decides whether to accept the offer based on willingness."""
        actor = ctx.actor
        founder = ctx.snapshot.entities.get(offer.recruiter_id)
        if not founder:
            return False
            
        # 1. Base Willingness from Relationship
        willingness = 0.0
        bond = actor.mind.social.known_bonds.get(offer.recruiter_id)
        if bond:
            # Trust is the strongest multiplier
            willingness += bond.trust * 0.5
            willingness += bond.loyalty * 0.3
            willingness += bond.admiration * 0.2
            
            # Debt (If we owe the founder, we are more likely to accept)
            if bond.debt > 0.3: # We owe them
                willingness += bond.debt * 0.4
                
            # Negative offsets
            willingness -= bond.rivalry * 0.6
            willingness -= bond.resentment * 0.4
        else:
            # Neutral starting point for strangers of same faction
            willingness = 0.1
            
        # 2. Reputation Bias
        recruiter_rep = founder.identity.reputation
        willingness += (recruiter_rep.trustworthiness / 10.0) * 0.3
        willingness += (recruiter_rep.heroism_score / 10.0) * 0.2
        
        # 3. Term Appraisal
        for term in offer.proposed_terms:
            if term.term_type == "payout":
                # Candidate's greed makes them want more
                greed = actor.mind.decision.personality.greed
                expected_share = 0.2 + (greed * 0.3) # 20% to 50%
                value = term.params.get("value", 0)
                if float(value) >= expected_share:
                    willingness += 0.3
                else:
                    willingness -= 0.2
            
        # 4. Motive Bias
        for motive in actor.mind.decision.motives:
            if motive.kind == "build_wealth":
                if offer.kind == ContractKind.MERCENARY: willingness += 0.2
            if motive.kind == "prove_strength":
                if offer.kind == ContractKind.EXPEDITION: willingness += 0.2

        # 5. Risk Assessment (Placeholder for simple HP check)
        if actor.combat.hp_ratio < 0.4:
            willingness -= 0.5 # Too injured to care about contracts
            
        # Final Decision
        threshold = 0.3 # Base threshold to say 'Yes'
        return willingness >= threshold
