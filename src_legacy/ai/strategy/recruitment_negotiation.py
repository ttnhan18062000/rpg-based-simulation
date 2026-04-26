"""Service for generating and evaluating social contract offers. [PHASE 4]"""

from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, Any

from src_legacy.core.models.enums import OfferStatus, ContractKind
from src_legacy.core.models.strategy import RecruitmentOfferRecord, ContractTermRecord

if TYPE_CHECKING:
    from src_legacy.ai.states.base import AIContext
    from src_legacy.core.entities.entity import Entity
    from src_legacy.core.models.strategy import ProjectRecord

from dataclasses import dataclass, field

@dataclass(frozen=True)
class OfferAppraisal:
    """Outcome of a candidate's evaluation of an offer."""
    status: OfferStatus
    counter_terms: list[ContractTermRecord] = field(default_factory=list)
    reason: str = ""

class RecruitmentNegotiationService:
    """Handles the async offer lifecycle: generation, appraisal, and response."""

    @classmethod
    def create_offer(
        cls, 
        ctx: AIContext, 
        candidate_id: int, 
        project: ProjectRecord,
        kind: ContractKind = ContractKind.EXPEDITION,
        profile: CognitionCapacityProfile | None = None
    ) -> RecruitmentOfferRecord:
        """Founder generates an initial recruitment offer for a candidate."""
        actor = ctx.actor
        
        # 1. Define Terms based on project needs and personality
        terms = []
        
        # Reward Split (Greed affects how much we keep)
        greed = actor.mind.decision.personality.greed
        base_share = 0.5 - (greed * 0.4) # Target share between 10% and 50%
        
        # [PHASE 4 INTEL CAPACITY] Judgment Stability Perturbation
        share = base_share
        if profile and profile.judgment_stability < 0.8:
            from src_legacy.core.models.enums import Domain
            seed = hash(f"offer_{candidate_id}_{ctx.snapshot.tick}") % 10000
            # Desperateness/Poor math adds/removes up to 20% share
            noise = (ctx.rng.next_float(Domain.SOCIAL, actor.id, ctx.snapshot.tick, seed) - 0.5) * (0.4 * (1.0 - profile.judgment_stability))
            share = max(0.05, min(0.6, base_share + noise))
            
        share = round(share, 2)
        
        terms.append(ContractTermRecord(
            term_type="payout",
            label="Payout Share",
            params={"value": share, "is_negotiable": True}
        ))
        
        # Role Expectation
        role = "vanguard" if project and project.metadata.get("risk", 0) > 0.5 else "support"
        terms.append(ContractTermRecord(
            term_type="behavior",
            label="Preferred Role",
            params={"role": role, "is_negotiable": True}
        ))

        # 2. Package the offer
        from src_legacy.core.models.enums import Domain
        offer_id = f"off_{ctx.rng.next_hex(Domain.SOCIAL, actor.id, ctx.snapshot.tick, sub_id=60)}"
        
        offer = RecruitmentOfferRecord(
            offer_id=offer_id,
            recruiter_id=actor.id,
            candidate_id=candidate_id,
            contract_kind=kind,
            project_id=project.project_id if project else None,
            status=OfferStatus.PENDING,
            proposed_terms=terms,
            expires_tick=ctx.snapshot.tick + 100,
            original_founder_id=actor.id
        )
        
        # Log initial history
        offer.negotiation_history.append({
            "tick": ctx.snapshot.tick,
            "from_id": actor.id,
            "status": OfferStatus.PENDING,
            "terms": [t.model_dump() for t in terms]
        })
        
        return offer

    @classmethod
    def evaluate_offer(
        cls, 
        ctx: AIContext, 
        offer: RecruitmentOfferRecord
    ) -> OfferAppraisal:
        """Candidate decides whether to accept, decline, or counter the offer."""
        actor = ctx.actor
        founder = ctx.snapshot.entities.get(offer.recruiter_id)
        if not founder:
            return OfferAppraisal(status=OfferStatus.CANCELLED, reason="Recruiter missing")
            
        # 1. Base Willingness from Relationship
        willingness = 0.0
        reason = "Insufficient motivation or trust"
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
        expected_share = 0.0
        current_share = 0.0
        
        for term in offer.proposed_terms:
            if term.term_type == "payout":
                # Candidate's greed makes them want more
                greed = actor.mind.decision.personality.greed
                expected_share = 0.2 + (greed * 0.3) # 20% to 50%
                current_share = float(term.params.get("value", 0))
                if current_share >= expected_share:
                    willingness += 0.3
                else:
                    willingness -= 0.2
            
        # 4. Motive Bias
        for motive in actor.mind.decision.motives:
            if motive.kind == "build_wealth":
                if offer.contract_kind == ContractKind.MERCENARY: willingness += 0.2
            if motive.kind == "prove_strength":
                if offer.contract_kind == ContractKind.EXPEDITION: willingness += 0.2

        # 5. Risk and Traumatic Bias [PHASE 5]
        if actor.combat.hp_ratio < 0.4:
            willingness -= 0.5 # Too injured to care about contracts
            
        # 5b. Betrayal Trauma Feedback [TCK-20260414-SOCIAL-03]
        from src_legacy.core.models.enums import TurningPointKind
        
        # Scan durable TurningPoints for private betrayal history (bypassing public fame)
        betrayals = [tp for tp in actor.mind.narrative.turning_points if tp.kind == TurningPointKind.BETRAYAL]
        
        if betrayals:
            # General distrust penalty
            willingness -= 0.5
            
            # Check for direct grudge: Did THIS recruiter betray us?
            direct_betrayal = any(offer.recruiter_id in tp.involved_entity_ids for tp in betrayals)
            if direct_betrayal:
                willingness -= 1.0 # Instant rejection
                reason = "Recruiter was involved in a past betrayal."
        
        # Fallback to general concern scan
        has_betrayal_concern = any("Betrayal" in c.label for c in actor.mind.strategic.concerns) or \
                               any("Betrayal" in d.label for d in actor.mind.strategic.directives)
        if has_betrayal_concern:
            willingness -= 0.3
            
        # Final Decision
        threshold = 0.3 # Base threshold to say 'Yes'
        
        if willingness >= threshold:
            return OfferAppraisal(status=OfferStatus.ACCEPTED)
        
        # Haggling Check: If we are close and can counter a negotiable term [phase_3_task_1]
        # Candidates haggle if willingness is within 0.4 of threshold
        if willingness >= (threshold - 0.4) and offer.negotiation_count < 2:
            # Look for negotiable terms to counter
            counter_terms = []
            made_counter = False
            
            for term in offer.proposed_terms:
                if term.term_type == "payout" and term.params.get("is_negotiable", False):
                    # Haggle for the expected share (plus a small greed buffer)
                    greed = actor.mind.decision.personality.greed
                    min_acceptable = expected_share - (0.1 * (1.0 - greed))
                    
                    if current_share < min_acceptable:
                        new_params = dict(term.params)
                        # We ask for a bit more than expected share if we are greedy
                        new_params["value"] = round(expected_share + (greed * 0.1), 2)
                        counter_terms.append(ContractTermRecord(
                            term_type="payout",
                            label="Counter Payout",
                            params=new_params
                        ))
                        made_counter = True
                    else:
                        counter_terms.append(term)
                else:
                    counter_terms.append(term)
            
            if made_counter:
                return OfferAppraisal(
                    status=OfferStatus.COUNTERED, 
                    counter_terms=counter_terms, 
                    reason="Haggling for better payout"
                )
                
        return OfferAppraisal(status=OfferStatus.DECLINED, reason=reason)

    @classmethod
    def evaluate_counter(
        cls,
        ctx: AIContext,
        offer: RecruitmentOfferRecord,
        counter_appraisal: OfferAppraisal
    ) -> OfferStatus:
        """Recruiter evaluates the candidate's counter-offer. [phase_3_task_1]"""
        actor = ctx.actor # The Recruiter
        project = next((p for p in actor.mind.strategic.projects if p.project_id == offer.project_id), None)
        
        # 1. Base willingness to haggle based on urgency and relationship
        # High priority projects make us more desperate
        base_willingness = 0.5
        if project:
            base_willingness += project.priority * 0.1
            base_willingness += project.urgency * 0.2
            
        # 2. Social Bond check
        bond = actor.mind.social.known_bonds.get(offer.candidate_id)
        if bond:
            base_willingness += bond.loyalty * 0.2
            base_willingness -= bond.resentment * 0.3
            
        # 3. Term Evaluate
        for term in counter_appraisal.counter_terms:
            if term.term_type == "payout":
                counter_value = float(term.params.get("value", 0))
                # If they ask for more than 40% of the total, we get suspicious
                if counter_value > 0.4:
                    base_willingness -= (counter_value - 0.4) * 2.0
        
        # Final Decision for recruiter
        if base_willingness >= 0.4:
            return OfferStatus.ACCEPTED
        return OfferStatus.DECLINED

    @classmethod
    def process_lifecycle(
        cls, 
        ctx: AIContext, 
        offer: RecruitmentOfferRecord
    ) -> OfferStatus | None:
        """Check for expiry or withdrawal of an offer. [phase_3_task_1]"""
        # 1. Expiry check
        if offer.expires_tick and ctx.snapshot.tick > offer.expires_tick:
            return OfferStatus.EXPIRED
            
        # 2. Withdrawal check (If recruiter found another group or died)
        recruiter = ctx.snapshot.entities.get(offer.recruiter_id)
        if not recruiter or not recruiter.combat.alive:
            return OfferStatus.CANCELLED
            
        return None
