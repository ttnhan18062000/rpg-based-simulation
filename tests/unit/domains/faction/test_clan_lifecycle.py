# Compliance IDs: SOC-263
"""
Tests for ClanLifecycleService.process_leave (TCK-20260903-CLAN-LIFECYCLE-SUCCESSION,
idea 40/M4, AC 4).
"""
from __future__ import annotations

import ast
import inspect

from src.core.state import AuthoritativeState, ClanState
from src.core.updates import ClanUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.systems.social_systems.clan_lifecycle import ClanLifecycleService
from src.observability.events import ClanMemberLeftEvent


def test_clan_leave_removes_entity_via_clan_update():
    update, event = ClanLifecycleService.process_leave(
        clan_id="stormfell", entity_id=11, tick=50
    )

    assert isinstance(update, ClanUpdate)
    assert update.clan_id == "stormfell"
    assert update.member_entity_ids_remove == (11,)
    assert not update.member_entity_ids_add
    assert update.leader_entity_id_set is None
    assert update.dissolved_tick_set is None

    cs = ClanState(clan_id="stormfell", member_entity_ids=(10, 11, 12))
    state = AuthoritativeState(tick=1, seed=0, clans={"stormfell": cs})
    new_state = ApplyPath.apply_partial(state, StateUpdate(clan_updates=[update]))

    assert 11 not in new_state.clans["stormfell"].member_entity_ids
    assert set(new_state.clans["stormfell"].member_entity_ids) == {10, 12}


def test_clan_leave_emits_clan_specific_event():
    update, event = ClanLifecycleService.process_leave(
        clan_id="stormfell", entity_id=11, tick=50
    )

    assert isinstance(event, ClanMemberLeftEvent)
    assert event.clan_id == "stormfell"
    assert event.entity_id == 11
    assert event.event_type == "clan_member_left"
    assert event.event_category == "social"


def test_clan_leave_never_mutates_clan_state_directly():
    """Architecture guard: process_leave's source must not call
    object.__setattr__/direct field assignment on any ClanState instance -- only
    typed record returns are allowed."""
    from src.systems.social_systems import clan_lifecycle

    source = inspect.getsource(clan_lifecycle.ClanLifecycleService.process_leave)
    assert "object.__setattr__" not in source
    assert ".member_entity_ids =" not in source
    assert ".leader_entity_id =" not in source
    assert ".dissolved_tick =" not in source
