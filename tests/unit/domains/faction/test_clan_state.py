"""Unit tests for ClanState (schema-only; TCK-20260831-CLAN-STATE-SCHEMA)."""
from dataclasses import FrozenInstanceError
import dataclasses


def test_clan_state_serialization_round_trip():
    from src.core.state import ClanState

    cs = ClanState(
        clan_id="stormfell",
        name="House Stormfell",
        member_entity_ids=(1, 2, 3),
        home_region_ids=("region_east", "region_north"),
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


def test_clan_state_serialization_round_trip_defaults():
    from src.core.state import ClanState

    cs = ClanState(clan_id="x")
    restored = ClanState.from_dict(cs.to_canonical_dict())

    assert restored == cs
    assert restored.member_entity_ids == ()
    assert restored.home_region_ids == ()
    assert restored.tension_level == 0.0
    assert restored.leader_entity_id is None
    assert restored.founded_tick == 0
    assert restored.dissolved_tick is None


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


def test_clan_state_does_not_touch_authoritative_state():
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate

    assert "clan" not in {f.name.lower() for f in dataclasses.fields(AuthoritativeState)}
    assert "clan" not in {f.name.lower() for f in dataclasses.fields(StateUpdate)}


def test_clan_state_does_not_share_faction_state_identity():
    from src.core.state import ClanState, FactionState

    assert ClanState is not FactionState
    assert not isinstance(ClanState(clan_id="x"), FactionState)
