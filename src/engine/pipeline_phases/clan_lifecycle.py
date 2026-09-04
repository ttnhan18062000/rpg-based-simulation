# Compliance IDs: SOC-264
from __future__ import annotations
from typing import TYPE_CHECKING, List, Union

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate
    from src.observability.events import ClanMemberLeftEvent, ClanSuccessionEvent


class ClanLifecyclePhase:
    """
    Pipeline phase responsible for committing Clan membership changes (join/leave)
    from action outcomes, and running margin-free succession + dissolution checks
    each tick (idea 40/M4, TCK-20260903-CLAN-LIFECYCLE-SUCCESSION).

    Runs immediately after the "groups" phase: action_routing (which produces the
    SUCCESS/FAILURE JOIN_CLAN/LEAVE_CLAN task outcomes Sub-step A reads) and
    lifecycle/combat_engagement (which produce the same-tick combat.alive_set=False
    updates Sub-step B's succession check needs) both run earlier in the same tick.

    `ActionRouter.execute_action` is contractually locked to returning
    Dict[int, EntityUpdate], so `CoreActions.execute_join_clan`/`execute_leave_clan`
    cannot themselves emit a registry-level ClanUpdate. This phase is the second
    half of that two-phase design: it reads the already-annotated task outcomes
    (`EntityUpdate.task.payload_set`, annotated automatically by
    `ActionRoutingPhase.route()`) and converts them into ClanUpdate membership
    deltas.
    """

    # Accumulated leave/succession events from the most recent resolve() call.
    # Cleared at the start of every resolve() call, mirroring GroupPhase.last_tick_events'
    # structure. Note: like GroupPhase.last_tick_events/last_tick_defection_events, this
    # buffer is not currently consumed by kernel.py's real event dispatch -- tests assert
    # on ClanLifecycleService's direct return values instead.
    last_tick_events: List["Union[ClanMemberLeftEvent, ClanSuccessionEvent]"] = []

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src.core.updates import StateUpdate as _StateUpdate, ClanUpdate
        from src.systems.social_systems.clan_lifecycle import ClanLifecycleService

        ClanLifecyclePhase.last_tick_events = []

        tick = state.tick
        new_clan_updates: List[ClanUpdate] = []

        # Sub-step A: membership changes from JOIN_CLAN/LEAVE_CLAN action outcomes.
        for eid, eupd in update.entity_updates.items():
            task = eupd.task
            if task is None or not task.payload_set:
                continue
            payload = task.payload_set
            action = payload.get("action")
            if action not in ("JOIN_CLAN", "LEAVE_CLAN") or payload.get("outcome") != "SUCCESS":
                continue
            clan_id = payload.get("clan_id")
            if not clan_id:
                continue

            if action == "JOIN_CLAN":
                new_clan_updates.append(
                    ClanUpdate(clan_id=clan_id, member_entity_ids_add=(eid,))
                )
            else:
                leave_update, leave_event = ClanLifecycleService.process_leave(clan_id, eid, tick)
                new_clan_updates.append(leave_update)
                ClanLifecyclePhase.last_tick_events.append(leave_event)

        # Sub-step B: succession + dissolution, evaluated over the start-of-tick clans.
        for clan_id, clan in state.clans.items():
            members = [
                state.entities[m_id]
                for m_id in clan.member_entity_ids
                if m_id in state.entities
            ]

            succession_update, succession_event = ClanLifecycleService.process_succession(
                clan, members, update, tick
            )
            if succession_update is not None:
                new_clan_updates.append(succession_update)
            if succession_event is not None:
                ClanLifecyclePhase.last_tick_events.append(succession_event)

            dissolution_update = ClanLifecycleService.process_dissolution(clan, tick)
            if dissolution_update is not None:
                new_clan_updates.append(dissolution_update)

        if not new_clan_updates:
            return update

        return update.merge(_StateUpdate(clan_updates=new_clan_updates))
