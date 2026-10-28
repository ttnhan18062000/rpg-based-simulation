"""TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (owner decisions 44 and 73): nothing is free.

A meal at the inn gives 60 hunger for 5 gold, a bed gives hp +5 and readiness +10 for 10 gold, each applied with the payment or not at all, with no
clamp to what the subject holds. Every case runs through the real path: `ActionRouter.execute_action`, then `ResourceTransactionSystem.resolve_all`.
"""
from __future__ import annotations

import pickle
from dataclasses import asdict, replace

from src.core.builder import V2EntityBuilder
from src.core.enums import ReasonCode
from src.core.state import AuthoritativeState, BuildingState, InventoryComponent
from src.core.updates import EntityUpdate, ResourceTransferIntent, StateUpdate
from src.engine.domain.action_router import ActionRouter
from src.engine.economy import ResourceTransactionSystem
from src.engine.service_prices import EAT_PRICE_GOLD, INN_MEAL_HUNGER, REST_PRICE_GOLD


def _world(gold: int, *, hunger: float = 80.0, items=()):
    ent = (V2EntityBuilder(1).kind("worker").properties({"species_id": "human"}).location(11.0, 10.0).biological(hunger=hunger).inventory(gold=gold).build())
    ent = replace(ent, inventory=replace(ent.inventory, items=list(items)))
    inn = BuildingState(id=1, kind="inn", position=(10, 10), functional=True, inventory=InventoryComponent(gold=0))
    return ent, AuthoritativeState(tick=1, seed=1, entities={1: ent}, buildings={1: inn}, building_tiles={(10, 10): "inn"}, town_tiles={(11, 10), (10, 10)})


def _act(action: str, gold: int, **kw):
    ent, state = _world(gold, **kw)
    upd = ActionRouter.execute_action(ent, {"action": action, "target_id": 1}, state.tick, None, state)[1]
    return ent, state, upd


def _resolve(state, upd):
    return ResourceTransactionSystem.resolve_all(state, StateUpdate(entity_updates={1: upd})).entity_updates[1]


def _purse_change(state, upd):
    out = ResourceTransactionSystem.resolve_all(state, StateUpdate(entity_updates={1: upd}))
    building = out.building_updates.get(1)
    return (building.inventory.gold_delta if building is not None and building.inventory else 0), (out.entity_updates[1].inventory.gold_delta if out.entity_updates[1].inventory else 0)


# ---- the meal -------------------------------------------------------------------------------------------------------------------------------------

def test_a_broke_subject_beside_the_inn_is_not_fed_and_the_task_ends_with_a_typed_failure():
    _, state, upd = _act("EAT", EAT_PRICE_GOLD - 1)
    assert not upd.resource_transfers and upd.biological is None
    assert upd.navigation.failure_reason == ReasonCode.SOURCE_MISSING and upd.readiness_delta == 0.0


def test_a_subject_holding_exactly_the_price_pays_in_full_and_is_fed_in_one_accepted_transfer():
    _, state, upd = _act("EAT", EAT_PRICE_GOLD)
    (meal,) = upd.resource_transfers
    assert meal.gold_cost == EAT_PRICE_GOLD and meal.gold_delta == 0 and meal.biological_upd.hunger_delta == -INN_MEAL_HUNGER == -60.0
    out = _resolve(state, upd)
    assert [r.accepted for r in out.intent_results] == [True]
    assert out.biological.hunger_delta == -60.0 and out.biological.last_meal_tick_set == 1
    assert out.inventory.gold_delta == -EAT_PRICE_GOLD
    assert _purse_change(state, upd) == (EAT_PRICE_GOLD, -EAT_PRICE_GOLD)  # coin is conserved: the building gets what the subject paid


def test_a_meal_rejected_at_apply_time_gives_no_hunger_relief_and_moves_no_coin():
    """The race the up-front check cannot close: the purse is empty when the transfer resolves. The relief rides on the transfer, so it is refused with it."""
    _, state, upd = _act("EAT", EAT_PRICE_GOLD)
    ent = state.entities[1]
    broke_state = replace(state, entities={1: replace(ent, inventory=replace(ent.inventory, gold=0))})
    out = _resolve(broke_state, upd)
    assert [r.accepted for r in out.intent_results] == [False] and out.intent_results[0].reason == ReasonCode.ACTION_EXHAUSTION
    assert out.biological is None and out.inventory is None


