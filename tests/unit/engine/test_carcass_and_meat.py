"""Decision 44 (commit iii, first half): a body leaves meat, the diet gate decides who may eat what, and eating at a corpse is traceable.

Real corpus kinds stand in (wolf: meat-only diet; human: omnivore); no exact meat figure beyond the coarse yield bands is pinned.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

import src.core.registries  # noqa: F401  (seeds the item registry from content)
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction, ReasonCode
from src.core.conservation import ResourceTransactionResolver
from src.core.items import food_class, food_hunger_recovery
from src.core.models.inventory import ItemStack
from src.core.state import AuthoritativeState, CorpseState, RegionState
from src.engine import behavior_consumers
from src.engine.appraisal import can_eat_item, can_use_inn_meal
from src.engine.carcass import RAW_MEAT_ITEM, body_meat
from src.engine.domain.core_actions import carried_meal, corpse_meal, eat_at_corpse_update


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository

    repo = CatalogRepository("data/content")
    repo.load_all()
    behavior_consumers.configure_behavior_consumers(repo)
    yield
    behavior_consumers.reset_behavior_consumers()


def _creature(eid, species, pos=(10.0, 10.0), items=()):
    return (V2EntityBuilder(eid).kind("monster").location(*pos)
            .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, properties={"species_id": species})
            .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True).lifecycle(active=True)
            .biological(hunger=90.0).build()) if not items else replace(
        _creature(eid, species, pos), inventory=replace(_creature(eid, species, pos).inventory, items=list(items)))


def test_food_values_of_existing_foods_are_unchanged_and_raw_meat_fills_less_than_a_prepared_meal():
    assert (food_class("wild_berries"), food_hunger_recovery("wild_berries")) == ("plant", 30.0)
    assert (food_class("travel_ration"), food_hunger_recovery("travel_ration")) == ("prepared", 30.0)
    assert food_class(RAW_MEAT_ITEM) == "meat"
    assert 0.0 < food_hunger_recovery(RAW_MEAT_ITEM) < food_hunger_recovery("travel_ration")
    assert food_class("iron_ore") is None


def test_a_body_leaves_meat_sized_by_its_kind_and_a_body_that_feeds_nobody_leaves_none():
    wolf, human, undead = _creature(1, "wolf"), _creature(2, "human"), _creature(3, "undead")
    orc = _creature(4, "orc")
    assert body_meat(wolf)[0].item_id == RAW_MEAT_ITEM and body_meat(human)[0].quantity >= 1
    assert body_meat(orc)[0].quantity > body_meat(_creature(5, "goblin"))[0].quantity  # large yields more than small
    assert body_meat(undead) == []


def test_the_diet_gate_a_meat_only_kind_eats_no_berries_and_no_inn_meal_while_a_person_eats_both():
    wolf, human = _creature(1, "wolf"), _creature(2, "human")
    assert can_eat_item(wolf, RAW_MEAT_ITEM) and not can_eat_item(wolf, "wild_berries") and not can_eat_item(wolf, "travel_ration")
    assert all(can_eat_item(human, i) for i in (RAW_MEAT_ITEM, "wild_berries", "travel_ration"))
    assert can_use_inn_meal(human) and not can_use_inn_meal(wolf)
    assert not can_eat_item(wolf, "iron_ore")


def test_a_carried_meal_obeys_the_gate_and_an_undeclared_species_keeps_the_legacy_behaviour():
    berries = [ItemStack("wild_berries", 2)]
    assert carried_meal(_creature(1, "wolf", items=berries), 5) == []
    assert carried_meal(_creature(2, "human", items=berries), 5) != []
    legacy = replace(_creature(3, "human", items=berries), identity=replace(_creature(3, "human").identity, properties={}))
    assert carried_meal(legacy, 5) != []


def _state(corpse, *entities):
    region = RegionState(id="field", name="Field", bounds=(0, 0, 60, 60))
    return AuthoritativeState(tick=5, seed=1, entities={e.id: e for e in entities}, regions={"field": region}, corpses={corpse.id: corpse})


def _corpse(items, pos=(10.0, 11.0)):
    return CorpseState(id=1000007, original_entity_id=7, position=pos, items=items, decay_tick=105)


def test_eating_at_a_corpse_takes_one_unit_traceably_and_applies_the_hunger_recovery():
    wolf = _creature(1, "wolf")
    corpse = _corpse([ItemStack(RAW_MEAT_ITEM, 2)])
    state = _state(corpse, wolf)
    update = eat_at_corpse_update(wolf, corpse.id, state, 5)
    (intent,) = update.resource_transfers
    assert intent.source_kind == "CORPSE_FOOD" and intent.source_id == corpse.id  # traceable to the body
    result = ResourceTransactionResolver.resolve(state, wolf, intent)
    assert result.accepted
    assert result.corpse_update.items == [ItemStack(RAW_MEAT_ITEM, 1)]  # meat leaves the carcass only by being eaten
    assert result.biological_update.hunger_delta == -food_hunger_recovery(RAW_MEAT_ITEM)


def test_eating_at_a_corpse_refuses_what_the_diet_excludes_what_is_out_of_reach_and_a_locked_corpse():
    wolf = _creature(1, "wolf")
    assert corpse_meal(wolf, _corpse([ItemStack("wild_berries", 3)]), 5) == []  # not in the wolf's diet
    assert corpse_meal(wolf, _corpse([ItemStack(RAW_MEAT_ITEM, 1)], pos=(10.0, 30.0)), 5) == []  # out of reach
    corpse = _corpse([ItemStack(RAW_MEAT_ITEM, 1)])
    state = _state(corpse, wolf)
    (intent,) = corpse_meal(wolf, corpse, 5)
    locked = ResourceTransactionResolver.resolve(state, wolf, intent, reservations={("CORPSE", corpse.id): 1})
    assert not locked.accepted and locked.reason == ReasonCode.TARGET_LOCKED
    gone = eat_at_corpse_update(wolf, 999, state, 5)
    assert gone.navigation.failure_reason == ReasonCode.SOURCE_MISSING and not gone.resource_transfers


def test_a_death_through_the_apply_path_leaves_the_kinds_meat_on_the_corpse_whatever_the_cause():
    from src.core.state import AuthoritativeState
    from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
    from src.engine.apply import ApplyPath

    for species, expect_meat in (("wolf", True), ("undead", False)):
        victim = _creature(1, species)
        state = AuthoritativeState(tick=1, seed=42, entities={1: victim})
        update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate(hp_delta=-500, alive_set=False))})
        corpse = ApplyPath.apply_generation(state, update, next_tick=2).corpses[1000001]
        assert any(stack.item_id == RAW_MEAT_ITEM for stack in corpse.items) is expect_meat
