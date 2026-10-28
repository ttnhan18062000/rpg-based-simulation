"""
src/domains/cooperation/providers.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 — Partner Candidate Provider.
"""

from __future__ import annotations
from dataclasses import dataclass
from math import floor
from typing import Dict, List, Optional, Tuple
from src.core.state import EntityState, AuthoritativeState
from src.domains.cooperation.evaluators import HelpNeed
from src.content_semantics.faction import are_entities_hostile
from src.content_semantics.relation import RelationContext

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

class PartnerCandidateIndex:
    """Per-tick candidate source for ``PartnerCandidateProvider`` (TCK-20261023-COOPERATION-CANDIDATES-ENUMERATED-PER-ENTITY-PER-TICK).

    Holds the active, alive entities in ``state.entities`` iteration order (``rank``) and a spatial grid with a cell
    size equal to the spatial radius, so a requester's nearby candidates are the 3x3 neighbouring cells instead of every
    entity. Read-only over the state: it is valid only while positions, liveness and activity do not change, which is
    true for the whole cooperation phase (every change is deferred into the returned update).
    """

    __slots__ = ("radius", "rank", "entities", "cells")

    def __init__(self, state: AuthoritativeState, radius: float) -> None:
        self.radius = radius
        self.rank: Dict[int, int] = {}
        self.entities: Dict[int, EntityState] = {}
        self.cells: Dict[Tuple[int, int], List[int]] = {}
        for i, (eid, ent) in enumerate(state.entities.items()):
            if not ent.lifecycle.active or not ent.combat.alive:
                continue
            self.rank[eid] = i
            self.entities[eid] = ent
            pos = ent.navigation.position
            self.cells.setdefault(self._cell(pos[0], pos[1]), []).append(eid)

    def _cell(self, x: float, y: float) -> Tuple[int, int]:
        return (floor(x / self.radius), floor(y / self.radius))

    def candidate_ids(self, entity: EntityState) -> List[int]:
        """Ids the exhaustive scan could keep (within radius, or trust > 0.7), in ``state.entities`` order."""
        my_pos = entity.navigation.position
        cx, cy = self._cell(my_pos[0], my_pos[1])
        ids = set()
        for gx in (cx - 1, cx, cx + 1):
            for gy in (cy - 1, cy, cy + 1):
                bucket = self.cells.get((gx, gy))
                if bucket:
                    ids.update(bucket)
        for cand_id, trust in entity.social.trust_history.items():
            if trust > 0.7 and cand_id in self.rank:
                ids.add(cand_id)
        ids.discard(entity.id)
        return sorted(ids, key=self.rank.__getitem__)


class PartnerCandidateProvider:
    @staticmethod
    def build_index(state: AuthoritativeState, budget: CandidateBudget = CandidateBudget()) -> PartnerCandidateIndex:
        """Build the spatial partner-candidate index over ``state`` within ``budget.spatial_radius``; it lives for one tick."""
        return PartnerCandidateIndex(state, budget.spatial_radius)

    @staticmethod
    def get_candidates(
        entity: EntityState,
        state: AuthoritativeState,
        help_needs: Tuple[HelpNeed, ...],
        budget: CandidateBudget = CandidateBudget(),
        index: Optional[PartnerCandidateIndex] = None,
    ) -> Tuple[PartnerCandidate, ...]:
        if index is None or index.radius != budget.spatial_radius:
            index = PartnerCandidateIndex(state, budget.spatial_radius)
        candidates = []
        my_pos = entity.navigation.position

        for cand_id in index.candidate_ids(entity):
            cand = index.entities[cand_id]

            # Keep if nearby or highly trusted (checked before hostility: hostility only removes, so the order of
            # the two filters does not change the result, and it spares the per-pair catalog call for far entities).
            c_pos = cand.navigation.position
            dx = my_pos[0] - c_pos[0]
            dy = my_pos[1] - c_pos[1]
            dist = (dx**2 + dy**2)**0.5
            trust = entity.social.trust_history.get(cand_id, 0.5)
            if not (dist <= budget.spatial_radius or trust > 0.7):
                continue
            familiarity = entity.social.familiarity_history.get(cand_id, 0.0)

            # Exclude hostiles
            manhattan = abs(dx) + abs(dy)
            if are_entities_hostile(entity, cand, RelationContext(distance=float(manhattan), combat_engaged=True)):
                # TODO(TCK-20260824-OCCUPATION-CHANGE-TRIGGER): EntityRole(1) is SHOPKEEPER
                # (src/core/enums.py:8), not a distinct "Hireling"/"Guild Merchant" role. Now
                # that role_set is runtime-reachable (OccupationChangeGoalScorer), any entity
                # that transitions into SHOPKEEPER is silently treated as a Hireling here for
                # cooperation-partner selection. Disclosed, not fixed -- out of that ticket's scope.
                # Unless special hireling or merchant
                if cand.identity.role != 1: # Let role 1 (Hireling) pass regardless of faction (or if faction matches)
                    continue

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
