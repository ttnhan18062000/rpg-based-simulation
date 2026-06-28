# Compliance IDs: SOC-228, SOC-230
"""
PartyLifecycleService — periodic leadership election and defection for active party groups.

Ticket: TCK-20260619-E41B-LEADERSHIP (check_leadership)
Ticket: TCK-20260619-E41D-DEFECTION-ESCORT (check_defection)
Logic IDs: SOC-228, SOC-230

Election rule (SOC-228):
  Runs every LEADERSHIP_CHECK_INTERVAL ticks per group.
  If the best-sociability member's sociability exceeds the current leader's
  sociability by >= 0.2, the member with the highest sociability (lowest id
  as tiebreaker) is elected leader and a LeadershipChangedEvent is emitted.

Defection rule (SOC-230):
  An entity defects when len(group.grievance_log) >= DEFECTION_GRIEVANCE_THRESHOLD (3).
  On defection: entity is removed from group.member_ids; a BetrayalDesertionEvent is
  emitted; entity notoriety increases by 2.0 via EntityUpdate.social.
  If the group drops to <= 1 member after defection, dissolution_tick is set.

All state changes are returned as typed records/updates (immutable dataclass
replace pattern) — never written directly to AuthoritativeState.
"""
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from src.core.state import GroupRecord, EntityState
    from src.core.updates import EntityUpdate
    from src.observability.events import LeadershipChangedEvent, BetrayalDesertionEvent


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

    # ------------------------------------------------------------------
    # Defection check (SOC-230)
    # ------------------------------------------------------------------

    DEFECTION_GRIEVANCE_THRESHOLD: int = 3  # unresolved grievances required to defect

    @staticmethod
    def effective_defection_threshold(group: "GroupRecord") -> int:
        """
        Compute the effective defection threshold for this group.

        High-composition parties (composition_score > 0) receive a bonus of
        0–2 extra grievances, sustaining them longer before dissolution (SOC-232).

        composition_score = 0.0  → threshold = 3  (baseline)
        composition_score = 0.5  → threshold = 4  (+1 grievance)
        composition_score = 1.0  → threshold = 5  (+2 grievances)
        """
        bonus = round(group.composition_score * 2)
        return PartyLifecycleService.DEFECTION_GRIEVANCE_THRESHOLD + bonus

    @staticmethod
    def check_defection(
        group: "GroupRecord",
        entity: "EntityState",
        tick: int,
    ) -> "Tuple[Optional[GroupRecord], Optional[BetrayalDesertionEvent], Optional[EntityUpdate]]":
        """
        Evaluate whether *entity* defects from *group* this tick.

        Args:
            group:  The active GroupRecord to evaluate.
            entity: The candidate entity (must be in group.member_ids).
            tick:   Current simulation tick.

        Returns:
            (None, None, None)
                — Defection threshold not met; entity stays.
            (updated_group, event, entity_update)
                — Entity defects: updated group (member removed), BetrayalDesertionEvent,
                  and EntityUpdate applying notoriety_delta=2.0 to the defecting entity.

        Contract:
            - Does NOT mutate group or entity.
            - Deterministic: pure function of inputs.
            - If group drops to <= 1 member after defection, dissolution_tick is set.
            - Entity must be in group.member_ids; behaviour is undefined otherwise.
        """
        threshold = PartyLifecycleService.effective_defection_threshold(group)
        if len(group.grievance_log) < threshold:
            return (None, None, None)

        from src.observability.events import BetrayalDesertionEvent
        from src.core.updates import EntityUpdate, SocialUpdate

        new_members = group.member_ids - {entity.id}
        dissolution = tick if len(new_members) <= 1 else group.dissolution_tick

        updated_group = replace(
            group,
            member_ids=new_members,
            dissolution_tick=dissolution,
            last_updated_tick=tick,
        )

        event = BetrayalDesertionEvent.create(
            tick=tick,
            group_id=group.id,
            entity_id=entity.id,
            grievance_count=len(group.grievance_log),
            remaining_member_ids=sorted(new_members),
        )

        entity_update = EntityUpdate(
            entity_id=entity.id,
            social=SocialUpdate(notoriety_delta=2.0),
        )

        return (updated_group, event, entity_update)
