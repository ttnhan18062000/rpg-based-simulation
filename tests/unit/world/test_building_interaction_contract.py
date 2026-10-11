import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, TaskComponent, BuildingState
from src.engine.service_prices import REST_PRICE_GOLD
from src.engine.domain.action_router import ActionRouter
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate

from src.core.builder import V2EntityBuilder

def create_mock_entity(eid, pos=(10, 10), hp=50):
    return (V2EntityBuilder(eid)
        .kind("hero")
        .location(*pos)
        .combat(hp=hp)
        .build())

def _inn_rest_update(gold):
    entity = replace(create_mock_entity(1, pos=(5.0, 5.0), hp=50), inventory=replace(create_mock_entity(1).inventory, gold=gold))
    state = AuthoritativeState(
        tick=1, seed=42,
        entities={1: entity},
        town_tiles={(5, 5)},
        building_tiles={(5, 5): "inn"},
        buildings={10: BuildingState(id=10, kind="inn", position=(5.0, 5.0), functional=True)}
    )
    # The bed lands with the action (building_services.py), not in the cadence-gated town phase.
    return ActionRouter.execute_action(entity, {"action": "REST", "target_id": 10}, state.tick, None, state)[1]


def test_building_interaction_inn_rest_recovery():
    # Free beds stay as on main (owner decision 44): the recovery is on the update and the 10-gold charge is clamped at what the subject holds.
    upd = _inn_rest_update(gold=REST_PRICE_GOLD)
    (bed,) = upd.resource_transfers
    assert bed.gold_delta == -REST_PRICE_GOLD
    assert upd.combat.hp_delta == 5
    assert upd.biological.sleep_debt_delta == 0.0  # decision 41 (ruled): the debt falls per tick while asleep; a bed has no separate rate
    assert upd.readiness_delta == 10.0


def test_inn_rest_without_gold_still_recovers_as_on_main():
    upd = _inn_rest_update(gold=0)
    assert upd.readiness_delta == 10.0 and upd.combat.hp_delta == 5  # free beds stay on until the removal lands
