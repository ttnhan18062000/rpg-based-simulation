import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.strategic import BlockerState
from src.town.inn import InnAction
from src.town.home import HomeAction
from src.town.class_hall import ClassHallAction
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline

@pytest.mark.v2_contract
def test_class_hall_inn_rest_recovery():
    # 1. Setup: High sleep debt, 10 gold
    entity = (V2EntityBuilder(99)
        .kind("hero")
        .location(0, 0)
        .biological(sleep_debt=80.0, hunger=50.0)
        .inventory(gold=20)
        .build())
    state = AuthoritativeState(tick=100, seed=42, entities={99: entity})
    
    # 2. Inn Rest
    upd = InnAction.rest(entity, state)
    assert upd is not None
    
    # 3. Refine & Apply
    upd = AuthoritativeApplyPipeline.refine(state, upd)
    next_state = ApplyPath.apply_generation(state, upd)
    new_ent = next_state.entities[99]
    
    assert new_ent.biological.sleep_debt == 0.0
    # Hunger: 50.0 - 20.0 (Inn) + 0.1 (ApplyPath passive decay) = 30.1
    assert abs(new_ent.biological.hunger - 30.1) < 0.001
    assert new_ent.biological.well_rested_until == 200 # 100 + 100
    assert new_ent.inventory.gold == 10

@pytest.mark.v2_contract
def test_home_upgrade_blocker():
    # 1. Setup: Maintenance blocker
    blocker = BlockerState(id="m1", kind="maintenance", subject="roof")
    entity = (V2EntityBuilder(99)
        .kind("hero")
        .location(0, 0)
        .strategic(blockers={"m1": blocker})
        .inventory(gold=150)
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity})
    
    # 2. Home Upgrade
    upd = HomeAction.upgrade(entity, state)
    assert upd is not None
    
    # 3. Refine & Apply
    upd = AuthoritativeApplyPipeline.refine(state, upd)
    next_state = ApplyPath.apply_generation(state, upd)
    assert "m1" not in next_state.entities[99].strategic.blockers
    assert next_state.entities[99].inventory.gold == 50

@pytest.mark.v2_contract
def test_class_hall_training():
    # 1. Setup: Capability blocker
    blocker = BlockerState(id="c1", kind="capability", subject="iron_smithing")
    entity = (V2EntityBuilder(99)
        .kind("hero")
        .location(0, 0)
        .strategic(blockers={"c1": blocker})
        .inventory(gold=60)
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity})
    
    # 2. Train
    upd = ClassHallAction.train(entity, "iron_smithing", state)
    assert upd is not None
    
    # 3. Refine & Apply
    upd = AuthoritativeApplyPipeline.refine(state, upd)
    next_state = ApplyPath.apply_generation(state, upd)
    assert "c1" not in next_state.entities[99].strategic.blockers
    assert "iron_smithing" in next_state.entities[99].identity.known_recipes
    assert next_state.entities[99].inventory.gold == 10