def test_carried_food_is_eaten_without_the_inn_and_without_gold():
    from src.core.models.inventory import ItemStack
    from src.core.items import food_hunger_recovery

    ent, state = _world(0)
    food = next(i for i in ("bread", "cooked_meat", "meal", "wild_berries", "berries") if food_hunger_recovery(i) > 0.0)
    ent = replace(ent, inventory=replace(ent.inventory, items=[ItemStack(item_id=food, quantity=1)]))
    state = replace(state, entities={1: ent})
    upd = ActionRouter.execute_action(ent, {"action": "EAT", "target_id": 1}, state.tick, None, state)[1]
    assert upd.navigation is None or upd.navigation.failure_reason is None
    assert any(t.items_remove for t in upd.resource_transfers)


def test_eat_with_nothing_carried_and_no_inn_fails_typed_and_does_not_burn_readiness():
    ent, state = _world(50)
    state = replace(state, buildings={}, building_tiles={})
    upd = ActionRouter.execute_action(ent, {"action": "EAT"}, state.tick, None, state)[1]
    assert upd.biological is None and not upd.resource_transfers and upd.navigation.failure_reason == ReasonCode.SOURCE_MISSING


def test_the_typed_failure_does_not_fire_when_an_inn_serves_a_subject_that_can_pay():
    """The merge order: the failure is for nothing to eat, not for the plain EAT update the inn's transfer is merged into."""
    _, state, upd = _act("EAT", 50)
    assert upd.navigation is None or upd.navigation.failure_reason is None
    assert upd.readiness_delta == -100.0 and len(upd.resource_transfers) == 1


# ---- the bed --------------------------------------------------------------------------------------------------------------------------------------

def test_a_bed_is_refused_up_front_to_a_subject_without_the_price():
    _, state, upd = _act("REST", REST_PRICE_GOLD - 1)
    assert not upd.resource_transfers and upd.readiness_delta == 0.0 and upd.combat is None


def test_a_paid_bed_gives_hp_and_readiness_and_takes_the_full_price():
    _, state, upd = _act("REST", REST_PRICE_GOLD)
    assert upd.readiness_delta == 0.0  # the bed's effects ride on the transfer, none on the update itself
    out = _resolve(state, upd)
    assert out.inventory.gold_delta == -REST_PRICE_GOLD and out.combat.hp_delta == 5 and out.readiness_delta == 10.0
    assert _purse_change(state, upd) == (REST_PRICE_GOLD, -REST_PRICE_GOLD)


def test_a_bed_rejected_at_apply_time_gives_no_gold_hp_or_readiness():
    """The regression pin for the free rest: readiness used to sit on the update and survived a rejected payment."""
    _, state, upd = _act("REST", REST_PRICE_GOLD)
    ent = state.entities[1]
    out = _resolve(replace(state, entities={1: replace(ent, inventory=replace(ent.inventory, gold=0))}), upd)
    assert [r.accepted for r in out.intent_results] == [False]
    assert out.readiness_delta == 0.0 and out.combat is None and out.inventory is None


def test_a_bed_in_a_rolled_back_group_gives_nothing():
    _, state, upd = _act("REST", REST_PRICE_GOLD)
    (bed,) = upd.resource_transfers
    failing = ResourceTransferIntent(source_id=1, source_kind="TOWN_SERVICE", gold_cost=10_000, transfer_kind="REST", group_id="g")
    grouped = replace(upd, resource_transfers=[replace(bed, group_id="g"), failing])
    ent = state.entities[1]
    out = _resolve(replace(state, entities={1: replace(ent, inventory=replace(ent.inventory, gold=50))}), grouped)
    assert [r.accepted for r in out.intent_results] == [False, False]
    assert out.readiness_delta == 0.0 and out.combat is None and out.inventory is None


def test_the_intent_with_a_readiness_field_round_trips():
    intent = ResourceTransferIntent(source_id=1, source_kind="TOWN_SERVICE", gold_cost=10, transfer_kind="REST", readiness_delta=10.0)
    assert ResourceTransferIntent(**asdict(intent)) == intent and pickle.loads(pickle.dumps(intent)) == intent
    assert ResourceTransferIntent(source_id=1, source_kind="X").readiness_delta == 0.0  # the default leaves every other transfer unchanged
