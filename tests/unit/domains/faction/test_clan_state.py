"""Unit tests for ClanState and its wiring into AuthoritativeState/StateUpdate/apply.py
(idea 40/M4, TCK-20260903-CLAN-LIFECYCLE-SUCCESSION; schema originally added by
TCK-20260831-CLAN-STATE-SCHEMA)."""
from dataclasses import FrozenInstanceError
import dataclasses
import pytest


def test_clan_state_serialization_round_trip():
    from src.core.state import ClanState

    cs = ClanState(
        clan_id="stormfell",
        name="House Stormfell",
        member_entity_ids=(1, 2, 3),
        home_region_ids=("region_east", "region_north"),
        asset_ids=(10, 20),
        tension_level=0.4,
        leader_entity_id=1,
        founded_tick=120,
        dissolved_tick=None,
    )
    d = cs.to_canonical_dict()
    restored = ClanState.from_dict(d)

    assert restored == cs
    assert isinstance(restored.member_entity_ids, tuple)
    assert isinstance(restored.home_region_ids, tuple)
    assert isinstance(restored.asset_ids, tuple)


def test_clan_state_serialization_round_trip_defaults():
    from src.core.state import ClanState

    cs = ClanState(clan_id="x")
    restored = ClanState.from_dict(cs.to_canonical_dict())

    assert restored == cs
    assert restored.member_entity_ids == ()
    assert restored.home_region_ids == ()
    assert restored.asset_ids == ()
    assert restored.tension_level == 0.0
    assert restored.leader_entity_id is None
    assert restored.founded_tick == 0
    assert restored.dissolved_tick is None


def test_clan_state_asset_ids_round_trip():
    from src.core.state import ClanState

    cs = ClanState(clan_id="x", asset_ids=(3, 1, 2))
    d = cs.to_canonical_dict()
    assert d["asset_ids"] == [1, 2, 3]

    restored = ClanState.from_dict(d)
    assert restored.asset_ids == (1, 2, 3)


def test_clan_state_is_frozen():
    import pytest
    from src.core.state import ClanState

    cs = ClanState(clan_id="x")
    with pytest.raises(FrozenInstanceError):
        cs.clan_id = "y"  # type: ignore


def test_clan_state_canonical_dict_is_sorted_and_deterministic():
    from src.core.state import ClanState

    a = ClanState(
        clan_id="x",
        member_entity_ids=(3, 1, 2),
        home_region_ids=("region_c", "region_a", "region_b"),
    )
    b = ClanState(
        clan_id="x",
        member_entity_ids=(1, 2, 3),
        home_region_ids=("region_a", "region_b", "region_c"),
    )

    assert a.to_canonical_dict() == b.to_canonical_dict()
    assert a.to_canonical_dict()["member_entity_ids"] == [1, 2, 3]
    assert a.to_canonical_dict()["home_region_ids"] == ["region_a", "region_b", "region_c"]


def test_clan_state_is_wired_into_authoritative_state():
    from src.core.state import AuthoritativeState, ClanState
    from src.core.updates import StateUpdate

    state = AuthoritativeState(tick=0, seed=0)
    assert hasattr(state, "clans")
    assert state.clans == {}
    field_names = {f.name for f in dataclasses.fields(AuthoritativeState)}
    assert "clans" in field_names

    update_field_names = {f.name for f in dataclasses.fields(StateUpdate)}
    assert "clan_updates" in update_field_names

    state2 = AuthoritativeState(tick=1, seed=0, clans={"x": ClanState(clan_id="x")})
    assert state2.clans["x"].clan_id == "x"


def test_clan_state_does_not_share_faction_state_identity():
    from src.core.state import ClanState, FactionState

    assert ClanState is not FactionState
    assert not isinstance(ClanState(clan_id="x"), FactionState)


