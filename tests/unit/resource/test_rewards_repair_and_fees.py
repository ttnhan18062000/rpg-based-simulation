"""Rewards come out of a payer, a repair is paid once, fees go to the ground's owner (EXCH-02, decisions 38 and 58; specs ME-S23 and ME-S24)."""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.conservation import ResourceTransactionResolver
from src.core.enums import Faction, ReasonCode
from src.core.state import AuthoritativeState, BuildingState, InventoryComponent, ItemStack, OwedRecord, RegionState
from src.core.treasury import treasury_key
from src.core.update_models.resources import ResourceTransferIntent
from src.core.updates import EquipmentUpdate, EntityUpdate, StateUpdate
from src.engine.cadence import SystemCadence
from src.engine.domain.core_actions import CoreActions
from src.engine.town_resolution import TownResolutionSystem

HERO = int(Faction.HERO_GUILD)
KEY = treasury_key(HERO)


def _hero(eid=1, gold=0, items=None):
    return V2EntityBuilder(eid).kind("hero").location(2.0, 2.0).combat(alive=True, hp=10).inventory(gold=gold, items=items or []).build()


def _quest_intent(gold):
    return ResourceTransferIntent(source_id="q1", source_kind="QUEST", gold_delta=gold, transfer_kind="QUEST_REWARD",
                                  treasury_faction=HERO, treasury_pays=True)


def _state(treasury, owed=None, tick=40):
    region = RegionState(id="town", name="Town", bounds=(0, 0, 20, 20), kind="TOWN", owner_faction_id=HERO)
    return AuthoritativeState(tick=tick, seed=1, regions={"town": region}, entities={1: _hero(1), 2: _hero(2)},
                              global_resources={KEY: treasury}, owed=owed or {})


def test_a_quest_reward_is_paid_from_the_treasury_which_falls_by_the_same_amount():
    state = _state(100.0)
    res = ResourceTransactionResolver.resolve(state, state.entities[1], _quest_intent(30))
    assert res.accepted and res.inventory_update.gold_delta == 30 and res.treasury_update.gold_delta == -30 and res.owed is None


def test_a_short_treasury_owes_the_reward_and_no_coin_appears():
    state = _state(10.0)
    res = ResourceTransactionResolver.resolve(state, state.entities[1], _quest_intent(30))
    assert res.accepted and res.inventory_update.gold_delta == 0 and res.treasury_update is None
    assert (res.owed.creditor_id, res.owed.debtor_faction, res.owed.amount, res.owed.posted_tick) == (1, HERO, 30, 40)


def test_a_second_reward_in_the_same_tick_cannot_overspend_the_treasury():
    state = _state(40.0)
    pending = {KEY: -30.0}   # the first reward of this tick already took 30
    res = ResourceTransactionResolver.resolve(state, state.entities[2], _quest_intent(30), treasury_pending=pending)
    assert res.owed is not None and res.owed.amount == 30


def test_debts_are_paid_oldest_first_when_the_treasury_can_and_the_queue_waits_at_the_first_it_cannot_meet():
    owed = {"a": OwedRecord("a", 1, HERO, 30, 10), "b": OwedRecord("b", 2, HERO, 20, 20)}
    out = TownResolutionSystem.resolve(_state(35.0, owed), StateUpdate(), cadence=SystemCadence())
    assert out.owed_remove == ["a"]                                    # 35 covers the oldest (30); the next (20) must wait
    assert out.entity_updates[1].inventory.gold_delta == 30 and 2 not in out.entity_updates
    assert out.resource_updates[KEY] <= 5.0                            # the debt came out of the treasury (upkeep may take more)


def test_a_debt_to_a_dead_creditor_is_written_off_without_moving_coin():
    state = _state(100.0, {"a": OwedRecord("a", 1, HERO, 30, 10)})
    dead = replace(state.entities[1], combat=replace(state.entities[1].combat, alive=False))
    state = replace(state, entities={**state.entities, 1: dead})
    out = TownResolutionSystem.resolve(state, StateUpdate(), cadence=SystemCadence())
    assert out.owed_remove == ["a"] and 1 not in out.entity_updates


def test_a_kill_pays_no_coin_only_experience():
    from src.engine.combat import CombatResolutionSystem
    attacker = V2EntityBuilder(1).kind("hero").location(1.0, 1.0).combat(alive=True, hp=100, atk=500, readiness=100.0).build()
    victim = V2EntityBuilder(2).kind("monster").location(1.0, 2.0).combat(alive=True, hp=1).inventory(gold=9).build()
    state = AuthoritativeState(tick=5, seed=1, entities={1: attacker, 2: victim})
    upd = CombatResolutionSystem.resolve_attack(attacker, victim, state)
    assert all(t.gold_delta == 0 for t in upd.resource_transfers)


def _smith(gold=0):
    return BuildingState(id=9, kind="blacksmith", position=(2, 2), functional=True, inventory=InventoryComponent(gold=gold))


def _worn(eid=1, gold=0, items=None):
    e = _hero(eid, gold, items)
    return replace(e, equipment=replace(e.equipment, durability={"weapon": 50.0}))


def test_a_repair_at_the_smith_is_charged_once_into_the_smiths_purse():
    entity = _worn(gold=100)
    state = AuthoritativeState(tick=5, seed=1, entities={1: entity}, buildings={9: _smith()}, building_tiles={(2, 2): "blacksmith"})
    upd = CoreActions.execute_repair(entity, 5, state)[1]
    (intent,) = upd.resource_transfers
    assert intent.source_id == 9 and intent.gold_cost == 25 and intent.gold_delta == 0
    res = ResourceTransactionResolver.resolve(state, entity, intent)
    assert res.accepted and res.inventory_update.gold_delta == -25 and res.building_update.inventory.gold_delta == 25


def test_away_from_a_smith_a_carried_kit_is_used_up_and_no_coin_moves():
    entity = _worn(gold=100, items=[ItemStack("repair_kit", 1)])
    state = AuthoritativeState(tick=5, seed=1, entities={1: entity})
    upd = CoreActions.execute_repair(entity, 5, state)[1]
    assert not upd.resource_transfers
    assert upd.equipment.durability_set == {"weapon": 100.0}
    assert [(s.item_id, s.quantity) for s in upd.inventory.items_remove] == [("repair_kit", 1)] and upd.inventory.gold_delta == 0


def test_with_no_smith_and_no_kit_nothing_is_offered_and_nothing_changes():
    entity = _worn(gold=100)
    state = AuthoritativeState(tick=5, seed=1, entities={1: entity})
    upd = CoreActions.execute_repair(entity, 5, state)[1]
    assert not upd.resource_transfers and upd.equipment is None and upd.inventory is None


def test_a_gold_sink_fee_is_paid_to_the_treasury_of_the_faction_holding_the_ground():
    entity = _hero(1, gold=50)
    state = _state(0.0)
    intent = ResourceTransferIntent(source_id="gold_sink", source_kind="SERVICE_FEE", gold_cost=1, gold_delta=0, transfer_kind="FEE", treasury_faction=HERO)
    res = ResourceTransactionResolver.resolve(state, entity, intent)
    assert res.accepted and res.inventory_update.gold_delta == -1 and res.treasury_update.gold_delta == 1
