"""A body holds the dead entity's coin; the coin is taken by a looter or lies where it fell as a purse on the ground at decay (ruling 61) (EXCH-02, decisions 38 and 58)."""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, CorpseState, InventoryComponent, ItemStack, RegionState
from src.core.treasury import total_coin, treasury_key
from src.core.update_models.resources import ResourceTransferIntent
from src.core.conservation import ResourceTransactionResolver
from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.engine.world_dynamics import WorldDynamicsSystem


def _hero(eid=1, gold=0, items=None):
    return V2EntityBuilder(eid).kind("hero").location(2.0, 2.0).combat(alive=True, hp=10).inventory(gold=gold, items=items or []).build()


def test_a_killed_entity_leaves_its_coin_and_goods_on_the_body_not_on_its_record():
    state = AuthoritativeState(tick=10, seed=1, entities={1: _hero(gold=7, items=[ItemStack("wood", 2)])})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate(hp_delta=-10, alive_set=False))})
    after = ApplyPath.apply_generation(state, update)
    corpse = after.corpses[1000001]
    assert corpse.gold == 7 and [(s.item_id, s.quantity) for s in corpse.items] == [("wood", 2)]
    assert after.entities[1].inventory.gold == 0 and not after.entities[1].inventory.items


def test_a_looter_takes_the_coin_the_body_holds():
    looter = _hero(2)
    corpse = CorpseState(id=9, original_entity_id=1, position=(2.0, 2.0), items=[ItemStack("wood", 2)], decay_tick=500, gold=7)
    state = AuthoritativeState(tick=10, seed=1, entities={2: looter}, corpses={9: corpse})
    intent = ResourceTransferIntent(source_id=9, source_kind="CORPSE", items_add=[ItemStack("wood", 2)], gold_delta=1000)  # whatever the intent says
    res = ResourceTransactionResolver.resolve(state, looter, intent)
    assert res.accepted and res.inventory_update.gold_delta == 7 and res.corpse_remove == 9


def _decay(state):
    from src.systems.world_systems.generator import EntityGenerator
    return WorldDynamicsSystem.resolve_dynamics(state, StateUpdate(), EntityGenerator(1))


def _decay_state(owner=None, gold=7):
    region = RegionState(id="r", name="R", bounds=(0, 0, 10, 10), owner_faction_id=owner)
    corpse = CorpseState(id=9, original_entity_id=1, position=(2.0, 2.0), items=[], decay_tick=5, gold=gold)
    return AuthoritativeState(tick=10, seed=1, regions={"r": region}, corpses={9: corpse})


def test_a_decayed_body_leaves_its_coin_where_it_fell_as_a_purse_on_the_ground_not_in_any_treasury():
    state = _decay_state(int(Faction.HERO_GUILD))
    out = _decay(state)
    assert 9 in out.corpses_remove
    assert not out.resource_updates.get(treasury_key(Faction.HERO_GUILD))
    purse, = out.ground_items_add_or_update
    assert (purse.gold, purse.position, purse.quantity, purse.item_id) == (7, (2.0, 2.0), 0, "")


def test_the_purse_carries_whose_body_it_fell_from_and_when_and_keeps_it_through_serialisation():
    out = _decay(_decay_state())
    purse, = out.ground_items_add_or_update
    assert (purse.source_entity_id, purse.dropped_tick) == (1, 11)
    canon = purse.to_canonical_dict()
    assert (canon["gold"], canon["source_entity_id"], canon["dropped_tick"]) == (7, 1, 11)


def test_a_body_without_coin_leaves_no_purse():
    assert _decay(_decay_state(gold=0)).ground_items_add_or_update == []


def test_coin_is_conserved_across_death_decay_and_loot_and_an_unlooted_purse_stays_put():
    state = AuthoritativeState(tick=10, seed=1, entities={1: _hero(gold=7), 2: _hero(2)})
    before = total_coin(state)
    died = ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate(hp_delta=-10, alive_set=False))}))
    assert total_coin(died) == before
    died = replace(died, tick=1000)  # the body's decay tick has passed
    decayed = ApplyPath.apply_generation(died, _decay(died))
    assert not decayed.corpses and total_coin(decayed) == before
    purse, = decayed.ground_items.values()
    assert purse.gold == 7 and purse.source_entity_id == 1
    later = ApplyPath.apply_generation(decayed, StateUpdate())  # nobody picks it up: it stays
    assert later.ground_items == decayed.ground_items and total_coin(later) == before
    looter = decayed.entities[2]
    res = ResourceTransactionResolver.resolve(decayed, looter, ResourceTransferIntent(source_id=purse.id, source_kind="GROUND_ITEM", transfer_kind="LOOT"))
    assert res.accepted and res.inventory_update.gold_delta == 7 and res.ground_item_remove == purse.id
    taken = ApplyPath.apply_generation(decayed, StateUpdate(entity_updates={2: EntityUpdate(entity_id=2, inventory=res.inventory_update)},
                                                           ground_items_remove=[purse.id]))
    assert taken.entities[2].inventory.gold == 7 and not taken.ground_items and total_coin(taken) == before
