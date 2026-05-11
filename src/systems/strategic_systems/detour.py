# Compliance IDs: STRAT-006, STRAT-008, STRAT-009, STRAT-012, STRAT-204, STRAT-205, STRAT-206, STRAT-207, STRAT-208, STRAT-209, STRAT-210, STRAT-211, STRAT-212
"""
Detour Suggestion System for Strategic Cognition.

Generates detour suggestions from blockers and leads within bounded
breadth/depth limits defined by the entity's CognitionProfile.

Covers:
- Part 1 §Strategic: Detours are suggested from blockers and leads within breadth/depth limits
- Part 1 §Strategic: Rejected/tested leads are suppressed to avoid blind retries
"""
from __future__ import annotations
from dataclasses import replace
from typing import List, Optional

from src.core.state import EntityState
from src.core.strategic import (
    BlockerState, LeadState, LeadCertainty, ObjectiveState, ObjectiveStatus,
    CognitionProfile
)
from src.core.updates import StrategicUpdate


class DetourSuggestionResult:
    """A single detour suggestion linking a blocker to a lead."""
    __slots__ = ('blocker_id', 'lead_id', 'objective_kind', 'target', 'score')

    def __init__(self, blocker_id: str, lead_id: str, objective_kind: str,
                 target: Optional[str], score: float):
        self.blocker_id = blocker_id
        self.lead_id = lead_id
        self.objective_kind = objective_kind
        self.target = target
        self.score = score


