"""A body holds the dead entity's coin; the coin is taken by a looter or escheats to the ground's owner at decay (EXCH-02, decisions 38 and 58)."""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, CorpseState, InventoryComponent, ItemStack, RegionState
from src.core.treasury import treasury_key
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


def _decay_state(owner):
    region = RegionState(id="r", name="R", bounds=(0, 0, 10, 10), owner_faction_id=owner)
    corpse = CorpseState(id=9, original_entity_id=1, position=(2.0, 2.0), items=[], decay_tick=5, gold=7)
    return AuthoritativeState(tick=10, seed=1, regions={"r": region}, corpses={9: corpse})


def test_a_decayed_body_pays_its_coin_to_the_treasury_of_the_faction_holding_the_ground():
    out = _decay(_decay_state(int(Faction.HERO_GUILD)))
    assert 9 in out.corpses_remove
    assert out.resource_updates[treasury_key(Faction.HERO_GUILD)] == 7


def test_a_decayed_body_on_unheld_ground_pays_the_neutral_treasury():
    out = _decay(_decay_state(None))
    assert out.resource_updates[treasury_key(Faction.NEUTRAL)] == 7
