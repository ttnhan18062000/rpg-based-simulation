import pytest
from dataclasses import replace
from src.core.state import EntityState, LifecycleComponent, AuthoritativeState, CombatComponent
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate, InventoryUpdate
from src.systems.lifecycle import LifecycleSystem
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.models.social import SocialBond

def test_aging_per_tick():
    """Verify that entities age by 1 tick every generation."""
    ent = (V2EntityBuilder(1)
           .location(0.0, 0.0)
           .lifecycle(age_ticks=50)
           .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent})
    
    update = StateUpdate()
    next_state = ApplyPath.apply_generation(state, update, 101, 101)
    
    assert next_state.entities[1].lifecycle.age_ticks == 51

def test_death_by_old_age():
    """Verify that reaching max age triggers death."""
    # Note: V2EntityBuilder doesn't have max_age_ticks setter, we use replace for now
    ent = (V2EntityBuilder(1)
           .location(0.0, 0.0)
           .lifecycle(age_ticks=1000)
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
           .location(0.0, 0.0)
           .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent})
    
    # Simulate a KILL outcome from combat
    kill_upd = CombatUpdate(outcome_kind="KILL", is_lethal=True)
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=kill_upd)})
    
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    ent_upd = refined.entity_updates[1]
    assert ent_upd.active is False
    assert ent_upd.lifecycle.death_reason_set == "COMBAT"

def test_permadeath_death_classification():
    """A PERMADEATH outcome (a rebirth-eligible Hero at generation cap, src/engine/combat.py)
    must deactivate the entity the same as a KILL outcome -- regression for a real bug where
    resolve_lifecycle only checked outcome_kind=="KILL", leaving a "permanently dead" Hero
    active=True and still acting."""
    ent = (V2EntityBuilder(1)
           .location(0.0, 0.0)
           .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent})

    permadeath_upd = CombatUpdate(outcome_kind="PERMADEATH", is_lethal=True)
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=permadeath_upd)})

    refined = LifecycleSystem.resolve_lifecycle(state, update)

    ent_upd = refined.entity_updates[1]
    assert ent_upd.active is False
    assert ent_upd.lifecycle.death_reason_set == "COMBAT"
    assert ent_upd.lifecycle.is_permadeath_set is True

def test_succession_and_heirloom_transfer():
    """Verify that heirlooms are transferred to the heir upon death."""
    # Build parent with heir and heirlooms
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .build())
    parent_life = LifecycleComponent(
        age_ticks=100, max_age_ticks=100, 
        heir_entity_id=2, 
        heirlooms=["Excalibur"]
    )
    parent = replace(parent, lifecycle=parent_life)
    
    heir = (V2EntityBuilder(2)
            .location(1.0, 1.0)
            .build())
    
    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: heir})
    
    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)
    
    # Heir should receive the item via transaction
    heir_upd = refined.entity_updates[2]
    assert len(heir_upd.resource_transfers) > 0
    transfer = heir_upd.resource_transfers[0]
    assert any(stack.item_id == "Excalibur" for stack in transfer.items_add)

    # Logic ID: STRAT-142

    # Logic ID: SOC-042

    # Logic ID: SOC-042

def test_manual_heir_entity_id_transfers_even_if_heir_inactive():
    """The pre-existing manual-heir-transfer liveness check only tests existence, not
    .lifecycle.active -- default-heir selection's stricter filter must not have tightened
    this pre-existing behavior."""
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .build())
    parent_life = LifecycleComponent(
        age_ticks=100, max_age_ticks=100,
        heir_entity_id=2,
        heirlooms=["Excalibur"]
    )
    parent = replace(parent, lifecycle=parent_life)

    heir = (V2EntityBuilder(2)
            .location(1.0, 1.0)
            .lifecycle(active=False)
            .build())

    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: heir})

    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    heir_upd = refined.entity_updates[2]
    assert len(heir_upd.resource_transfers) > 0
    transfer = heir_upd.resource_transfers[0]
    assert any(stack.item_id == "Excalibur" for stack in transfer.items_add)

