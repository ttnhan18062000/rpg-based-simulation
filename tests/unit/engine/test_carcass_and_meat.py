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


def test_meat_balances_from_records_alone_through_eating_looting_and_decay():
    """Body meat at death = meat eaten at the corpse + meat looted + meat decayed, each read from its own typed record."""
    from src.core.state import AuthoritativeState
    from src.core.updates import CombatUpdate, EntityUpdate, ResourceTransferIntent, StateUpdate
    from src.domains.world_emergence.schema import WorldEventCategory
    from src.engine.apply import ApplyPath
    from src.engine.world_dynamics import WorldDynamicsSystem
    from src.systems.world_systems.generator import EntityGenerator

    # Source: three orcs die (large bodies), each leaving the same declared yield.
    orcs = {i: _creature(i, "orc", (10.0 + 3 * i, 10.0)) for i in (1, 2, 3)}
    state = AuthoritativeState(tick=1, seed=42, entities=dict(orcs))
    deaths = StateUpdate(entity_updates={i: EntityUpdate(entity_id=i, combat=CombatUpdate(hp_delta=-500, alive_set=False)) for i in orcs})
    state = ApplyPath.apply_generation(state, deaths, next_tick=2)
    meat = {cid: next(s.quantity for s in c.items if s.item_id == RAW_MEAT_ITEM) for cid, c in state.corpses.items()}
    source = sum(meat.values())
    assert source == 3 * body_meat(orcs[1])[0].quantity

    # Sink 1: one unit eaten at corpse 1 by a wolf (CORPSE_FOOD transfer keyed by the corpse id).
    wolf = _creature(9, "wolf", (12.0, 10.0))
    state = replace(state, entities={**state.entities, 9: wolf})
    eat = ResourceTransactionResolver.resolve(state, wolf, corpse_meal(wolf, state.corpses[1000001], 2)[0])
    eaten = sum(1 for _ in [eat] if eat.accepted)  # one unit per meal
    assert eat.accepted and eat.corpse_update.items[0].quantity == meat[1000001] - 1

    # Sink 2: corpse 2 is looted whole (the existing CORPSE transfer).
    loot = ResourceTransactionResolver.resolve(state, wolf, ResourceTransferIntent(
        source_id=1000002, source_kind="CORPSE", items_add=list(state.corpses[1000002].items), transfer_kind="LOOT"))
    looted = sum(s.quantity for s in loot.inventory_update.items_add if s.item_id == RAW_MEAT_ITEM)
    assert loot.accepted and loot.corpse_remove == 1000002

    # Sink 3: corpse 3 decays with its meat on it; the typed MEAT_DECAYED record carries the quantity.
    decay_state = replace(state, tick=state.corpses[1000003].decay_tick)
    refined = WorldDynamicsSystem.resolve_dynamics(decay_state, StateUpdate(), EntityGenerator(42))
    decayed = {e.subject: e.payload["quantity"] for e in refined.world_events_add if e.category == WorldEventCategory.MEAT_DECAYED}
    assert decayed["1000003"] == meat[1000003]

    # Corpse 1 still holds the rest; every unit of the source is accounted for by a record or by what remains.
    remaining = eat.corpse_update.items[0].quantity
    assert source == eaten + looted + int(decayed["1000003"]) + remaining


def test_an_inn_serves_no_meal_to_a_diet_without_prepared_food_however_it_came_to_stand_there():
    """Decision 44, structural: the guard sits at the service itself and at the free-meal relief, not only on the route to the inn."""
    from src.core.state import BuildingState
    from src.engine.building_services import service_delta
    from src.engine.domain.core_actions import eat_update

    inn = BuildingState(id=7, kind="inn", position=(10.0, 10.0), functional=True)
    region = RegionState(id="field", name="Field", bounds=(0, 0, 60, 60))
    for species, served in (("wolf", False), ("human", True)):
        eater = _creature(1, species, (10.0, 10.0))
        state = AuthoritativeState(tick=5, seed=1, entities={1: eater}, regions={"field": region}, buildings={7: inn},
                                   building_tiles={(10, 10): "inn"})
        assert (service_delta(state, eater, "EAT", 5) is not None) is served
        relief = eat_update(eater, 5).biological
        assert (relief is not None and relief.hunger_delta < 0) is served