def test_authoritative_state_has_clans_field():
    from src.core.state import AuthoritativeState, ClanState

    state = AuthoritativeState(tick=0, seed=0)
    assert hasattr(state, "clans")
    assert state.clans == {}

    field_names = {f.name for f in dataclasses.fields(AuthoritativeState)}
    assert "clans" in field_names

    cs = ClanState(clan_id="stormfell", leader_entity_id=1)
    state2 = AuthoritativeState(tick=1, seed=0, clans={"stormfell": cs})
    assert state2.clans["stormfell"].leader_entity_id == 1

    with pytest.raises(FrozenInstanceError):
        state.clans = {}  # type: ignore


def test_clan_update_is_noop():
    from src.core.updates import ClanUpdate

    noop = ClanUpdate(clan_id="x")
    assert noop.is_noop()

    assert not ClanUpdate(clan_id="x", member_entity_ids_add=(1,)).is_noop()
    assert not ClanUpdate(clan_id="x", member_entity_ids_remove=(1,)).is_noop()
    assert not ClanUpdate(clan_id="x", leader_entity_id_set=1).is_noop()
    assert not ClanUpdate(clan_id="x", dissolved_tick_set=5).is_noop()


def test_clan_update_membership_add_remove():
    from src.core.state import AuthoritativeState, ClanState
    from src.core.updates import StateUpdate, ClanUpdate
    from src.engine.apply import ApplyPath

    cs = ClanState(clan_id="stormfell", member_entity_ids=(1, 2))
    state = AuthoritativeState(tick=1, seed=0, clans={"stormfell": cs})

    update = StateUpdate(
        clan_updates=[
            ClanUpdate(
                clan_id="stormfell",
                member_entity_ids_add=(3,),
                member_entity_ids_remove=(1,),
            )
        ]
    )
    new_state = ApplyPath.apply_partial(state, update)

    result_members = set(new_state.clans["stormfell"].member_entity_ids)
    assert result_members == {2, 3}


def test_state_update_merge_clan_updates():
    from src.core.updates import StateUpdate, ClanUpdate

    cu1 = ClanUpdate(clan_id="stormfell", member_entity_ids_add=(1,))
    cu2 = ClanUpdate(clan_id="riverford", member_entity_ids_add=(2,))

    upd1 = StateUpdate(clan_updates=[cu1])
    upd2 = StateUpdate(clan_updates=[cu2])

    merged = upd1.merge(upd2)
    assert len(merged.clan_updates) == 2
    assert cu1 in merged.clan_updates
    assert cu2 in merged.clan_updates


def test_state_update_is_noop_with_clan_updates():
    from src.core.updates import StateUpdate, ClanUpdate

    empty = StateUpdate()
    assert empty.is_noop()

    with_clan = StateUpdate(
        clan_updates=[ClanUpdate(clan_id="x", member_entity_ids_add=(1,))]
    )
    assert not with_clan.is_noop()


def test_clan_state_persists_across_ticks():
    from src.core.state import AuthoritativeState, ClanState
    from src.core.updates import StateUpdate
    from src.engine.apply import ApplyPath

    cs = ClanState(clan_id="stormfell", tension_level=0.5)
    state = AuthoritativeState(tick=1, seed=0, clans={"stormfell": cs})

    new_state = ApplyPath.apply_generation(state, StateUpdate(), next_tick=2)

    assert "stormfell" in new_state.clans
    assert new_state.clans["stormfell"].tension_level == 0.5
    assert new_state.tick == 2


def test_clan_state_no_new_idea68_fields():
    """Guards against idea 68 (Inter-Clan Relations) scope creep: ClanState/ClanUpdate must
    carry exactly the fields this ticket's plan specifies -- no diplomacy/alliance/war-adjacent
    additions."""
    from src.core.state import ClanState
    from src.core.updates import ClanUpdate

    clan_state_fields = {f.name for f in dataclasses.fields(ClanState) if not f.name.startswith("_")}
    assert clan_state_fields == {
        "clan_id", "name", "member_entity_ids", "home_region_ids", "asset_ids",
        "tension_level", "leader_entity_id", "founded_tick", "dissolved_tick",
    }

    clan_update_fields = {f.name for f in dataclasses.fields(ClanUpdate)}
    assert clan_update_fields == {
        "clan_id", "member_entity_ids_add", "member_entity_ids_remove",
        "leader_entity_id_set", "dissolved_tick_set",
    }
