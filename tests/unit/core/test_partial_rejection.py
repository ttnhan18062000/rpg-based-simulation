import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate, CombatIntent, TaskUpdate, NavigationUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.enums import ReasonCode, Faction
from src.core.builder import V2EntityBuilder

@pytest.fixture
def base_state():
    e1 = (V2EntityBuilder(1)
          .location(0.0, 0.0)
          .lifecycle(active=True)
          .combat(readiness=100.0)
          .identity(faction=Faction.HERO_GUILD)
          .build())
    return AuthoritativeState(tick=1, seed=42, entities={1: e1})

def test_partial_rejection_occupancy_vs_combat(base_state):
    """
    RPG-INFRA-200: partial_rejection_transparency
    Proof: This test ensures that if an entity proposes both an occupancy change (legal)
           and a combat action (illegal due to range), only the combat action is rejected.
    """
    # 1. Setup target out of range and DIFFERENT FACTION to avoid friendly fire check
    target = (V2EntityBuilder(2)
              .location(100.0, 100.0)
              .lifecycle(active=True)
              .identity(faction=Faction.MONSTER_HORDE)
              .build())
    state = replace(base_state, entities={**base_state.entities, 2: target})
    
    # 2. Propose move (legal) and attack (illegal due to range)
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                navigation=NavigationUpdate(target_set=(5.0, 5.0)),
                task=TaskUpdate(
                    work_kind_set="ENTITY_ACT",
                    payload_set={"action": "ATTACK", "target_id": 2}
                )
            )
        }
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # 3. Verify move was ATTEMPTED and processed (new_position is not None and not the same as start)
    assert refined.entity_updates[1].new_position is not None
    assert refined.entity_updates[1].new_position != (0.0, 0.0)
    assert refined.entity_updates[1].moved_this_tick is True
    
    # 4. Verify combat is rejected for RANGE, not faction
    task_res = refined.entity_updates[1].task
    assert task_res.payload_set.get("outcome") == "FAILURE"
    assert task_res.payload_set.get("reason") == ReasonCode.OUT_OF_RANGE

def test_partial_rejection_occupancy_vs_readiness(base_state):
    """
    Proof: This test ensures that if an entity is not ready, its action is rejected.
    """
    # 1. Setup entity with 0 readiness
    hero = (V2EntityBuilder(1)
            .location(0.0, 0.0)
            .lifecycle(active=True)
            .combat(readiness=0.0)
            .identity(faction=Faction.HERO_GUILD)
            .build())
    # Need a target to avoid TARGET_INVALID, and DIFFERENT FACTION
    target = (V2EntityBuilder(2)
              .location(1.0, 1.0)
              .lifecycle(active=True)
              .identity(faction=Faction.MONSTER_HORDE)
              .build())
    state = replace(base_state, entities={1: hero, 2: target})
    
    # 2. Propose move and action
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                navigation=NavigationUpdate(target_set=(1.0, 1.0)),
                task=TaskUpdate(
                    work_kind_set="ENTITY_ACT",
                    payload_set={"action": "ATTACK", "target_id": 2}
                )
            )
        }
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # 3. Verify action is rejected due to readiness
    task_res = refined.entity_updates[1].task
    assert task_res.payload_set.get("outcome") == "FAILURE"
    assert task_res.payload_set.get("reason") == ReasonCode.INSUFFICIENT_READINESS
