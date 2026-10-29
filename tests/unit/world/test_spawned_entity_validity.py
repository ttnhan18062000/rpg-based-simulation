"""Spawned and compiled entities carry valid identity, loadout and leash fields.

Sources: src/systems/world_systems/generator.py (EntityGenerator.spawn_monster), src/world/calamity.py (_spawn_world_boss),
src/worldbuilding/compiler.py (compiled entities), src/core/items.py (ItemRegistry).
"""
from pathlib import Path

import pytest

from src.core.enums import EntityRole, Faction
from src.core.items import ItemRegistry
from src.core.state import AuthoritativeState, RegionState
from src.systems.world_systems.generator import EntityGenerator
from src.world.calamity import CalamityService
from src.world.spawn_config import DIFFICULTY_TIERS
from tests.helpers.scenario import compile_world


def _corpus_worlds():
    return sorted(p.name for p in Path("data/worlds").iterdir() if p.is_dir())


def test_a_calamity_world_boss_has_the_boss_kind_the_monster_role_and_a_tier_four_level():
    region = RegionState(id="badlands", name="Badlands", bounds=(50, 50, 60, 60), calamity_intensity=0.8)
    state = AuthoritativeState(
        feature_flags={"ENABLE_WORLD_BOSS_SPAWN": "ON"}, tick=5000, seed=42, regions={"badlands": region}, last_calamity_tick=0
    )
    (boss,) = CalamityService._spawn_world_boss(state, EntityGenerator(42), region)

    tier = DIFFICULTY_TIERS[4]
    assert boss.kind == "world_boss"
    assert boss.identity.role == EntityRole.MONSTER and boss.identity.faction == Faction.MONSTER_HORDE
    assert tier.level_min <= boss.identity.evolution_level <= tier.level_max


@pytest.mark.parametrize("kind", ["monster", "goblin", "world_boss"])
def test_a_spawned_monster_has_a_home_at_the_spawn_point_and_a_positive_leash(kind):
    mob = EntityGenerator(42).spawn_monster(pos=(12.0, 7.0), kind=kind)

    assert mob.navigation.home_position == (12.0, 7.0)
    assert mob.navigation.leash_radius > 0


@pytest.mark.parametrize("world_id", _corpus_worlds())
def test_every_compiled_entity_carries_a_valid_loadout(world_id):
    """Every stack is a known item with a positive quantity, and no purse is negative."""
    state = compile_world(world_id, 42)
    for entity in state.entities.values():
        assert entity.inventory.gold >= 0, f"{world_id}: entity {entity.id} has negative gold"
        for stack in entity.inventory.items:
            assert ItemRegistry.get(stack.item_id) is not None, f"{world_id}: entity {entity.id} holds unknown item {stack.item_id!r}"
            assert stack.quantity > 0, f"{world_id}: entity {entity.id} holds {stack.quantity} of {stack.item_id!r}"
