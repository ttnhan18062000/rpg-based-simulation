# Compliance IDs: SOC-263
"""
ClanLifecycleService — leaving, margin-free succession-on-death, and dissolution for Clans.

Ticket: TCK-20260903-CLAN-LIFECYCLE-SUCCESSION (idea 40/M4)
Logic ID: SOC-263

This service is built fresh and deliberately does NOT import from
`party_lifecycle.py` (Group's 0.2-margin `check_leadership()`, SOC-228) or
`groups.py` (Group's unconditional dead-leader dissolution, SOC-176/SOC-189).
Clan succession has no sociability-margin gate; Clan dissolution requires both
an empty membership AND an empty asset/institutional-footprint measure, unlike
Group's unconditional dissolution. The lowest-entity-id tiebreak convention is
reused as a numeric rule only, never via a shared function/import.

All state changes are returned as typed records/updates (immutable dataclass
replace pattern) — never written directly to ClanState.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from src.core.state import ClanState, EntityState
    from src.core.updates import ClanUpdate, StateUpdate
    from src.observability.events import ClanMemberLeftEvent, ClanSuccessionEvent


class ClanLifecycleService:
    """
    Pure-static service for Clan leave/succession/dissolution lifecycle.
    """

    @staticmethod
    def process_leave(
        clan_id: str,
        entity_id: int,
        tick: int,
    ) -> "Tuple[ClanUpdate, ClanMemberLeftEvent]":
        """
        Unconditional -- no appraise_contract() gate (leaving requires no
        appraisal, only joining does). Returns the typed ClanUpdate removing
        entity_id from member_entity_ids and the Clan-specific event. Never
        mutates ClanState directly.
        """
        from src.core.updates import ClanUpdate
        from src.observability.events import ClanMemberLeftEvent

        update = ClanUpdate(
            clan_id=clan_id,
            member_entity_ids_remove=(entity_id,),
        )
        event = ClanMemberLeftEvent(
            tick=tick,
            clan_id=clan_id,
            entity_id=entity_id,
        )
        return update, event

    @staticmethod
    def process_succession(
        clan: "ClanState",
        members: List["EntityState"],
        current_update: Optional["StateUpdate"],
        tick: int,
    ) -> "Tuple[Optional[ClanUpdate], Optional[ClanSuccessionEvent]]":
        """
        No 0.2-margin gate (contrast SOC-228, party_lifecycle.py:94) -- promotes
        immediately whenever the leader is dead/inactive/None and at least one
        scoreable member exists. Leader liveness uses the same same-tick-effective-
        state pattern as GroupSystem.update_groups()'s is_alive/is_active
        (groups.py:32-57) -- re-implemented locally here (reading
        current_update.entity_updates before falling back to member
        EntityState.combat.alive/lifecycle.active), NOT imported from groups.py, to
        avoid any accidental coupling between Group and Clan lifecycle code.
        Tiebreak: lowest entity id, mirroring party_lifecycle.py:88-91's tiebreak
        convention (the tiebreak rule is reused as a numeric convention, not as a
        function call/import). Returns (None, None) when the leader is
        alive/active, and (None, None) when the leader is dead/None but no
        scoreable members remain (defers to process_dissolution).
        """
        from src.core.updates import ClanUpdate
        from src.observability.events import ClanSuccessionEvent

        def is_alive(e_id: int) -> bool:
            if current_update and e_id in current_update.entity_updates:
                upd = current_update.entity_updates[e_id]
                if upd.combat and upd.combat.alive_set is False:
                    return False
            for m in members:
                if m.id == e_id:
                    return m.combat.alive
            return False

        def is_active(e_id: int) -> bool:
            if current_update and e_id in current_update.entity_updates:
                upd = current_update.entity_updates[e_id]
                if upd.active is False:
                    return False
            for m in members:
                if m.id == e_id:
                    return m.lifecycle.active
            return False

        leader_id = clan.leader_entity_id

        if leader_id is not None and is_alive(leader_id) and is_active(leader_id):
            return None, None

        sociabilities: dict[int, float] = {
            m.id: m.identity.personality.sociability
            for m in members
            if m.id != leader_id and is_alive(m.id) and is_active(m.id)
        }

        if not sociabilities:
            return None, None

        best_id: int = min(
            sociabilities,
            key=lambda eid: (-sociabilities[eid], eid),
        )

        update = ClanUpdate(
            clan_id=clan.clan_id,
            leader_entity_id_set=best_id,
        )
        event = ClanSuccessionEvent(
            tick=tick,
            clan_id=clan.clan_id,
            old_leader_id=leader_id,
            new_leader_id=best_id,
        )
        return update, event

    @staticmethod
    def process_dissolution(clan: "ClanState", tick: int) -> "Optional[ClanUpdate]":
        """
        Sets dissolved_tick only when member_entity_ids AND asset_ids are BOTH
        empty (AC 2). Reads clan.member_entity_ids/asset_ids as given by the
        caller -- ClanLifecyclePhase passes the start-of-tick state.clans
        snapshot, so a clan whose last member leaves this same tick dissolves on
        the FOLLOWING tick's pass, the same one-tick-lag design already used by
        FactionAwarenessService (pipeline.py's own comment: "one-tick lag is
        inherent (state frozen)") -- not a new pattern. Returns None if already
        dissolved or not eligible.
        """
        from src.core.updates import ClanUpdate

        if clan.dissolved_tick is not None:
            return None
        if clan.member_entity_ids or clan.asset_ids:
            return None

        return ClanUpdate(
            clan_id=clan.clan_id,
            dissolved_tick_set=tick,
        )
