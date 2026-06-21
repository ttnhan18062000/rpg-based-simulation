# Compliance IDs: SOC-228
"""
PartyLifecycleService — periodic leadership election for active party groups.

Ticket: TCK-20260619-E41B-LEADERSHIP
Logic ID: SOC-228

Election rule:
  Runs every LEADERSHIP_CHECK_INTERVAL ticks per group.
  If the best-sociability member's sociability exceeds the current leader's
  sociability by >= 0.2, the member with the highest sociability (lowest id
  as tiebreaker) is elected leader and a LeadershipChangedEvent is emitted.

All state changes are returned as a new GroupRecord (immutable dataclass
replace pattern) — never written directly to AuthoritativeState.
"""
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from src.core.state import GroupRecord, EntityState
    from src.observability.events import LeadershipChangedEvent


class PartyLifecycleService:
    """
    Pure-static service for party lifecycle management.
    Implements periodic leadership re-election based on OCEAN sociability trait.
    """

    LEADERSHIP_CHECK_INTERVAL: int = 100  # ticks between election evaluations

    @staticmethod
    def check_leadership(
        group: "GroupRecord",
        members: List["EntityState"],
        tick: int,
    ) -> Tuple[Optional["GroupRecord"], Optional["LeadershipChangedEvent"]]:
        """
        Evaluate whether a leadership transition is warranted this tick.

        Args:
            group:   The active GroupRecord to evaluate.
            members: All EntityState objects that may be in this group (filtered
                     internally to group.member_ids).
            tick:    Current simulation tick.

        Returns:
            (None, None)                               — interval not yet reached; skip.
            (updated_group, None)                      — interval reached, no election.
            (updated_group_with_new_leader, event)     — leader elected; event ready.

        Contract:
            - Does NOT mutate 'group' or any EntityState.
            - Deterministic: tiebreaker is lowest entity id.
            - Members missing from 'members' list are silently skipped.
        """
        # Gate: only run at election interval boundaries
        if tick - group.last_leadership_check_tick < PartyLifecycleService.LEADERSHIP_CHECK_INTERVAL:
            return (None, None)

        # Build sociability map for members present in the provided list
        # Sociability is stored at entity.identity.personality.sociability
        member_id_set = group.member_ids
        sociabilities: dict[int, float] = {
            e.id: e.identity.personality.sociability
            for e in members
            if e.id in member_id_set
        }

        # No scoreable members — just update the check tick
        if not sociabilities:
            return (replace(group, last_leadership_check_tick=tick), None)

        current_sociability: float = sociabilities.get(group.leader_id, 0.0)

        # Deterministic max: prefer higher sociability; break ties by lowest entity id
        best_id: int = min(
            sociabilities,
            key=lambda eid: (-sociabilities[eid], eid),
        )
        best_sociability: float = sociabilities[best_id]

        if best_sociability - current_sociability >= 0.2:
            # Election: promote best candidate
            from src.observability.events import LeadershipChangedEvent

            updated_group = replace(
                group,
                leader_id=best_id,
                last_leadership_check_tick=tick,
            )
            event = LeadershipChangedEvent(
                tick=tick,
                group_id=group.id,
                old_leader_id=group.leader_id,
                new_leader_id=best_id,
                entity_id=best_id,
                related_entity_ids=[group.leader_id],
                payload={
                    "morale_delta": 0.1,
                    "old_sociability": current_sociability,
                    "new_sociability": best_sociability,
                },
            )
            return (updated_group, event)

        # No election — just update the check tick
        return (replace(group, last_leadership_check_tick=tick), None)