class DetourSuggestionSystem:
    """
    Pure decision logic: reads entity state, returns detour suggestions.
    Does NOT mutate any state directly.
    Logic ID: STRAT-004 (Leads are typed records with provenance and expiration)
    """

    @staticmethod
    def suggest_detours(
        entity: EntityState,
        current_tick: int
    ) -> List[DetourSuggestionResult]:
        """
        Generate detour suggestions from unresolved blockers paired with relevant leads.
        Logic ID: STRAT-201 (Leads have kind)
        Logic ID: STRAT-202 (Leads have subject)
        Logic ID: STRAT-203 (Leads have certainty)
        Logic ID: STRAT-204 (Leads have source trust)
        VERIFIED v2: strategic_detour_suggestion

        Rules:
        1. Only considers unresolved blockers.
        2. Only considers leads that have NOT been tested and failed.
        3. Limits results to profile.detour_breadth.
        4. Higher certainty leads score higher.
        5. Leads with trusted sources score higher.
        """
        profile = entity.strategic.profile
        strategic = entity.strategic

        # Collect unresolved blockers
        unresolved_blockers = [
            b for b in strategic.blockers.values()
            if not b.resolved
        ]

        if not unresolved_blockers:
            return []

        usable_leads = [
            l for l in strategic.leads.values()
            if (not l.tested or (l.test_outcome == 'FAILURE' and l.failure_count < 3))
            and l.certainty != LeadCertainty.EXHAUSTED 
            and l.suppression_until_tick < current_tick
        ]

        if not usable_leads:
            return []

        # Match blockers to leads by subject
        suggestions: List[DetourSuggestionResult] = []

        for blocker in unresolved_blockers:
            for lead in usable_leads:
                if not DetourSuggestionSystem._subjects_match(blocker, lead):
                    continue

                score = DetourSuggestionSystem._score_detour(
                    blocker, lead, strategic.source_trust
                )

                objective_kind = DetourSuggestionSystem._infer_objective_kind(blocker, lead)

                target = lead.detail if lead.kind == "location" and lead.detail else lead.subject

                suggestions.append(DetourSuggestionResult(
                    blocker_id=blocker.id,
                    lead_id=lead.id,
                    objective_kind=objective_kind,
                    target=target,
                    score=score
                ))

        # Sort by score descending, limit to breadth
        suggestions.sort(key=lambda s: s.score, reverse=True)
        return suggestions[:profile.detour_breadth]

    @staticmethod
    def suppress_exhausted_leads(entity: EntityState, current_tick: int) -> StrategicUpdate:
        """
        Part 1 §Strategic: Rejected/tested leads are suppressed to avoid blind retries.
        Implements Phase 6 Strategic Memory.
        Logic ID: STRAT-205 (Leads can be tested)
        """
        leads_to_update = []

        for lead in entity.strategic.leads.values():
            if lead.tested and lead.test_outcome == 'FAILURE':
                new_count = lead.failure_count + 1
                # If failed 3 times, mark as EXHAUSTED
                if new_count >= 3:
                    if lead.certainty != LeadCertainty.EXHAUSTED:
                        leads_to_update.append(replace(lead, certainty=LeadCertainty.EXHAUSTED, failure_count=new_count))
                else:
                    # Apply temporary suppression (e.g. 500 ticks as per Phase 6 spec)
                    suppression_tick = current_tick + 500
                    if lead.suppression_until_tick < suppression_tick:
                        leads_to_update.append(replace(lead, suppression_until_tick=suppression_tick, failure_count=new_count))

        if not leads_to_update:
            return StrategicUpdate()

        return StrategicUpdate(leads_add_or_update=leads_to_update)

    @staticmethod
    def enforce_bandwidth(
        entity: EntityState,
        current_tick: int
    ) -> StrategicUpdate:
        """
        Part 1 §Strategic: Leads and concerns are retained under profile-specific limits.

        Drops the lowest-scoring excess items when over capacity.
        """
        profile = entity.strategic.profile
        leads_to_remove: list[str] = []
        concerns_to_remove: list[str] = []

        # Enforce lead bandwidth
        active_leads = sorted(
            entity.strategic.leads.values(),
            key=lambda l: _certainty_score(l.certainty),
            reverse=True
        )
        if len(active_leads) > profile.max_leads:
            excess = active_leads[profile.max_leads:]
            leads_to_remove = [l.id for l in excess]

        # Enforce concern bandwidth
        active_concerns = sorted(
            entity.strategic.concerns.values(),
            key=lambda c: c.urgency,
            reverse=True
        )
        if len(active_concerns) > profile.max_concerns:
            excess = active_concerns[profile.max_concerns:]
            concerns_to_remove = [c.id for c in excess]

        if not leads_to_remove and not concerns_to_remove:
            return StrategicUpdate()

        return StrategicUpdate(
            leads_remove=leads_to_remove,
            concerns_remove=concerns_to_remove,
            overload_source_set="bandwidth" if leads_to_remove else None,
            overload_tick_set=current_tick if leads_to_remove else None
        )

    @staticmethod
    def _subjects_match(blocker: BlockerState, lead: LeadState) -> bool:
        """Check if a lead might resolve a blocker."""
        # Direct subject match
        if blocker.subject == lead.subject:
            return True
        # Material blocker + location lead for the material
        if blocker.kind == "material" and lead.kind == "location":
            if not lead.detail: return False
            return blocker.subject in lead.detail or lead.subject == "resource_node"
            
        # Inventory capacity blocker -> Location lead for town/shop/home
        if blocker.kind == "inventory" and blocker.subject == "capacity":
            return lead.kind == "location" and lead.subject in ("town", "shop", "home")
            
        # Danger/Safety blocker -> Location lead for safe zone/town
        if blocker.kind == "danger":
            return lead.kind == "location" and lead.subject in ("safe_zone", "town", "origin")
            
        return False

    @staticmethod
    def _score_detour(blocker, lead, source_trust) -> float:
        """Score a detour suggestion."""
        base = blocker.severity * 50

        # Certainty bonus
        certainty_bonus = _certainty_score(lead.certainty) * 30

        # Source trust bonus
        trust_bonus = 0.0
        if lead.source_entity_id and lead.source_entity_id in source_trust:
            trust_bonus = source_trust[lead.source_entity_id].trust * 20

        return base + certainty_bonus + trust_bonus

    @staticmethod
    def _infer_objective_kind(blocker: BlockerState, lead: LeadState) -> str:
        """Infer the right objective kind from a blocker+lead pair."""
        if blocker.kind == "material":
            if lead.kind == "location":
                return "reach_location"
            return "acquire_item"
        if blocker.kind == "access":
            return "reach_location"
        if blocker.kind == "inventory":
            return "reach_location" # Return to town to sell
        if blocker.kind == "danger":
            return "reach_location" # Retreat to safe zone
        if blocker.kind == "social" or blocker.kind == "group":
            return "social_engage"
        return "investigate"


def _certainty_score(certainty: LeadCertainty) -> float:
    """Convert LeadCertainty to a numeric score."""
    return {
        LeadCertainty.PRECISE: 1.0,
        LeadCertainty.APPROXIMATE: 0.7,
        LeadCertainty.VAGUE: 0.3,
        LeadCertainty.EXHAUSTED: 0.0
    }.get(certainty, 0.0)
