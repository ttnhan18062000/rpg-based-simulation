
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Dict, Any
from dataclasses import replace
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.core.enums import ReasonCode

if TYPE_CHECKING:
    from src.core.state import EntityState, AuthoritativeState

class SocialAppraisalSystem:
    """
    Evaluates social offers and contracts based on trust, risk, and utility.
    VERIFIED v2: SocialAppraisalSystem
    """

    @staticmethod
    def appraise_contract(
        entity: EntityState,
        contract: ContractState,
        state: AuthoritativeState
    ) -> Tuple[ContractStatus, ReasonCode, Dict[str, Any]]:
        """
        Evaluate an OFFERED or COUNTERED contract.
        Returns (new_status, reason, counter_terms).
        """
        # 1. Trust Check
        source_id = contract.source_id
        source_entity = state.entities.get(source_id)
        bond = entity.social.bonds.get(source_id)
        
        # Public Reputation Bias (Phase 9 Hardening)
        public_trust = 0.5
        if source_entity:
            public_trust = source_entity.social.public_reputation / 2.0 # 0.0 to 1.0
        
        if bond:
            # Private sentiment takes priority: sentiment=1.0 -> 1.0, -1.0 -> 0.0
            trust_score = (bond.sentiment + 1.0) / 2.0
        else:
            # Blend history with public reputation
            history_trust = entity.social.trust_history.get(source_id, 0.5)
            trust_score = (public_trust * 0.7) + (history_trust * 0.3)
        
        # Persistent Distrust for betrayers
        if trust_score < 0.2 or (bond and bond.sentiment < -0.8):
            return ContractStatus.CANCELLED, ReasonCode.TOTAL_DISTRUST, {}
            
        # Betrayal history check
        if entity.social.betrayal_count > 0:
            if trust_score < 0.4:
                return ContractStatus.CANCELLED, ReasonCode.BETRAYAL_HISTORY, {}

        # 2. Kind-Specific Appraisal
        if contract.kind == ContractKind.RECRUITMENT:
            return SocialAppraisalSystem._appraise_recruitment(entity, contract, trust_score)
        
        if contract.kind == ContractKind.LOAN:
            # Simple wrapper for now
            ok, reason = SocialAppraisalSystem._appraise_loan(entity, contract, trust_score)
            return (ContractStatus.ACCEPTED if ok else ContractStatus.CANCELLED), reason, {}
        
        elif contract.kind == ContractKind.POSITION_SWAP:
            return SocialAppraisalSystem._appraise_position_swap(
                entity,
                contract,
                state,
            )
            
        return ContractStatus.CANCELLED, ReasonCode.UNKNOWN, {}

    @staticmethod
    def _appraise_recruitment(
        entity: EntityState,
        contract: ContractState,
        trust_score: float
    ) -> Tuple[ContractStatus, ReasonCode, Dict[str, Any]]:
        # Domain 7 Hardening: Social Fatigue
        # Repeated offers within a short window increase rejection probability
        recent_rejections = entity.social.rejection_count.get(contract.source_id, 0)
        fatigue_penalty = 0.0
        if recent_rejections > 0:
            # -0.1 per recent rejection
            fatigue_penalty = min(0.5, recent_rejections * 0.1)
            
        # 0. Loyalty/Trust check (Immediate acceptance if extremely high)
        if trust_score >= 0.9 and fatigue_penalty < 0.2:
            return ContractStatus.ACCEPTED, ReasonCode.LOYALTY_ACCEPTANCE, {}
            
        pay = contract.terms.get("daily_pay", 0)
        risk = contract.terms.get("risk_level", "NORMAL")
        
        # 1. Utility vs Risk
        # Base pay expectation scales with level
        expected_pay = 10 * entity.identity.evolution_level
        utility = pay / max(1, expected_pay)
        
        risk_weight = 1.0 if risk == "HIGH" else (0.5 if risk == "NORMAL" else 0.1)
        
        # Domain 7 Hardening: Trait Modifiers
        traits = entity.identity.traits
        if "CAUTIOUS" in traits:
            risk_weight *= 1.5
            trust_score *= 0.8 # Requires higher trust
            
        if "LOYAL" in traits and trust_score > 0.6:
            utility += 0.3 # Easier to recruit by friends
            
        if "GREEDY" in traits:
            if utility < 1.0:
                return ContractStatus.CANCELLED, ReasonCode.INSUFFICIENT_INCENTIVE, {}
            utility *= 0.7 # Harder to satisfy even with high pay
            
        hp_pct = entity.combat.hp / entity.combat.max_hp
        
        # 2. Hard Rejections
        if risk == "HIGH" and hp_pct < 0.5:
            return ContractStatus.FAILED, ReasonCode.LOW_HP_RETREAT, {} 
            
        # 3. Scoring
        # Greed check: desperate entities accept lower pay
        is_desperate = entity.inventory.gold < 5
        greed_threshold = 0.5 if is_desperate else 1.0
        
        # Weighted score: (Trust * 0.4) + (Utility * 0.4) - (Risk * 0.2) - Fatigue
        score = (trust_score * 0.4) + (utility * 0.4) - (risk_weight * 0.2) - fatigue_penalty
        
        if score >= 0.5:
            return ContractStatus.ACCEPTED, ReasonCode.FAIR_COMPENSATION, {}
            
        # 4. Haggling (COUNTERED)
        if score >= 0.3 and contract.negotiation_count < 2 and "GREEDY" not in traits:
            # Propose a fair pay
            required_pay = int(max(pay, expected_pay * greed_threshold))
            if required_pay > pay:
                counter_terms = dict(contract.terms)
                counter_terms["daily_pay"] = required_pay
                return ContractStatus.COUNTERED, ReasonCode.HAGGLING_FOR_PAY, counter_terms
            
        return ContractStatus.CANCELLED, ReasonCode.INSUFFICIENT_INCENTIVE, {}
            
    @staticmethod
    def recalibrate_trust(
        observer_social: SocialComponent,
        subject_id: int,
        outcome_quality: float = 0.0,
        harm_ratio: float = 0.0
    ) -> SocialUpdate:
        """
        Recalculate trust based on a concrete interaction outcome.
        VERIFIED v2: SocialAppraisalSystem.recalibrate_trust
        """
        # ... logic for recalibration ...
        from src.core.updates import SocialBondUpdate, SocialUpdate
        trust_delta = outcome_quality * 0.1
        if harm_ratio > 0:
            trust_delta -= harm_ratio * 0.5
            
        return SocialUpdate(
            trust_delta={subject_id: trust_delta},
            bond_updates=[SocialBondUpdate(
                target_id=subject_id,
                sentiment_delta=trust_delta * 2.0
            )]
        )

    @staticmethod
    def _appraise_loan(
        entity: EntityState,
        contract: ContractState,
        trust_score: float
    ) -> Tuple[bool, ReasonCode]:
        amount = contract.terms.get("amount", 0)
        interest = contract.terms.get("interest_rate", 0.0)
        
        if interest > 0.5: # Usury!
            return False, ReasonCode.USURY_REJECTION
            
        if entity.inventory.gold < 5 and amount > 20:
            return True, ReasonCode.DESPERATION_ACCEPTANCE
            
        if trust_score > 0.5 and interest <= 0.1:
            return True, ReasonCode.FRIENDLY_LOAN
            
        return False, ReasonCode.UNNECESSARY_DEBT
    
    
    @staticmethod
    def _appraise_position_swap(
        entity: EntityState,
        contract: ContractState,
        state: AuthoritativeState,
    ) -> tuple[ContractStatus, ReasonCode, dict[str, Any]]:
        """
        Evaluate whether the target entity accepts an adjacent position swap.

        LAW:
            An entity may accept a swap when:
                - both parties exist
                - both are active/alive
                - both are adjacent
                - neither party is in HOLD mode
                - the contract has not expired
                - the contract positions still match the current world state

        This is intentionally simpler than recruitment/loan appraisal because a
        one-tick corridor swap is a low-risk movement agreement, not a long-term
        social obligation.
        """
        from src.core.movement_modes import MovementMode

        source = state.entities.get(contract.source_id)
        target = state.entities.get(contract.target_id)

        if source is None or target is None:
            return ContractStatus.CANCELLED, ReasonCode.TARGET_INVALID, {}

        if contract.expiry_tick != -1 and state.tick > contract.expiry_tick:
            return ContractStatus.EXPIRED, ReasonCode.PATH_EXHAUSTED, {}

        if not source.lifecycle.active or not target.lifecycle.active:
            return ContractStatus.CANCELLED, ReasonCode.POSITION_SWAP_REFUSED, {}

        if not source.combat.alive or not target.combat.alive:
            return ContractStatus.CANCELLED, ReasonCode.POSITION_SWAP_REFUSED, {}

        if source.navigation.movement_mode == MovementMode.HOLD:
            return ContractStatus.CANCELLED, ReasonCode.POSITION_SWAP_REFUSED, {}

        if target.navigation.movement_mode == MovementMode.HOLD:
            return ContractStatus.CANCELLED, ReasonCode.POSITION_SWAP_REFUSED, {}

        source_pos = source.navigation.position
        target_pos = target.navigation.position

        dist = abs(source_pos[0] - target_pos[0]) + abs(source_pos[1] - target_pos[1])
        if dist != 1:
            return ContractStatus.CANCELLED, ReasonCode.OUT_OF_RANGE, {}

        expected_terms = {
            "source_from": source_pos,
            "source_to": target_pos,
            "target_from": target_pos,
            "target_to": source_pos,
        }

        for key, expected_pos in expected_terms.items():
            if key in contract.terms:
                actual = tuple(contract.terms[key])
                if actual != expected_pos:
                    return ContractStatus.CANCELLED, ReasonCode.POSITION_SWAP_REFUSED, {}

        return ContractStatus.ACCEPTED, ReasonCode.POSITION_SWAP_ACCEPTED, {}
    

    @staticmethod
    def process_betrayal(
        victim: EntityState,
        betrayer_id: int,
        salience: float,
        current_tick: int
    ) -> tuple[SocialUpdate, StrategicUpdate]:
        """
        LEG-RPG-119: Betrayal (Avenge).
        Part 1 §Social: Private betrayal history can override public recruiter reputation.
        """
        from src.core.updates import SocialBondUpdate, SocialUpdate, StrategicUpdate
        from src.core.strategic import TurningPointState, DirectiveState, DirectivePriority
        
        # Heavy trust penalty for betrayal
        trust_delta = -0.3 - (salience * 0.4)

        social_update = SocialUpdate(
            trust_delta={betrayer_id: trust_delta},
            bond_updates=[SocialBondUpdate(
                target_id=betrayer_id,
                sentiment_delta=trust_delta * 2.0,
                last_interaction_tick_set=current_tick
            )],
            betrayal_increment=1
        )

        # High-salience betrayals create an AVENGE directive and a TurningPoint
        tp = TurningPointState(
            id=f"tp_betrayal_{betrayer_id}_{current_tick}",
            kind="betrayal",
            subject_id=betrayer_id,
            salience=salience,
            tick=current_tick
        )
        
        strategic_update = StrategicUpdate(turning_points_add=[tp])
        if salience > 0.5:
            directive = DirectiveState(
                id=f"directive_avenge_{betrayer_id}",
                kind="avenge",
                target=str(betrayer_id),
                priority=DirectivePriority.HIGH if salience > 0.7 else DirectivePriority.NORMAL,
                salience=salience,
                created_tick=current_tick
            )
            strategic_update = replace(strategic_update,
                directives_add_or_update=[directive]
            )

        return social_update, strategic_update

    @staticmethod
    def recalibrate_source_trust(
        observer: EntityState,
        source_id: int,
        outcome: str,  # 'SUCCESS' or 'FAILURE'
    ) -> StrategicUpdate:
        """
        LEG-RPG-123: Refutation drops trust.
        """
        from src.core.updates import StrategicUpdate
        from src.core.strategic import SourceTrustEntry
        
        existing = observer.strategic.source_trust.get(source_id)
        current_trust = existing.trust if existing else 0.5
        current_interactions = existing.interactions if existing else 0

        if outcome == "SUCCESS":
            new_trust = min(1.0, current_trust + 0.1)
        else:  # FAILURE
            new_trust = max(0.0, current_trust - 0.15)

        updated = SourceTrustEntry(
            entity_id=source_id,
            trust=new_trust,
            interactions=current_interactions + 1,
            last_outcome=outcome
        )

        return StrategicUpdate(source_trust_updates=[updated])

    @staticmethod
    def update_familiarity(
        observer: EntityState,
        subject_id: int,
        interaction_quality: float,
        current_tick: int,
        cha_modifier: float = 1.0
    ) -> SocialUpdate:
        """
        Part 1 §Social: Social learning updates familiarity/trust-like bonds.
        VERIFIED v2: SocialAppraisalSystem.process_social_event
        """
        from src.core.updates import SocialBondUpdate, SocialUpdate
        
        familiarity_gain = 0.05 * cha_modifier
        sentiment_shift = interaction_quality * 0.1

        return SocialUpdate(
            bond_updates=[SocialBondUpdate(
                target_id=subject_id,
                familiarity_delta=familiarity_gain,
                sentiment_delta=sentiment_shift,
                last_interaction_tick_set=current_tick
            )]
        )

    @staticmethod
    def calculate_recruitment_cost(
        recruiter: EntityState,
        candidate: EntityState
    ) -> int:
        """
        Part 1 §Social: Recruitment evaluates trust, level, and greed.
        Scales cost with target level and trust bond.
        """
        # Base cost 100
        base_cost = 100
        level_mult = candidate.identity.evolution_level
        
        # Bond sentiment preference
        bond = candidate.social.bonds.get(recruiter.id)
        if bond:
            # sentiment=1.0 -> trust=1.0, sentiment=-1.0 -> trust=0.0
            trust = (bond.sentiment + 1.0) / 2.0
        else:
            trust = candidate.social.trust_history.get(recruiter.id, 0.5)
            
        # trust=1.0 -> mult=0.5, trust=0.5 -> mult=1.0, trust=0.0 -> mult=1.5
        trust_mult = 1.5 - trust
        
        cost = int(base_cost * level_mult * trust_mult)
        return max(50, cost)

class RecruitmentAppraiser:
    """
    Consolidated recruitment logic for Phase E5.
    VERIFIED v2: RecruitmentAppraiser.evaluate
    """
    @staticmethod
    def evaluate(entity: EntityState, contract: ContractState, trust_score: float) -> Tuple[ContractStatus, ReasonCode, Dict[str, Any]]:
        return SocialAppraisalSystem._appraise_recruitment(entity, contract, trust_score)

