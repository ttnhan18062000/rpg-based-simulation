"""A conquest flips ownership and adds no body (TCK-20261014-A-CONQUEST-NO-LONGER-SPAWNS-A-STRONGHOLD-BODY-D71, owner ruling D71).

Ownership changes hands at influence <= -50 (an unowned region) and is liberated at >= +50 (an invader-owned region); both thresholds are
unchanged. The stronghold entity that used to appear on a conquest, with no parent and no cost, is gone, so a conquest changes no entity count and
does not move ``next_entity_id``.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, RegionState
from src.core.updates import NO_OWNER_SENTINEL, StateUpdate
from src.engine.apply import ApplyPath
from src.world.influence import FactionInfluenceService


def _dead(n: int, faction: Faction, kind: str):
    return [V2EntityBuilder(1000 + i).kind(kind).location(5, 5).identity(faction=faction).combat(hp=0).combat(alive=False).build() for i in range(n)]


def _state(influence: float, owner=None):
    bystander = V2EntityBuilder(1).kind("hero").location(1, 1).identity(faction=Faction.HERO_GUILD).combat(hp=30, max_hp=30).build()
    region = RegionState(id="wild", name="Wild", bounds=(0, 0, 10, 10), influence=influence, owner_faction_id=owner)
    return AuthoritativeState(tick=100, seed=42, regions={"wild": region}, entities={1: bystander}, next_entity_id=2)


def _shift(state, deaths):
    return ApplyPath.apply_generation(state, FactionInfluenceService.process_influence_shift(state, deaths))


def test_a_conquest_flips_ownership_at_minus_fifty_and_adds_no_entity():
    state = _state(0.0)
    just_short = _shift(state, _dead(9, Faction.HERO_GUILD, "hero"))
    assert just_short.regions["wild"].influence == -45.0 and just_short.regions["wild"].owner_faction_id is None
    conquered = _shift(just_short, _dead(1, Faction.HERO_GUILD, "hero"))
    assert conquered.regions["wild"].influence == -50.0
    assert conquered.regions["wild"].owner_faction_id == Faction.MONSTER_HORDE
    assert set(conquered.entities) == set(state.entities) and conquered.next_entity_id == state.next_entity_id


def test_an_invader_owned_region_is_liberated_at_plus_fifty_and_adds_no_entity():
    state = _state(-50.0, owner=Faction.MONSTER_HORDE)
    short = _shift(state, _dead(19, Faction.MONSTER_HORDE, "monster"))
    assert short.regions["wild"].influence == 45.0 and short.regions["wild"].owner_faction_id == Faction.MONSTER_HORDE
    freed = _shift(short, _dead(1, Faction.MONSTER_HORDE, "monster"))
    assert freed.regions["wild"].influence == 50.0
    assert freed.regions["wild"].owner_faction_id in (None, NO_OWNER_SENTINEL)
    assert set(freed.entities) == set(state.entities) and freed.next_entity_id == state.next_entity_id


def test_conquest_then_liberation_round_trip_changes_no_entity():
    state = _state(0.0)
    held = _shift(state, _dead(10, Faction.HERO_GUILD, "hero"))
    assert held.regions["wild"].owner_faction_id == Faction.MONSTER_HORDE
    freed = _shift(held, _dead(20, Faction.MONSTER_HORDE, "monster"))
    assert freed.regions["wild"].influence == 50.0 and freed.regions["wild"].owner_faction_id in (None, NO_OWNER_SENTINEL)
    assert set(freed.entities) == set(state.entities) and freed.next_entity_id == state.next_entity_id


def test_the_conquest_lifecycle_entry_point_and_stronghold_spawner_are_gone():
    assert not hasattr(FactionInfluenceService, "process_conquest_lifecycle")
    from src.systems.world_systems.generator import EntityGenerator
    assert not hasattr(EntityGenerator, "spawn_stronghold")


def test_the_conquest_flip_is_deterministic():
    a = _shift(_state(0.0), _dead(10, Faction.HERO_GUILD, "hero"))
    b = _shift(_state(0.0), _dead(10, Faction.HERO_GUILD, "hero"))
    assert a.regions == b.regions and a.entities == b.entities and a.next_entity_id == b.next_entity_id


def test_a_town_in_a_conquered_region_pays_its_tax_to_the_horde_treasury_with_no_stronghold_in_the_world():
    """The knock-on of the flip is unchanged: the place holder is read from the region owner, never from a body."""
    from src.core.state import BuildingState, InventoryComponent
    from src.engine.place_tax import tax_on

    region = RegionState(id="town", name="Town", bounds=(0, 0, 20, 20), kind="TOWN", influence=0.0, tax_share=0.1)
    shop = BuildingState(id=2, kind="shop", position=(8, 8), functional=True, inventory=InventoryComponent(gold=500))
    state = AuthoritativeState(tick=100, seed=42, regions={"town": region}, buildings={2: shop}, entities={}, next_entity_id=2)
    assert tax_on(state, shop, 100) == (None, 0)                       # nobody holds it yet
    deaths = [V2EntityBuilder(1000 + i).kind("hero").location(5, 5).identity(faction=Faction.HERO_GUILD).combat(hp=0).combat(alive=False).build() for i in range(10)]
    conquered = ApplyPath.apply_generation(state, FactionInfluenceService.process_influence_shift(state, deaths))
    assert conquered.regions["town"].owner_faction_id == Faction.MONSTER_HORDE and not conquered.entities
    assert tax_on(conquered, conquered.buildings[2], 100) == (int(Faction.MONSTER_HORDE), 10)
