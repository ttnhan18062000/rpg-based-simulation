"""
src/domains/information/router.py
───────────────────────────────────────────────────────────────────────────────
Phase 5 — InformationQueryRouter

Given a subjective query, routes to matched local or known candidate sources,
evaluating trust, relevance, cost limits, and proximity limits.
"""

from __future__ import annotations
from typing import Tuple, List, Dict
import math

from src.core.state import EntityState, AuthoritativeState
from src.domains.information.schema import (
    InformationQuery,
    InformationSourceProfile,
    InformationSourceCandidate,
)


class InformationQueryRouter:
    """
    Routes queries to matched candidates based on source scope, location, trust, and gold.
    """

    @staticmethod
    def route(
        entity: EntityState,
        query: InformationQuery,
        state: AuthoritativeState,
        profiles: List[InformationSourceProfile],
        budget_max_gold: int = 100,
    ) -> Tuple[InformationSourceCandidate, ...]:
        """
        Evaluate candidate profiles against the query subject/kind.
        """
        candidates: List[InformationSourceCandidate] = []
        entity_pos = entity.navigation.position or (0.0, 0.0)

        # Retrieve source trust from strategic entries
        strat = getattr(entity, "strategic", None)
        source_trust_map = getattr(strat, "source_trust", {}) or {}

        # 1. Scope mapping helpers
        def matches_scope(kind: str, scopes: Tuple[str, ...]) -> bool:
            if kind == "material_source" and "common_resource_sources" in scopes:
                return True
            if kind == "recipe_definition" and "recipe_requirements" in scopes:
                return True
            if kind == "danger_rating" and "regional_danger" in scopes:
                return True
            return False

        for prof in profiles:
            # 2. Check scopes compatibility
            if not matches_scope(query.kind, prof.knowledge_scopes) and prof.source_kind != "traveler":
                continue

            # 3. Check cost limits
            if prof.cost_gold > budget_max_gold:
                continue

            # 4. Proximity distance cost (mocked or loaded coordinates)
            dist_cost = 0.0
            # If the source corresponds to another entity/npc, compute real distance
            source_entity = state.entities.get(prof.source_id)
            if source_entity:
                tgt_pos = source_entity.navigation.position or (0.0, 0.0)
                dx = tgt_pos[0] - entity_pos[0]
                dy = tgt_pos[1] - entity_pos[1]
                dist_cost = math.sqrt(dx * dx + dy * dy)

            # 5. Extract Trust Score
            trust_entry = source_trust_map.get(prof.source_id)
            trust_score = trust_entry.trust if trust_entry else 0.5

            # 6. Expected Relevance & Certainty
            expected_relevance = 0.5
            if query.kind == "recipe_definition" and prof.source_kind == "blacksmith":
                expected_relevance = 0.95
            elif query.kind == "material_source" and prof.source_kind == "guide":
                expected_relevance = 0.8
            elif query.kind == "danger_rating" and prof.source_kind == "guild":
                expected_relevance = 0.85

            expected_certainty = prof.accuracy * trust_score

            candidates.append(
                InformationSourceCandidate(
                    source_id=prof.source_id,
                    source_kind=prof.source_kind,
                    expected_relevance=round(expected_relevance, 2),
                    expected_certainty=round(expected_certainty, 2),
                    cost_gold=prof.cost_gold,
                    distance_cost=round(dist_cost, 2),
                    trust_score=round(trust_score, 2),
                    reason=f"Matched {prof.source_kind} scope for {query.kind}.",
                )
            )

        # Sort candidates: higher expected certainty, lower cost
        candidates.sort(key=lambda c: (-c.expected_certainty, c.cost_gold))

        return tuple(candidates[:3]) # Cap at 3 candidates
