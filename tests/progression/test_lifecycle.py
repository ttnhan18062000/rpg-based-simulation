import pytest
from dataclasses import replace
from src.core.state import EntityState, LifecycleComponent, AuthoritativeState, CombatComponent
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate, InventoryUpdate
from src.systems.lifecycle import LifecycleSystem
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction

def test_aging_per_tick():
    """Verify that entities age by 1 tick every generation."""
    ent = (V2EntityBuilder(1)
           .at((0.0, 0.0))
           .with_lifecycle(age_ticks=50)
           .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent})
    
    update = StateUpdate()
    next_state = ApplyPath.apply_generation(state, update, 101, 101)
    
    assert next_state.entities[1].lifecycle.age_ticks == 51

def test_death_by_old_age():
    """Verify that reaching max age triggers death."""
    # Note: V2EntityBuilder doesn't have max_age_ticks setter, we use replace for now
    ent = (V2EntityBuilder(1)
           .at((0.0, 0.0))
           .with_lifecycle(age_ticks=1000)
           .build())
    ent = replace(ent, lifecycle=replace(ent.lifecycle, max_age_ticks=1000))
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent})
    
    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)
    
    ent_upd = refined.entity_updates[1]
    assert ent_upd.active is False
    assert ent_upd.lifecycle.death_reason_set == "OLD_AGE"
    assert ent_upd.lifecycle.is_permadeath_set is True

def test_combat_death_classification():
    """Verify that a KILL outcome is classified as a lifecycle death."""
    ent = (V2EntityBuilder(1)
           .at((0.0, 0.0))
           .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent})
    
    # Simulate a KILL outcome from combat
    kill_upd = CombatUpdate(outcome_kind="KILL", is_lethal=True)
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=kill_upd)})
    
    refined = LifecycleSystem.resolve_lifecycle(state, update)
    
    ent_upd = refined.entity_updates[1]
    assert ent_upd.active is False
    assert ent_upd.lifecycle.death_reason_set == "COMBAT"

def test_succession_and_heirloom_transfer():
    """Verify that heirlooms are transferred to the heir upon death."""
    # Build parent with heir and heirlooms
    parent = (V2EntityBuilder(1)
              .at((0.0, 0.0))
              .build())
    parent_life = LifecycleComponent(
        age_ticks=100, max_age_ticks=100, 
        heir_entity_id=2, 
        heirlooms=["Excalibur"]
    )
    parent = replace(parent, lifecycle=parent_life)
    
    heir = (V2EntityBuilder(2)
            .at((1.0, 1.0))
            .build())
    
    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: heir})
    
    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)
    
    # Heir should receive the item via transaction
    heir_upd = refined.entity_updates[2]
    assert len(heir_upd.resource_transfers) > 0
    transfer = heir_upd.resource_transfers[0]
    assert any(stack.item_id == "Excalibur" for stack in transfer.items_add)

def test_near_death_hardening_logic():
    """Directly test the hardening logic in the pipeline."""
    from src.engine.pipeline import AuthoritativeApplyPipeline
    
    hero = (V2EntityBuilder(1)
            .kind("HERO")
            .at((0.0, 0.0))
            .with_identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
            .with_combat(hp=100, max_hp=100)
            .build())
            
    attacker = (V2EntityBuilder(2)
                .kind("MONSTER")
                .at((1.0, 0.0))
                .with_identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
                .with_combat(atk=105)
                .readiness(100.0)
                .build())
    
    state = AuthoritativeState(tick=100, seed=42, entities={1: hero, 2: attacker})
    
    # Simulate an attack that would leave hero at low HP
    from src.core.updates import TaskUpdate
    task_upd = TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 1})
    update = StateUpdate(entity_updates={2: EntityUpdate(entity_id=2, task=task_upd)})
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Hero should have a combat update with max_hp_delta
    hero_upd = refined.entity_updates[1]
    assert hero_upd.combat is not None
    assert hero_upd.combat.max_hp_delta == 5
