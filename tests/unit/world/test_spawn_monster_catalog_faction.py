"""
TCK-20261005-SPAWN-MONSTER-STRIPS-CATALOG-FACTION-FROM-EVERY-RUNTIME-SPAWNED-MONSTER

A runtime-spawned monster whose kind has a catalog faction carries that faction's `faction_id`, so the
endurance the catalog declares for it applies. Kinds with no unambiguous catalog faction (bosses included)
keep only the legacy bucket. The legacy bucket itself is never granted immunity.
"""
from __future__ import annotations

import pytest

from src.content_semantics.faction import get_faction_id_str, get_faction_semantics_service
from src.core.enums import Faction
from src.systems.world_systems.generator import SPAWN_KIND_CATALOG_FACTION, EntityGenerator

CAMP_KINDS = ["goblin_warrior", "orc_warrior", "goblin_raider"]


@pytest.mark.parametrize("kind", CAMP_KINDS)
def test_spawned_monster_carries_its_catalog_faction_and_endurance(kind):
    mob = EntityGenerator(seed=1).spawn_monster((0.0, 0.0), kind=kind)
    faction_id = get_faction_id_str(mob)
    assert faction_id == SPAWN_KIND_CATALOG_FACTION[kind]
    assert mob.identity.faction == Faction.MONSTER_HORDE
    assert "NATURAL_TERRAIN" in get_faction_semantics_service().get_hazard_immunities(faction_id)


def test_every_mapped_faction_exists_in_the_catalog():
    repo = get_faction_semantics_service().repo
    assert {f for f in SPAWN_KIND_CATALOG_FACTION.values() if repo.get_faction(f) is None} == set()


@pytest.mark.parametrize("kind", ["world_boss", "bear", "harpy", "golem", "wolf", "slime"])
def test_kinds_without_a_catalog_faction_are_unchanged(kind):
    mob = EntityGenerator(seed=1).spawn_monster((0.0, 0.0), kind=kind)
    assert "faction_id" not in mob.identity.properties
    assert get_faction_id_str(mob) == "monster_horde"
    assert not get_faction_semantics_service().get_hazard_immunities("monster_horde")


def test_disabling_control_without_the_table_goblin_loses_endurance(monkeypatch):
    monkeypatch.setattr("src.systems.world_systems.generator.SPAWN_KIND_CATALOG_FACTION", {})
    mob = EntityGenerator(seed=1).spawn_monster((0.0, 0.0), kind="goblin_warrior")
    assert not get_faction_semantics_service().get_hazard_immunities(get_faction_id_str(mob))


# TCK-20261005-LAW-OCCUPANCY-COLLISION-HARD-LAW-ERRORS-ON-MAIN: spawn_monster placed a respawn on a tile an
# earlier spawn still held; once spawns survive (faction restored) that fired the hard law every tick.
def _state_with_monster_at(pos):
    from src.core.state import AuthoritativeState
    gen = EntityGenerator(seed=1)
    holder = gen.spawn_monster(pos, kind="goblin_warrior")
    return gen, AuthoritativeState(tick=5, seed=1, entities={holder.id: holder})


def test_spawn_onto_an_occupied_tile_lands_on_a_free_neighbour():
    gen, state = _state_with_monster_at((10.0, 10.0))
    mob = gen.spawn_monster((10.0, 10.0), state=state, kind="goblin_warrior")
    x, y = mob.navigation.position
    assert (int(x), int(y)) != (10, 10) and max(abs(int(x) - 10), abs(int(y) - 10)) == 2
    assert mob.navigation.home_position == (10.0, 10.0)


def test_same_tick_spawns_do_not_share_a_tile():
    gen, state = _state_with_monster_at((10.0, 10.0))
    tiles = {tuple(map(int, gen.spawn_monster((10.0, 10.0), state=state, kind="orc_warrior").navigation.position)) for _ in range(8)}
    assert len(tiles) == 8 and (10, 10) not in tiles


def test_no_clear_tile_fails_loudly():
    gen, state = _state_with_monster_at((10.0, 10.0))
    import src.systems.world_systems.generator as g
    with pytest.raises(RuntimeError, match="no clear spawn tile"):
        for _ in range((2 * g._SPAWN_FREE_TILE_RADIUS + 1) ** 2):
            gen.spawn_monster((10.0, 10.0), state=state, kind="orc_warrior")


def test_free_tile_is_kept_exactly():
    gen, state = _state_with_monster_at((10.0, 10.0))
    assert gen.spawn_monster((40.0, 40.0), state=state, kind="orc_warrior").navigation.position == (40.0, 40.0)


def _hero(entity_id, pos):
    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole
    return (V2EntityBuilder(entity_id).kind("hero").location(*pos).identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
            .combat(hp=100, max_hp=100, atk=10, def_stat=5, readiness=100.0, attack_range=1.5).build())


@pytest.mark.parametrize("kind", ["wolf", "bear", "golem", "goblin_warrior", "orc_warrior", "dragonkin", "bandit"])
def test_hero_and_spawned_monster_stay_mutually_hostile(kind):
    """Hostility must keep coming from the legacy bucket: restoring a catalog faction must not make a spawned monster non-hostile."""
    from src.core.state import AuthoritativeState
    from src.engine.legality import LegalityServiceV2
    mob = EntityGenerator(seed=1).spawn_monster((6.0, 5.0), kind=kind)
    hero = _hero(1000, (5.0, 5.0))
    state = AuthoritativeState(tick=5, seed=1, entities={hero.id: hero, mob.id: mob})
    assert LegalityServiceV2.verify_attack_legality(hero, mob, state)[0]
    assert LegalityServiceV2.verify_attack_legality(mob, hero, state)[0]
