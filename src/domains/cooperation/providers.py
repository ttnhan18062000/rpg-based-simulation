"""
src/domains/cooperation/providers.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 — Partner Candidate Provider.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List
from src.core.state import EntityState, AuthoritativeState
from src.domains.cooperation.evaluators import HelpNeed

@dataclass(frozen=True, slots=True)
class PartnerCandidate:
    entity_id: int
    relationship_score: float
    trust_score: float
    role_fit_score: float
    availability_score: float
    cost_gold: int = 0
    risk_penalty: float = 0.0
    reason: str | None = None

@dataclass(frozen=True, slots=True)
class CandidateBudget:
    max_candidates: int = 5
    spatial_radius: float = 15.0

class PartnerCandidateProvider:
    @staticmethod
    def get_candidates(
        entity: EntityState,
        state: AuthoritativeState,
        help_needs: Tuple[HelpNeed, ...],
        budget: CandidateBudget = CandidateBudget(),
    ) -> Tuple[PartnerCandidate, ...]:
        candidates = []
        my_pos = entity.navigation.position
        
        # Scoped scan (spatial + trusted social)
        for cand_id, cand in state.entities.items():
            if cand_id == entity.id:
                continue
                
            # Exclude dead or inactive
            if not cand.lifecycle.active or not cand.combat.alive:
                continue
                
            # Exclude hostiles
            if cand.identity.faction != entity.identity.faction:
                # TODO(TCK-20260824-OCCUPATION-CHANGE-TRIGGER): EntityRole(1) is SHOPKEEPER
                # (src/core/enums.py:8), not a distinct "Hireling"/"Guild Merchant" role. Now
                # that role_set is runtime-reachable (OccupationChangeGoalScorer), any entity
                # that transitions into SHOPKEEPER is silently treated as a Hireling here for
                # cooperation-partner selection. Disclosed, not fixed -- out of that ticket's scope.
                # Unless special hireling or merchant
                if cand.identity.role != 1: # Let role 1 (Hireling) pass regardless of faction (or if faction matches)
                    continue

            # Calculate spatial distance (cheap bounding box check first)
            c_pos = cand.navigation.position
            dx = my_pos[0] - c_pos[0]
            dy = my_pos[1] - c_pos[1]
            if abs(dx) > budget.spatial_radius or abs(dy) > budget.spatial_radius:
                # Still check trusted social fallback
                trust = entity.social.trust_history.get(cand_id, 0.5)
                if trust <= 0.7:
                    continue
                dist = (dx**2 + dy**2)**0.5
            else:
                dist = (dx**2 + dy**2)**0.5
            
            # Check social ties
            trust = entity.social.trust_history.get(cand_id, 0.5)
            familiarity = entity.social.familiarity_history.get(cand_id, 0.0)
            
            # Keep if nearby or highly trusted
            if dist <= budget.spatial_radius or trust > 0.7:
                # Score compatibility components
                availability = 1.0 - (dist / budget.spatial_radius) if dist > 0.0 else 1.0
                availability = max(0.1, min(availability, 1.0))
                
                # Check active contract load
                if cand.strategic.contracts:
                    availability = max(0.05, availability - 0.3)
                    
                role_fit = 0.5
                if cand.combat.tactical_role == "SUPPORT":
                    role_fit = 0.8
                elif cand.combat.tactical_role == "VANGUARD":
                    role_fit = 0.7
                    
                # TODO(TCK-20260824-OCCUPATION-CHANGE-TRIGGER): EntityRole(1) is SHOPKEEPER
                # (src/core/enums.py:8), not a distinct "Hireling"/"Guild Merchant" role. Now
                # that role_set is runtime-reachable (OccupationChangeGoalScorer), any entity
                # that transitions into SHOPKEEPER is silently charged a hireling cost here.
                # Disclosed, not fixed -- out of that ticket's scope.
                cost = 20 if cand.identity.role == 1 else 0
                
                # Grudge penalty
                grudge = entity.social.grudge_history.get(cand_id, 0.0)
                risk_pen = grudge * 0.5
                
                reason_str = "Within spatial radius" if dist <= budget.spatial_radius else "Highly trusted ally"
                
                candidates.append(PartnerCandidate(
                    entity_id=cand_id,
                    relationship_score=familiarity,
                    trust_score=trust,
                    role_fit_score=role_fit,
                    availability_score=availability,
                    cost_gold=cost,
                    risk_penalty=risk_pen,
                    reason=reason_str
                ))
                
        # Sort candidates deterministically: prefer highest trust + role fit + availability
        candidates.sort(key=lambda x: (x.trust_score * 0.4 + x.role_fit_score * 0.3 + x.availability_score * 0.3 - x.risk_penalty), reverse=True)
        
        # Cap candidate count
        return tuple(candidates[:budget.max_candidates])
