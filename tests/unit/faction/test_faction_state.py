"""Unit tests for FactionState, FactionUpdate, and apply-path integration (E53Aa)."""
from dataclasses import fields, FrozenInstanceError
import pytest


def test_faction_state_serialization_round_trip():
    from src.core.state import FactionState
    from src.core.enums import DiplomaticState

    fs = FactionState(
        faction_id="hero_guild",
        territory=("region_north", "region_east"),
        resources={"gold": 100, "iron": 50},
        diplomatic_relations={"monster_horde": DiplomaticState.HOSTILE, "town_council": DiplomaticState.ALLIED},
        active_doctrines=("doctrine_raid", "doctrine_defend"),
        military_strength=2.5,
        tension_level=0.3,
    )
    d = fs.to_canonical_dict()
    restored = FactionState.from_dict(d)

    assert restored == fs
    assert isinstance(restored.territory, tuple)
    assert isinstance(restored.active_doctrines, tuple)
    keys = list(d["resources"].keys())
    assert keys == sorted(keys)
    keys2 = list(d["diplomatic_relations"].keys())
    assert keys2 == sorted(keys2)


def test_faction_state_serialization_round_trip_defaults():
    from src.core.state import FactionState

    fs = FactionState(faction_id="x")
    restored = FactionState.from_dict(fs.to_canonical_dict())
    assert restored == fs
    assert restored.tension_level == 0.0
    assert restored.military_strength == 1.0
    assert restored.territory == ()
    assert restored.active_doctrines == ()


def test_authoritative_state_has_factions_field():
    from src.core.state import AuthoritativeState, FactionState

    state = AuthoritativeState(tick=0, seed=0)
    assert hasattr(state, "factions")
    assert state.factions == {}

    field_names = {f.name for f in fields(AuthoritativeState)}
    assert "factions" in field_names

    fs = FactionState(faction_id="hero_guild", military_strength=3.0)
    state2 = AuthoritativeState(tick=1, seed=0, factions={"hero_guild": fs})
    assert state2.factions["hero_guild"].military_strength == 3.0

    with pytest.raises(FrozenInstanceError):
        state.factions = {}  # type: ignore


def test_faction_update_apply_tension_delta():
    from src.core.state import AuthoritativeState, FactionState
    from src.core.updates import StateUpdate, FactionUpdate
    from src.engine.apply import ApplyPath

    fs = FactionState(faction_id="monster_horde", tension_level=0.2)
    state = AuthoritativeState(tick=1, seed=0, factions={"monster_horde": fs})

    update = StateUpdate(
        faction_updates=[
            FactionUpdate(faction_id="monster_horde", tension_delta=0.1)
        ]
    )
    new_state = ApplyPath.apply_partial(state, update)

    assert "monster_horde" in new_state.factions
    result = new_state.factions["monster_horde"]
    assert abs(result.tension_level - 0.3) < 1e-9
    assert result.military_strength == 1.0


def test_faction_update_territory_add_remove():
    from src.core.state import AuthoritativeState, FactionState
    from src.core.updates import StateUpdate, FactionUpdate
    from src.engine.apply import ApplyPath

    fs = FactionState(
        faction_id="town_council",
        territory=("region_a", "region_b"),
    )
    state = AuthoritativeState(tick=1, seed=0, factions={"town_council": fs})

    update = StateUpdate(
        faction_updates=[
            FactionUpdate(
                faction_id="town_council",
                territory_add=("region_c",),
                territory_remove=("region_a",),
            )
        ]
    )
    new_state = ApplyPath.apply_partial(state, update)

    result_territory = set(new_state.factions["town_council"].territory)
    assert result_territory == {"region_b", "region_c"}


def test_faction_update_military_strength_set():
    from src.core.state import AuthoritativeState, FactionState
    from src.core.updates import StateUpdate, FactionUpdate
    from src.engine.apply import ApplyPath

    fs = FactionState(faction_id="neutral", military_strength=1.0)
    state = AuthoritativeState(tick=1, seed=0, factions={"neutral": fs})

    update = StateUpdate(
        faction_updates=[
            FactionUpdate(faction_id="neutral", military_strength_set=5.0)
        ]
    )
    new_state = ApplyPath.apply_partial(state, update)
    assert new_state.factions["neutral"].military_strength == 5.0


def test_faction_update_is_noop():
    from src.core.updates import FactionUpdate
    from src.core.enums import DiplomaticState

    noop = FactionUpdate(faction_id="hero_guild")
    assert noop.is_noop()

    not_noop = FactionUpdate(faction_id="hero_guild", tension_delta=0.1)
    assert not not_noop.is_noop()

    assert not FactionUpdate(faction_id="x", military_strength_set=2.0).is_noop()
    assert not FactionUpdate(faction_id="x", territory_add=("r1",)).is_noop()
    assert not FactionUpdate(faction_id="x", territory_remove=("r1",)).is_noop()
    assert not FactionUpdate(faction_id="x", resources_delta={"gold": 1}).is_noop()
    assert not FactionUpdate(faction_id="x", diplomatic_relations_set={"y": DiplomaticState.HOSTILE}).is_noop()
    assert not FactionUpdate(faction_id="x", active_doctrines_set=()).is_noop()


def test_state_update_merge_faction_updates():
    from src.core.updates import StateUpdate, FactionUpdate

    fu1 = FactionUpdate(faction_id="hero_guild", tension_delta=0.1)
    fu2 = FactionUpdate(faction_id="monster_horde", tension_delta=0.2)

    upd1 = StateUpdate(faction_updates=[fu1])
    upd2 = StateUpdate(faction_updates=[fu2])

    merged = upd1.merge(upd2)
    assert len(merged.faction_updates) == 2
    assert fu1 in merged.faction_updates
    assert fu2 in merged.faction_updates


def test_state_update_is_noop_with_faction_updates():
    from src.core.updates import StateUpdate, FactionUpdate

    empty = StateUpdate()
    assert empty.is_noop()

    with_faction = StateUpdate(
        faction_updates=[FactionUpdate(faction_id="x", tension_delta=0.1)]
    )
    assert not with_faction.is_noop()


def test_faction_state_factions_persist_across_ticks():
    from src.core.state import AuthoritativeState, FactionState
    from src.core.updates import StateUpdate
    from src.engine.apply import ApplyPath

    fs = FactionState(faction_id="hero_guild", tension_level=0.5)
    state = AuthoritativeState(tick=1, seed=0, factions={"hero_guild": fs})

    new_state = ApplyPath.apply_generation(state, StateUpdate(), next_tick=2)

    assert "hero_guild" in new_state.factions
    assert new_state.factions["hero_guild"].tension_level == 0.5
    assert new_state.tick == 2
