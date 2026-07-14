"""
src/domains/adventure/service.py
───────────────────────────────────────────────────────────────────────────────
Phase 3 — AdventureDecisionService

Selects the best route candidate for an entity, applies imperfect scoring bias,
and constructs the final bridge state using RouteToProjectMapper.
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Optional

from src.core.state import EntityState, ResourceNodeState
from src.domains.adventure.schema import (
    RouteFamily,
    AdventureRouteOption,
    RejectedRoute,
    AdventureDecisionResult,
)
from src.domains.adventure.scoring import AdventureRouteScorer
from src.domains.adventure.mapper import RouteToProjectMapper


class AdventureDecisionService:
    """
    Evaluates and selects the optimal adventure route candidate for an entity.
    Coordinates route candidate generation, scoring, and mapping.
    """

    @staticmethod
    def decide(
        entity: EntityState,
        candidates: List[AdventureRouteOption],
        tick: int = 0,
        resource_nodes: Optional[Dict[int, ResourceNodeState]] = None,
        faction_directives: Optional[list] = None,
        factions: Optional[Any] = None,
    ) -> AdventureDecisionResult:
        """
        Evaluate candidates, score them using Personality biased heuristics,
        and select the highest scoring valid option.
        
        Args:
            entity: The current EntityState (immutable view)
            candidates: List of generated AdventureRouteOptions
            tick: Current simulation tick
            
        Returns:
            AdventureDecisionResult representing the selected choice, rejections,
            and proposed strategic bridge objects.
        """
        if not candidates:
            # Return deferred/default empty result
            defer_route = AdventureRouteOption(
                family=RouteFamily.DEFER_WITH_REASON,
                score=0.0,
                confidence=1.0,
                expected_benefit=0.0,
                expected_risk=0.0,
                reason="No candidate routes generated.",
            )
            return AdventureDecisionResult(
                selected=defer_route,
                rejected=(),
                proposed_project=None,
                proposed_objective=None,
                trace={"reason": "no_candidates"},
            )

        # 1. Score all candidates using AdventureRouteScorer
        scored_candidates: List[AdventureRouteOption] = []
        for cand in candidates:
            scored = AdventureRouteScorer.score(
                entity, cand,
                resource_nodes=resource_nodes,
                faction_directives=faction_directives,
                factions=factions,
            )
            scored_candidates.append(scored)

        # 2. Separate into valid and blocked/rejected lists
        valid_candidates = [c for c in scored_candidates if not c.blockers]
        blocked_candidates = [c for c in scored_candidates if c.blockers]

        # 3. Sort candidates to find the best selection
        # Criteria: Highest score, then highest confidence, then expected benefit
        valid_candidates.sort(
            key=lambda x: (x.score, x.confidence, x.expected_benefit),
            reverse=True,
        )

        selected: Optional[AdventureRouteOption] = None
        rejected_list: List[RejectedRoute] = []

        if valid_candidates:
            selected = valid_candidates[0]
            # Remaining valid candidates are rejected
            for r_cand in valid_candidates[1:]:
                rejected_list.append(
                    RejectedRoute(
                        family=r_cand.family,
                        reason="Lower score than selected option.",
                        score=r_cand.score,
                    )
                )
        else:
            # No valid candidates (e.g. all blocked)
            selected = AdventureRouteOption(
                family=RouteFamily.DEFER_WITH_REASON,
                score=0.0,
                confidence=1.0,
                expected_benefit=0.0,
                expected_risk=0.0,
                reason="All candidates are blocked.",
            )

        # Process blocked candidates as rejected
        for b_cand in blocked_candidates:
            blocker_str = ", ".join(b_cand.blockers)
            rejected_list.append(
                RejectedRoute(
                    family=b_cand.family,
                    reason=f"Blocked: {blocker_str}",
                    score=b_cand.score,
                )
            )

        # 4. Map the selected route to strategic states
        proposed_project = None
        proposed_objective = None
        if selected and selected.family != RouteFamily.DEFER_WITH_REASON:
            # Determine target and target_position from requirements/opportunity if available
            # Let's extract first opportunity or location details if they exist in source_opportunity_ids
            target = None
            target_pos = None
            if selected.target_node_id is not None:
                target = str(selected.target_node_id)
            elif selected.source_opportunity_ids:
                target = selected.source_opportunity_ids[0]
            
            proj, obj = RouteToProjectMapper.map_to_states(
                family=selected.family,
                entity_id=entity.id,
                target=target,
                target_pos=target_pos,
                tick=tick,
            )
            proposed_project = proj
            proposed_objective = obj

        # Build explainable trace record
        trace = {
            "candidate_count": len(candidates),
            "valid_count": len(valid_candidates),
            "blocked_count": len(blocked_candidates),
            "selected_score": selected.score if selected else 0.0,
            # scored_candidates: consumed by DecisionTraceWriter in AdventureDecisionPhase
            "scored_candidates": scored_candidates,
        }

        return AdventureDecisionResult(
            selected=selected,
            rejected=tuple(rejected_list),
            proposed_project=proposed_project,
            proposed_objective=proposed_objective,
            trace=trace,
        )
