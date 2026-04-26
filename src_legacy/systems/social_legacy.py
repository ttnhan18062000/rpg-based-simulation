"""
Social Appraisal, Trust, Betrayal, Contracts, and Recruitment System.

Expanded in Phase 9 to support:
- LEG-RPG-119: Betrayal (Avenge) — betrayal adds directive
- LEG-RPG-123: Refutation drops trust
- Part 1 §Social: Private betrayal overrides public reputation
- Part 1 §Social: Social learning updates familiarity/trust bonds
- Part 1 §Social: Social contracts as explicit strategic objects
- Part 1 §Social: Breaking/honoring contracts has persistent consequences
- Part 1 §Social: Recruitment evaluates trust, debt, greed, capability fit, prior trauma
"""
from __future__ import annotations
from dataclasses import replace, dataclass, field
from typing import Dict, List, Optional

from src_legacy.core.state import EntityState, SocialBond
from src_legacy.core.updates import SocialUpdate, StrategicUpdate, SocialBondUpdate
from src_legacy.core.strategic import (
    DirectiveState, DirectivePriority, SourceTrustEntry
)


@dataclass(frozen=True, slots=True)
class SocialContract:
    """An explicit agreement between entities with consequences."""
    id: str
    kind: str  # 'escort', 'trade', 'alliance', 'protection', 'employment'
    party_ids: List[int] = field(default_factory=list)
    terms: Dict[str, float] = field(default_factory=dict)  # e.g. {'payout': 100, 'duration': 50}
    status: str = "ACTIVE"  # ACTIVE, HONORED, BROKEN, EXPIRED
    created_tick: int = 0
    expires_tick: int = 0


@dataclass(frozen=True, slots=True)
class TurningPoint:
    """A significant life event that persistently biases future behavior."""
    id: str
    kind: str  # 'betrayal', 'near_death', 'first_kill', 'great_victory', 'loss'
    subject_id: Optional[int] = None  # Related entity
    salience: float = 0.5  # How impactful (0.0 to 1.0)
    tick: int = 0


class SocialAppraisalSystem:
    """
    Authoritative logic for trust recalibration and social evaluation.
    Phase 9: Full betrayal, contract, and recruitment pipeline.
    """

    @staticmethod
    def recalibrate_trust(
        observer: EntityState,
        subject_id: int,
        outcome_quality: float = 0.0,
        harm_ratio: float = 0.0,
        help_ratio: float = 0.0
    ) -> SocialUpdate:
        """
        Recalculate trust based on a concrete interaction outcome.
        Legacy Parity:
        - Harm: -0.1 - (harm_ratio * 0.5)
        - Help: 0.05 + (help_ratio * 0.4)
        - General Success/Failure: 0.1 / -0.2
        """
        trust_delta = 0.0

        if harm_ratio > 0:
            trust_delta = -0.1 - (harm_ratio * 0.5)
        elif help_ratio > 0:
            trust_delta = 0.05 + (help_ratio * 0.4)
        else:
            if outcome_quality > 0:
                trust_delta = 0.1
            elif outcome_quality < 0:
                trust_delta = -0.2

        return SocialUpdate(
            trust_delta={subject_id: trust_delta},
            bond_updates=[SocialBondUpdate(
                target_id=subject_id,
                sentiment_delta=trust_delta * 2.0 # Scale trust [0,1] delta to sentiment [-1,1] delta
            )]
        )

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

        Returns both social and strategic updates:
        - Social: trust drop + betrayal count increment
        - Strategic: AVENGE directive if salience is high enough
        """
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

        # High-salience betrayals create an AVENGE directive
        strategic_update = StrategicUpdate()
        if salience > 0.5:
            directive = DirectiveState(
                id=f"directive_avenge_{betrayer_id}",
                kind="avenge",
                target=str(betrayer_id),
                priority=DirectivePriority.HIGH if salience > 0.7 else DirectivePriority.NORMAL,
                salience=salience,
                created_tick=current_tick
            )
            strategic_update = StrategicUpdate(
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
        Update source trust based on whether their lead proved accurate.
        """
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

    @staticmethod
    def evaluate_recruitment_offer(
        candidate: EntityState,
        recruiter_id: int,
        payout: int,
        risk: float,
        betrayal_history: Optional[Dict[int, int]] = None
    ) -> bool:
        """
        Part 1 §Social: Recruitment evaluates trust, debt, greed, capability fit, prior trauma.

        Extended to account for betrayal trauma: if the recruiter has betrayed
        this candidate before, recruitment is much harder.
        """
        bond = candidate.social.bonds.get(recruiter_id)
        if bond:
            trust = (bond.sentiment + 1.0) / 2.0
        else:
            trust = candidate.social.trust_history.get(recruiter_id, 0.5)

        # Betrayal penalty
        betrayal_penalty = 0.0
        if candidate.social.betrayal_count > 0:
            # General caution from having been betrayed
            betrayal_penalty = min(0.3, candidate.social.betrayal_count * 0.1)

        # Per-recruiter trust penalty (if recruiter specifically betrayed this entity)
        if trust < 0.3:
            betrayal_penalty += 0.2

        # Score = (Trust * 0.5) + (Payout/200 * 0.3) - (Risk * 0.1) - betrayal_penalty
        score = (trust * 0.5) + (min(1.0, payout / 200) * 0.3) - (risk * 0.1) - betrayal_penalty

        return score >= 0.5

    @staticmethod
    def process_contract_outcome(
        contract: SocialContract,
        outcome: str,  # 'HONORED' or 'BROKEN'
        current_tick: int
    ) -> tuple[SocialUpdate, List[TurningPoint]]:
        """
        Part 1 §Social: Breaking or honoring contracts has persistent consequences.

        Returns social updates and turning points for all parties.
        """
        turning_points = []
        trust_deltas: Dict[int, float] = {}

        bond_updates = []
        if outcome == "HONORED":
            # All parties gain mutual trust
            for party_id in contract.party_ids:
                for other_id in contract.party_ids:
                    if other_id != party_id:
                        trust_deltas[other_id] = trust_deltas.get(other_id, 0.0) + 0.1
                        bond_updates.append(SocialBondUpdate(
                            target_id=other_id,
                            sentiment_delta=0.2, # 0.1 * 2
                            last_interaction_tick_set=current_tick
                        ))

        elif outcome == "BROKEN":
            # Broken contract creates betrayal turning points
            for party_id in contract.party_ids:
                turning_points.append(TurningPoint(
                    id=f"tp_contract_broken_{contract.id}_{party_id}",
                    kind="betrayal",
                    subject_id=party_id,
                    salience=0.7,
                    tick=current_tick
                ))
                for other_id in contract.party_ids:
                    if other_id != party_id:
                        trust_deltas[other_id] = trust_deltas.get(other_id, 0.0) - 0.25
                        bond_updates.append(SocialBondUpdate(
                            target_id=other_id,
                            sentiment_delta=-0.5, # -0.25 * 2
                            last_interaction_tick_set=current_tick
                        ))

        reputation_delta = 0.1 if outcome == "HONORED" else -0.2
        social_update = SocialUpdate(
            trust_delta=trust_deltas,
            bond_updates=bond_updates,
            reputation_set=None  # Applied per-entity by caller
        )

        return social_update, turning_points

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
        CHA modifier scales familiarity gain rate.
        """
        bond = observer.social.bonds.get(subject_id, SocialBond(target_id=subject_id))
        
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
    def record_betrayal(target_id: int) -> SocialUpdate:
        """Logs a betrayal event impacting reputation."""
        return SocialUpdate(betrayal_increment=1)