def test_default_heir_selected_from_strongest_bond():
    """When heir_entity_id is None, a default heir is selected from the deceased's live bonds."""
    bond = SocialBond(target_id=2, familiarity=0.8, sentiment=0.5, last_interaction_tick=10)
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .social(bonds={2: bond})
              .build())
    parent_life = LifecycleComponent(
        age_ticks=100, max_age_ticks=100,
        heir_entity_id=None,
        heirlooms=["Excalibur"]
    )
    parent = replace(parent, lifecycle=parent_life)

    heir = (V2EntityBuilder(2)
            .location(1.0, 1.0)
            .build())

    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: heir})

    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    assert refined.entity_updates[1].lifecycle.heir_entity_id_set == 2

    heir_upd = refined.entity_updates[2]
    assert len(heir_upd.resource_transfers) > 0
    transfer = heir_upd.resource_transfers[0]
    assert any(stack.item_id == "Excalibur" for stack in transfer.items_add)

def test_default_heir_prefers_strongest_bond_among_multiple_candidates():
    """The higher-scoring candidate (familiarity=0.9,sentiment=0.0 -> 0.74) is selected over
    a lower-scoring one (familiarity=0.2,sentiment=1.0 -> 0.52)."""
    bond_a = SocialBond(target_id=2, familiarity=0.9, sentiment=0.0, last_interaction_tick=10)
    bond_b = SocialBond(target_id=3, familiarity=0.2, sentiment=1.0, last_interaction_tick=10)
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .social(bonds={2: bond_a, 3: bond_b})
              .build())
    parent_life = LifecycleComponent(age_ticks=100, max_age_ticks=100, heir_entity_id=None)
    parent = replace(parent, lifecycle=parent_life)

    candidate_a = (V2EntityBuilder(2).location(1.0, 1.0).build())
    candidate_b = (V2EntityBuilder(3).location(2.0, 2.0).build())

    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: candidate_a, 3: candidate_b})

    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    assert refined.entity_updates[1].lifecycle.heir_entity_id_set == 2

def test_default_heir_zero_bonds_no_heir_assigned():
    """Zero bonds -> no heir assigned, no exception raised."""
    parent = (V2EntityBuilder(1).location(0.0, 0.0).build())
    parent_life = LifecycleComponent(age_ticks=100, max_age_ticks=100, heir_entity_id=None)
    parent = replace(parent, lifecycle=parent_life)

    state = AuthoritativeState(tick=100, seed=42, entities={1: parent})

    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    assert refined.entity_updates[1].lifecycle.heir_entity_id_set is None
    for ent_upd in refined.entity_updates.values():
        assert len(ent_upd.resource_transfers) == 0

def test_default_heir_all_bonded_targets_dead_or_missing_no_heir_assigned():
    """Every bonded target is either present-but-inactive or absent entirely -> no heir assigned."""
    bond_dead = SocialBond(target_id=2, familiarity=0.9, sentiment=0.9, last_interaction_tick=10)
    bond_missing = SocialBond(target_id=3, familiarity=0.9, sentiment=0.9, last_interaction_tick=10)
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .social(bonds={2: bond_dead, 3: bond_missing})
              .build())
    parent_life = LifecycleComponent(age_ticks=100, max_age_ticks=100, heir_entity_id=None)
    parent = replace(parent, lifecycle=parent_life)

    dead_candidate = (V2EntityBuilder(2)
                       .location(1.0, 1.0)
                       .lifecycle(active=False)
                       .build())

    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: dead_candidate})

    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    assert refined.entity_updates[1].lifecycle.heir_entity_id_set is None

def test_default_heir_selection_deterministic_across_repeated_calls():
    """Reversed bond-dict insertion order must not change the selected heir."""
    bond_a = SocialBond(target_id=2, familiarity=0.9, sentiment=0.0, last_interaction_tick=10)
    bond_b = SocialBond(target_id=3, familiarity=0.2, sentiment=1.0, last_interaction_tick=10)

    def build_and_run(bonds):
        parent = (V2EntityBuilder(1)
                  .location(0.0, 0.0)
                  .social(bonds=bonds)
                  .build())
        parent_life = LifecycleComponent(age_ticks=100, max_age_ticks=100, heir_entity_id=None)
        parent = replace(parent, lifecycle=parent_life)
        candidate_a = (V2EntityBuilder(2).location(1.0, 1.0).build())
        candidate_b = (V2EntityBuilder(3).location(2.0, 2.0).build())
        state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: candidate_a, 3: candidate_b})
        refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())
        return refined.entity_updates[1].lifecycle.heir_entity_id_set

    heir_forward = build_and_run({2: bond_a, 3: bond_b})
    heir_reversed = build_and_run({3: bond_b, 2: bond_a})

    assert heir_forward == heir_reversed == 2

