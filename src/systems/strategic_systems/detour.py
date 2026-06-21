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
    BlockerState, LeadKind, LeadState, LeadCertainty, ObjectiveState, ObjectiveStatus,
    CognitionProfile
)
from src.core.updates import StrategicUpdate
from src.engine.domain.lead_routing import LeadRoutingSystem


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
                    blocker, lead, strategic.source_trust, strategic.beliefs
                )

                objective_kind = DetourSuggestionSystem._infer_objective_kind(blocker, lead)

                # PERSON and CONCEPT leads use LeadRoutingSystem for target resolution
                if lead.kind in (LeadKind.PERSON, LeadKind.CONCEPT):
                    _, target = LeadRoutingSystem.resolve_objective_kind(lead)
                else:
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
        import logging
        logger = logging.getLogger(__name__)

        profile = entity.strategic.profile
        leads_to_remove: list[str] = []
        concerns_to_remove: list[str] = []
        hypotheses_to_remove: list[str] = []
        projects_to_remove: list[str] = []

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

        # Enforce hypothesis capacity
        active_hypotheses = sorted(
            entity.strategic.hypotheses.values(),
            key=lambda h: h.confidence,
            reverse=True
        )
        if len(active_hypotheses) > profile.max_hypotheses:
            excess = active_hypotheses[profile.max_hypotheses:]
            hypotheses_to_remove = [h.id for h in excess]

        # Enforce project capacity
        active_proj_id = entity.strategic.current_project_id
        def _proj_priority(p):
            if p.id == active_proj_id:
                return (1, p.id)
            return (0, p.id)
            
        all_projects = sorted(
            entity.strategic.projects.values(),
            key=_proj_priority,
            reverse=True
        )
        if len(all_projects) > profile.max_active_projects:
            excess = all_projects[profile.max_active_projects:]
            projects_to_remove = [p.id for p in excess]

        # Logging observability events
        if leads_to_remove:
            logger.debug(
                f"[Tick {current_tick}] CognitionCapacityTrimmed: Entity {entity.id} "
                f"trimmed leads. Before: {len(active_leads)}, After: {len(active_leads) - len(leads_to_remove)}, "
                f"Dropped: {leads_to_remove}"
            )
        if concerns_to_remove:
            logger.debug(
                f"[Tick {current_tick}] CognitionCapacityTrimmed: Entity {entity.id} "
                f"trimmed concerns. Before: {len(active_concerns)}, After: {len(active_concerns) - len(concerns_to_remove)}, "
                f"Dropped: {concerns_to_remove}"
            )
        if hypotheses_to_remove:
            logger.debug(
                f"[Tick {current_tick}] CognitionCapacityTrimmed: Entity {entity.id} "
                f"trimmed hypotheses. Before: {len(active_hypotheses)}, After: {len(active_hypotheses) - len(hypotheses_to_remove)}, "
                f"Dropped: {hypotheses_to_remove}"
            )
        if projects_to_remove:
            logger.debug(
                f"[Tick {current_tick}] CognitionCapacityTrimmed: Entity {entity.id} "
                f"trimmed projects. Before: {len(all_projects)}, After: {len(all_projects) - len(projects_to_remove)}, "
                f"Dropped: {projects_to_remove}"
            )

        if not leads_to_remove and not concerns_to_remove and not hypotheses_to_remove and not projects_to_remove:
            return StrategicUpdate()

        return StrategicUpdate(
            leads_remove=leads_to_remove,
            concerns_remove=concerns_to_remove,
            hypotheses_remove=hypotheses_to_remove,
            projects_remove=projects_to_remove,
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
    def _score_detour(blocker, lead, source_trust, beliefs) -> float:
        """Score a detour suggestion."""
        base = blocker.severity * 50

        # Certainty bonus
        certainty_bonus = _certainty_score(lead.certainty) * 30

        # Source trust bonus
        trust_bonus = 0.0
        if lead.source_entity_id and lead.source_entity_id in source_trust:
            trust_bonus = source_trust[lead.source_entity_id].trust * 20

        # Contradiction penalty
        contradiction_penalty = 0.0
        matching_belief = next((b for b in beliefs.values() if b.subject == lead.subject), None)
        if matching_belief:
            contradiction_penalty = matching_belief.contradictions * 25.0

        return base + certainty_bonus + trust_bonus - contradiction_penalty

    @staticmethod
    def _infer_objective_kind(blocker: BlockerState, lead: LeadState) -> str:
        """Infer the right objective kind from a blocker+lead pair.

        PERSON and CONCEPT leads are routed via LeadRoutingSystem regardless
        of blocker kind (Logic ID: E42E-002).
        """
        # PERSON and CONCEPT leads have their own routing logic (E42E)
        if lead.kind == LeadKind.PERSON or lead.kind == LeadKind.CONCEPT:
            obj_kind, _ = LeadRoutingSystem.resolve_objective_kind(lead)
            return obj_kind.value

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
