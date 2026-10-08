import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, TaskComponent, BuildingState
from src.engine.service_prices import REST_PRICE_GOLD
from src.engine.town_resolution import TownResolutionSystem
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
    raw_update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "REST"}))
    })
    return TownResolutionSystem.resolve(state, raw_update).entity_updates[1]


def test_building_interaction_inn_rest_recovery():
    # A bed is bought (SURV-06): its effects ride on the paid transfer, readiness is granted to a subject that can pay.
    upd = _inn_rest_update(gold=REST_PRICE_GOLD)
    (bed,) = upd.resource_transfers
    assert bed.gold_delta == -REST_PRICE_GOLD
    assert bed.combat_upd.hp_delta == 5
    assert bed.biological_upd.sleep_debt_delta == -5.0
    assert upd.readiness_delta == 10.0


def test_inn_rest_without_gold_grants_no_readiness():
    upd = _inn_rest_update(gold=0)
    assert upd.readiness_delta == 0.0  # the resolver rejects the unpaid transfer, so nothing else is delivered