def test_default_heir_tie_break_deterministic():
    """Score ties break on highest last_interaction_tick, then lowest target_id."""
    bond_older = SocialBond(target_id=2, familiarity=0.5, sentiment=0.5, last_interaction_tick=5)
    bond_newer = SocialBond(target_id=3, familiarity=0.5, sentiment=0.5, last_interaction_tick=50)
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .social(bonds={2: bond_older, 3: bond_newer})
              .build())
    parent_life = LifecycleComponent(age_ticks=100, max_age_ticks=100, heir_entity_id=None)
    parent = replace(parent, lifecycle=parent_life)
    candidate_a = (V2EntityBuilder(2).location(1.0, 1.0).build())
    candidate_b = (V2EntityBuilder(3).location(2.0, 2.0).build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: candidate_a, 3: candidate_b})
    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())
    assert refined.entity_updates[1].lifecycle.heir_entity_id_set == 3

    bond_low_id = SocialBond(target_id=2, familiarity=0.5, sentiment=0.5, last_interaction_tick=10)
    bond_high_id = SocialBond(target_id=3, familiarity=0.5, sentiment=0.5, last_interaction_tick=10)
    parent2 = (V2EntityBuilder(4)
               .location(0.0, 0.0)
               .social(bonds={2: bond_low_id, 3: bond_high_id})
               .build())
    parent2_life = LifecycleComponent(age_ticks=100, max_age_ticks=100, heir_entity_id=None)
    parent2 = replace(parent2, lifecycle=parent2_life)
    state2 = AuthoritativeState(tick=100, seed=42, entities={4: parent2, 2: candidate_a, 3: candidate_b})
    refined2 = LifecycleSystem.resolve_lifecycle(state2, StateUpdate())
    assert refined2.entity_updates[4].lifecycle.heir_entity_id_set == 2

def test_default_heir_does_not_override_manual_heir_entity_id():
    """A manually-set heir_entity_id must win even when a higher-scoring bonded candidate exists."""
    bond_high = SocialBond(target_id=3, familiarity=1.0, sentiment=1.0, last_interaction_tick=999)
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .social(bonds={3: bond_high})
              .build())
    parent_life = LifecycleComponent(
        age_ticks=100, max_age_ticks=100,
        heir_entity_id=2,
        heirlooms=["Excalibur"]
    )
    parent = replace(parent, lifecycle=parent_life)

    heir = (V2EntityBuilder(2).location(1.0, 1.0).build())
    other_candidate = (V2EntityBuilder(3).location(2.0, 2.0).build())

    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: heir, 3: other_candidate})

    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    heir_upd = refined.entity_updates[2]
    assert len(heir_upd.resource_transfers) > 0
    transfer = heir_upd.resource_transfers[0]
    assert any(stack.item_id == "Excalibur" for stack in transfer.items_add)

    assert 3 not in refined.entity_updates or len(refined.entity_updates[3].resource_transfers) == 0

    life_upd = refined.entity_updates[1].lifecycle
    assert life_upd.heir_entity_id_set in (None, 2)

def test_near_death_hardening_logic():
    """Directly test the hardening logic in the pipeline."""
    from src.engine.pipeline import AuthoritativeApplyPipeline
    
    hero = (V2EntityBuilder(1)
            .kind("HERO")
            .location(0.0, 0.0)
            .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
            .combat(hp=100, max_hp=100)
            .build())
            
    attacker = (V2EntityBuilder(2)
                .kind("MONSTER")
                .location(1.0, 0.0)
                .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
                .combat(atk=105)
                .combat(readiness=100.0)
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
