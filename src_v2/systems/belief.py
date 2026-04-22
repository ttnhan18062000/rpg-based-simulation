"""
Belief Cycle System.

Manages the lifecycle of beliefs: rumors → observations → decay.

Covers:
- LEG-RPG-150: Belief cycle (Rumors)
- LEG-RPG-125: Contradiction degrades certainty
- Part 1 §Strategic: Knowledge remains uncertain until resolved
"""
from __future__ import annotations
from dataclasses import replace, dataclass, field
from typing import Dict, List, Optional

from src_v2.core.state import EntityState
from src_v2.core.strategic import (
    LeadState, LeadCertainty, HypothesisState, SourceTrustEntry
)
from src_v2.core.updates import StrategicUpdate


@dataclass(frozen=True, slots=True)
class BeliefEntry:
    """A single belief about the world."""
    id: str
    subject: str
    claim: str
    certainty: float = 0.5  # 0.0 to 1.0
    source: str = "observation"  # 'observation', 'rumor', 'deduction'
    source_entity_id: Optional[int] = None
    created_tick: int = 0
    last_refreshed_tick: int = 0
    contradictions: int = 0


class BeliefCycleSystem:
    """
    Pure decision logic for belief management.
    Does NOT mutate state directly — returns StrategicUpdates.
    """

    @staticmethod
    def decay_stale_beliefs(
        entity: EntityState,
        current_tick: int,
        decay_rate: float = 0.02,
        stale_threshold: int = 50
    ) -> StrategicUpdate:
        """
        LEG-RPG-150: Beliefs decay over time.
        Leads that haven't been refreshed lose certainty.
        """
        leads_to_update = []

        for lead in entity.strategic.leads.values():
            ticks_since = current_tick - lead.discovered_tick
            if ticks_since < stale_threshold:
                continue
            if lead.certainty == LeadCertainty.EXHAUSTED:
                continue
            if lead.certainty == LeadCertainty.PRECISE:
                # Direct observations decay slower
                continue

            # Demote certainty
            current = lead.certainty
            if current == LeadCertainty.APPROXIMATE:
                new_certainty = LeadCertainty.VAGUE
            elif current == LeadCertainty.VAGUE:
                new_certainty = LeadCertainty.EXHAUSTED
            else:
                continue

            leads_to_update.append(replace(lead, certainty=new_certainty))

        if not leads_to_update:
            return StrategicUpdate()

        return StrategicUpdate(leads_add_or_update=leads_to_update)

    @staticmethod
    def process_rumor(
        entity: EntityState,
        rumor_subject: str,
        rumor_detail: str,
        source_entity_id: int,
        current_tick: int
    ) -> StrategicUpdate:
        """
        LEG-RPG-150: Rumors have lower certainty than direct observation.
        """
        lead = LeadState(
            id=f"lead_rumor_{rumor_subject}_{current_tick}",
            kind="location",
            subject=rumor_subject,
            detail=rumor_detail,
            discovered_tick=current_tick,
            certainty=LeadCertainty.VAGUE,
            source_entity_id=source_entity_id
        )
        return StrategicUpdate(leads_add_or_update=[lead])

    @staticmethod
    def process_observation(
        entity: EntityState,
        subject: str,
        detail: str,
        current_tick: int
    ) -> StrategicUpdate:
        """
        Direct observations create PRECISE leads.
        """
        lead = LeadState(
            id=f"lead_obs_{subject}_{current_tick}",
            kind="location",
            subject=subject,
            detail=detail,
            discovered_tick=current_tick,
            certainty=LeadCertainty.PRECISE
        )
        return StrategicUpdate(leads_add_or_update=[lead])

    @staticmethod
    def apply_contradiction(
        entity: EntityState,
        lead_id: str,
        contradicting_evidence: str
    ) -> StrategicUpdate:
        """
        LEG-RPG-125: Contradiction degrades certainty.
        """
        lead = entity.strategic.leads.get(lead_id)
        if not lead:
            return StrategicUpdate()

        # Demote certainty
        current = lead.certainty
        if current == LeadCertainty.PRECISE:
            new_certainty = LeadCertainty.APPROXIMATE
        elif current == LeadCertainty.APPROXIMATE:
            new_certainty = LeadCertainty.VAGUE
        elif current == LeadCertainty.VAGUE:
            new_certainty = LeadCertainty.EXHAUSTED
        else:
            return StrategicUpdate()

        updated_lead = replace(lead, certainty=new_certainty)

        # Also degrade supporting hypotheses
        hypotheses_to_update = []
        for hyp in entity.strategic.hypotheses.values():
            if lead_id in hyp.supporting_lead_ids:
                new_confidence = max(0.0, hyp.confidence - 0.2)
                hypotheses_to_update.append(replace(hyp, confidence=new_confidence))

        return StrategicUpdate(
            leads_add_or_update=[updated_lead],
            hypotheses_add_or_update=hypotheses_to_update
        )

    @staticmethod
    def estimate_threat(
        entity: EntityState,
        region_id: str
    ) -> float:
        """
        LEG-RPG-150: Threat estimation from belief state.
        Aggregates danger-related beliefs about a region.
        """
        threat = 0.0

        # From concerns
        for concern in entity.strategic.concerns.values():
            if concern.kind == "danger" and concern.source == region_id:
                threat += concern.urgency

        # From leads about the region
        for lead in entity.strategic.leads.values():
            if lead.subject == region_id and lead.kind == "event":
                certainty_weight = {
                    LeadCertainty.PRECISE: 1.0,
                    LeadCertainty.APPROXIMATE: 0.6,
                    LeadCertainty.VAGUE: 0.2,
                    LeadCertainty.EXHAUSTED: 0.0
                }.get(lead.certainty, 0.0)
                threat += 0.3 * certainty_weight

        return min(1.0, threat)
