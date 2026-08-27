"""
src/domains/cooperation/evaluators.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 — Help Need and Partner Fit Evaluators.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any, Mapping
from src.core.state import EntityState, AuthoritativeState
from src.core.strategic import RiskLevel
from src.domains.cooperation.postures import CooperationPosture

@dataclass(frozen=True, slots=True)
class HelpNeed:
    key: str
    severity: float
    reason: str
    required_support_tags: Tuple[str, ...] = field(default_factory=tuple)
    acceptable_postures: Tuple[str, ...] = field(default_factory=tuple)

class HelpNeedEvaluator:
    @staticmethod
    def evaluate(
        entity: EntityState,
        state: AuthoritativeState,
    ) -> Tuple[HelpNeed, ...]:
        needs = []
        
        # Check active objective and project
        current_obj_id = entity.strategic.current_objective_id
        current_proj_id = entity.strategic.current_project_id
        
        if not current_obj_id:
            return ()
            
        # Get active objective to see if it is high risk or requires support
        objective = None
        if current_proj_id and current_proj_id in entity.strategic.projects:
            proj = entity.strategic.projects[current_proj_id]
            for obj in proj.objectives:
                if obj.id == current_obj_id:
                    objective = obj
                    break
                    
        # Check combat risk belief
        combat_belief = entity.strategic.beliefs.get("combat_risk")
        risk_level = RiskLevel.NORMAL
        if combat_belief:
            risk_level = combat_belief.get("level", RiskLevel.NORMAL)
            
        # Check prior near-death turning points
        has_near_death = any(tp.kind == "near_death" for tp in entity.strategic.turning_points)

        # 1. Risky combat creates combat support need
        if risk_level in (RiskLevel.HIGH, RiskLevel.EXTREME) or has_near_death:
            sev = 0.8 if risk_level == RiskLevel.EXTREME else 0.6
            if has_near_death:
                sev += 0.15
            sev = min(sev, 1.0)
            
            # Urgency booster based on HP
            if entity.combat.hp < entity.combat.max_hp * 0.4:
                sev = min(sev + 0.2, 1.0)
                
            needs.append(HelpNeed(
                key="combat_support_needed",
                severity=sev,
                reason="Combat capability risk is high or near_death history exists",
                required_support_tags=("damage", "tank"),
                acceptable_postures=(CooperationPosture.REQUEST_HELP, CooperationPosture.HIRE_SUPPORT)
            ))
            
        # 2. Low HP creates healer/protection need
        if entity.combat.hp < entity.combat.max_hp * 0.3:
            needs.append(HelpNeed(
                key="healer_needed",
                severity=0.9,
                reason="Critical low HP",
                required_support_tags=("healer", "protector"),
                acceptable_postures=(CooperationPosture.REQUEST_HELP, CooperationPosture.HIRE_SUPPORT, CooperationPosture.DEFER_NO_PARTNER)
            ))
            
        # 3. Unknown route/region creates guide/scout need
        nav_target = entity.navigation.target
        if nav_target and getattr(entity.navigation, "region_id", None) is None:
            needs.append(HelpNeed(
                key="guide_needed",
                severity=0.5,
                reason="Target lies in unexplored region",
                required_support_tags=("guide", "scout"),
                acceptable_postures=(CooperationPosture.REQUEST_HELP, CooperationPosture.HIRE_SUPPORT)
            ))
            
        # 4. Heavy load creates carry support need
        gold = entity.inventory.gold
        if gold > 1000:
            needs.append(HelpNeed(
                key="carry_support_needed",
                severity=0.4,
                reason="Possessing heavy gold stack",
                required_support_tags=("carry", "guard"),
                acceptable_postures=(CooperationPosture.REQUEST_HELP, CooperationPosture.HIRE_SUPPORT)
            ))

        return tuple(needs)


@dataclass(frozen=True, slots=True)
class PartnerFitReport:
    candidate_id: int
    fit_score: float
    trust_score: float
    capability_match: float
    objective_alignment: float
    risk: float
    reasons: Tuple[str, ...]

class PartnerFitEvaluator:
    @staticmethod
    def evaluate(
        requester: EntityState,
        candidate: EntityState,
        help_needs: Tuple[HelpNeed, ...],
        state: AuthoritativeState,
    ) -> PartnerFitReport:
        reasons = []
        
        # Determine baseline trust score (from private trust first, public second)
        trust_score = requester.social.trust_history.get(candidate.id, 0.5)
        # Check familiarity
        fam = requester.social.familiarity_history.get(candidate.id, 0.0)
        
        # Check bonds
        bond = requester.social.bonds.get(candidate.id)
        if bond:
            trust_score = max(trust_score, bond.sentiment)
            
        reasons.append(f"Base trust score evaluated at {trust_score:.2f}")

        # Penalty for past abandonment/betrayal
        grudge = requester.social.grudge_history.get(candidate.id, 0.0)
        if grudge > 0.0:
            trust_score = max(0.0, trust_score - grudge)
            reasons.append(f"Distrust penalty from past grudge: -{grudge:.2f}")

        # Check role compatibility for needs
        capability_match = 0.5
        candidate_role = candidate.combat.tactical_role
        
        # Match candidate role with required support tags
        for need in help_needs:
            if "combat_support" in need.key or "healer" in need.key:
                if candidate_role == "VANGUARD" and "tank" in need.required_support_tags:
                    capability_match = min(capability_match + 0.3, 1.0)
                    reasons.append("Candidate tactical role VANGUARD fits support tag: tank")
                elif candidate_role == "SUPPORT" and "healer" in need.required_support_tags:
                    capability_match = min(capability_match + 0.4, 1.0)
                    reasons.append("Candidate tactical role SUPPORT fits support tag: healer")
                elif candidate_role == "STRIKER" and "damage" in need.required_support_tags:
                    capability_match = min(capability_match + 0.25, 1.0)
                    reasons.append("Candidate tactical role STRIKER fits support tag: damage")

        # Check active objective alignment
        objective_alignment = 0.5
        req_obj = requester.strategic.current_objective_id
        cand_obj = candidate.strategic.current_objective_id
        if req_obj and cand_obj and req_obj == cand_obj:
            objective_alignment = 1.0
            reasons.append("Perfect objective alignment detected")
        elif req_obj and cand_obj:
            # Conflicting active objective reduces alignment
            objective_alignment = 0.2
            reasons.append("Conflicting active objective reduces alignment")

        # Cost penalty check
        cost = 0
        poor_penalty = 0.0
        # TODO(TCK-20260824-OCCUPATION-CHANGE-TRIGGER): EntityRole(1) is SHOPKEEPER
        # (src/core/enums.py:8), not a distinct "Hireling"/"Guild Merchant" role. Now that
        # role_set is runtime-reachable (OccupationChangeGoalScorer), any entity that
        # transitions into SHOPKEEPER is silently charged a hireling cost here. Disclosed,
        # not fixed -- out of that ticket's scope.
        # If candidate has HIRE_SUPPORT posture in mind, they want pay
        if candidate.identity.role == 1: # Guild Merchant/Hireling
            cost = 20
            if requester.inventory.gold < cost:
                poor_penalty = 0.4
                reasons.append("Cannot afford hireling cost")

        # Risk score calculation
        risk = 0.1
        if trust_score < 0.3:
            risk += 0.5
            reasons.append("Distrust risk factor added")
        if candidate.combat.hp < candidate.combat.max_hp * 0.4:
            risk += 0.3
            reasons.append("Candidate health risk factor added")

        # Final fit score: aggregate trust, capability, alignment, minus risk and poor penalty
        fit_score = (trust_score * 0.35 + capability_match * 0.3 + objective_alignment * 0.2 + (1.0 - risk) * 0.15)
        fit_score = max(0.0, min(fit_score - poor_penalty, 1.0))
        
        return PartnerFitReport(
            candidate_id=candidate.id,
            fit_score=fit_score,
            trust_score=trust_score,
            capability_match=capability_match,
            objective_alignment=objective_alignment,
            risk=risk,
            reasons=tuple(reasons)
        )
