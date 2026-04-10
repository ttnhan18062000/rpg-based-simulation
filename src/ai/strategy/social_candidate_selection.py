"""Service for discovering and ranking potential allies for social contracts. [PHASE 4]"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.core.models.enums import GoalType, HeroClass

if TYPE_CHECKING:
    from src.ai.states.base import AIContext
    from src.core.entities.entity import Entity
    from src.core.models.strategy import ProjectRecord

@dataclass(slots=True)
class CandidateScore:
    """Ranked candidate for social coordination."""
    entity_id: int
    score: float
    drivers: list[str]
    capability_match: bool = True

class SocialCandidateSelectionService:
    """Ranks potential allies using trust, debt, reputation, and role fit."""

    @classmethod
    def find_candidates(
        cls, 
        ctx: AIContext, 
        project: ProjectRecord | None = None,
        max_results: int = 5
    ) -> list[CandidateScore]:
        """Produce a ranked list of potential allies for the given project."""
        actor = ctx.actor
        snapshot = ctx.snapshot
        
        # 1. Identify raw pool (Same faction nearby or in memory)
        # For now, we consider all same-faction entities in the snapshot as potential candidates.
        potential_ids = [
            eid for eid, e in snapshot.entities.items()
            if eid != actor.id and e.identity.faction == actor.identity.faction and e.combat.alive
        ]
        
        # 2. Score each candidate
        scores: list[CandidateScore] = []
        for eid in potential_ids:
            candidate = snapshot.entities[eid]
            score, drivers, cap_match = cls._score_candidate(ctx, candidate, project)
            
            # Filter out extreme negatives (nemeses or those who completely lack capability)
            if score > -2.0:
                scores.append(CandidateScore(
                    entity_id=eid,
                    score=score,
                    drivers=drivers,
                    capability_match=cap_match
                ))
        
        # 3. Rank and bound
        scores.sort(key=lambda s: s.score, reverse=True)
        return scores[:max_results]

    @classmethod
    def _score_candidate(
        cls, 
        ctx: AIContext, 
        candidate: Entity, 
        project: ProjectRecord | None
    ) -> tuple[float, list[str], bool]:
        """Calculate a composite social-strategic score for a candidate."""
        actor = ctx.actor
        score = 0.0
        drivers = []
        cap_match = True
        
        # --- A. Relationship Dynamics (Private) ---
        bond = actor.mind.social.known_bonds.get(candidate.id)
        if bond:
            # Trust & Loyalty are primary drivers
            if bond.trust != 0:
                trust_bias = bond.trust * 2.0
                score += trust_bias
                drivers.append(f"trust:{trust_bias:+.1f}")
            
            if bond.loyalty > 0.2:
                loyalty_bias = bond.loyalty * 1.5
                score += loyalty_bias
                drivers.append(f"loyalty:{loyalty_bias:+.1f}")
            
            # Debt Leverage (If candidate owes us money/favors)
            # bond.debt < 0 means 'They owe us'
            if bond.debt < -0.2:
                debt_leverage = abs(bond.debt) * 1.2
                score += debt_leverage
                drivers.append(f"leverage:{debt_leverage:+.1f}")
            elif bond.debt > 0.5:
                # We owe them, maybe we avoid them if we are greedy/dishonorable?
                # Or maybe we recruit them to pay back? Let's assume neutral for now.
                pass
                
            # Negative Sentiment
            if bond.rivalry > 0.5:
                score -= bond.rivalry * 2.5
                drivers.append(f"rivalry:-{bond.rivalry*2.5:.1f}")
            if bond.resentment > 0.3:
                score -= bond.resentment * 2.0
                drivers.append(f"resentment:-{bond.resentment*2.0:.1f}")
        else:
            # Neutral/Unknown
            drivers.append("unknown:0.0")

        # --- B. Public Reputation (Public) ---
        rep = candidate.identity.reputation
        
        # Scale reputation impact: Higher impact for strangers
        rep_multiplier = 2.0 if not bond else 1.0
        
        # Trustworthiness affects recruitment reliability
        if rep.trustworthiness > 1.0:
            tr_bonus = (rep.trustworthiness / 5.0) * rep_multiplier
            score += tr_bonus
            drivers.append(f"reputable:{tr_bonus:+.1f}")
        elif rep.trustworthiness < -1.0:
            tr_penalty = (abs(rep.trustworthiness) / 4.0) * rep_multiplier
            score -= tr_penalty
            drivers.append(f"unreliable:-{tr_penalty:.1f}")
            
        # Heroism vs Cowardice for high-risk projects
        is_risky = project.urgency > 0.7 if project else False
        if is_risky:
            if rep.cowardice_score > 2.0:
                cw_penalty = (rep.cowardice_score / 3.0)
                score -= cw_penalty
                drivers.append(f"cowardly_risk:-{cw_penalty:.1f}")
            if rep.heroism_score > 2.0:
                hr_bonus = (rep.heroism_score / 4.0)
                score += hr_bonus
                drivers.append(f"heroic_fit:{hr_bonus:+.1f}")

        # Social Stigma Tags
        tags = rep.reputation_tags
        if "Calamity" in tags or "Menace" in tags:
            # Dangerous individuals are only recruited by those with low caution or similar stigma
            aggression = actor.mind.decision.personality.aggression
            if aggression < 0.7:
                score -= 3.0
                drivers.append("danger_stigma:-3.0")
            else:
                score += 1.0
                drivers.append("danger_attraction:+1.0")

        # --- C. Capability & Role Fit ---
        if project:
            required_roles = project.metadata.get("required_roles", [])
            # Simple check: healer role?
            if "healer" in required_roles:
                if candidate.identity.hero_class in (HeroClass.MAGE,): # Simplified check
                    score += 1.5
                    drivers.append("role_fit_healer:+1.5")
                else:
                    cap_match = False

        # --- D. Availability & Load ---
        # If candidate is already in a major project, they are less attractive
        c_strat = candidate.mind.strategic
        if c_strat.current_project_id:
            # Check project urgency/importance? 
            # For now, simple penalty for being busy
            score -= 0.8
            drivers.append("busy:-0.8")
            
        # Proximity (Tactical feasibility)
        dist = actor.spatial.pos.manhattan(candidate.spatial.pos)
        if dist > 30: # 3 regions away
            score -= 0.5
            drivers.append("distant:-0.5")

        return score, drivers, cap_match
