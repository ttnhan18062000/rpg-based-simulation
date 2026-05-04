import pytest
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, NavigationComponent, TaskComponent, GroupRecord, AuthoritativeState
from src.core.updates import StateUpdate, EntityUpdate, NavigationUpdate
from src.core.movement_modes import MovementMode
from dataclasses import replace
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath

def create_mock_state():
    return AuthoritativeState(
        tick=1,
        seed=42,
        entities={},
        resource_nodes={},
        ground_items={},
        corpses={},
        buildings={},
        regions={},
        groups={},
        terrain={}
    )

def create_mock_entity(id, pos, faction=0, role=0):
    from src.core.builder import V2EntityBuilder
    from src.core.enums import Faction, EntityRole
    return (V2EntityBuilder(id)
        .kind("hero")
        .at(pos)
        .with_identity(faction=Faction.HERO_GUILD if faction == 0 else Faction.MONSTER_HORDE, 
                       role=EntityRole.HERO if role == 0 else EntityRole.MONSTER)
        .with_combat(hp=100, max_hp=100, atk=10, def_stat=5, alive=True)
        .with_navigation()
        .readiness(100.0)
        .build()
    )

def test_opportunity_attack_on_egress():
    state = create_mock_state()
    # Entity 1 at (5, 5), Hostile at (5, 6)
    e1 = create_mock_entity(1, (5.0, 5.0), faction=0)
    e2 = create_mock_entity(2, (5.0, 6.0), faction=1)
    state.entities[1] = e1
    state.entities[2] = e2
    
    # E1 proposes to move to (4, 5) - leaving engagement
    raw_update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(4.0, 5.0), movement_mode_set=MovementMode.PURSUE))
        }
    )
    
    # Resolve
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Check if E1 took damage from OA
    upd1 = refined.entity_updates.get(1)
    assert upd1 is not None
    assert upd1.combat is not None
    assert upd1.combat.is_opportunity_attack is True
    assert upd1.combat.damage_taken > 0

def test_hold_mode_refuses_to_yield():
    state = create_mock_state()
    # E1 at (5, 5) with HOLD mode
    e1 = create_mock_entity(1, (5.0, 5.0), faction=0)
    e1 = ApplyPath._apply_entity_update(e1, EntityUpdate(entity_id=1, navigation=NavigationUpdate(movement_mode_set=MovementMode.HOLD)))
    
    # E2 at (5, 4) wants to move to (5, 5)
    e2 = create_mock_entity(2, (5.0, 4.0), faction=0)
    # Block sidestep tiles (4, 4) and (6, 4)
    e3 = create_mock_entity(3, (4.0, 4.0), faction=0)
    e4 = create_mock_entity(4, (6.0, 4.0), faction=0)
    
    state.entities[1] = e1
    state.entities[2] = e2
    state.entities[3] = e3
    state.entities[4] = e4
    
    # E2 has higher priority (id 2 vs 1)
    # HERO role gets 100 base.
    
    raw_update = StateUpdate(
        entity_updates={
            2: EntityUpdate(entity_id=2, navigation=NavigationUpdate(target_set=(5.0, 5.0), movement_mode_set=MovementMode.PURSUE))
        }
    )
    
    # Resolve
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Check if E2 failed to move because E1 refused to yield
    upd2 = refined.entity_updates.get(2)
    assert upd2.new_position is None or upd2.new_position == (5.0, 4.0)
    from src.core.enums import ReasonCode
    assert upd2.navigation.failure_reason == ReasonCode.OCCUPANCY_VIOLATION

def test_sidestepping_on_blocked_move():
    state = create_mock_state()
    # E1 at (5, 5), E2 at (6, 5) blocking horizontal move
    e1 = create_mock_entity(1, (5.0, 5.0), faction=0)
    e2 = create_mock_entity(2, (6.0, 5.0), faction=0) # Ally
    state.entities[1] = e1
    state.entities[2] = e2
    
    # E1 wants to move to (6, 5)
    raw_update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(6.0, 5.0), movement_mode_set=MovementMode.PURSUE))
        }
    )
    
    # Resolve
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # E1 should sidestep to (5, 4) or (5, 6)
    upd1 = refined.entity_updates.get(1)
    assert upd1.new_position in [(5.0, 4.0), (5.0, 6.0)]

def test_evasive_retreat_skips_oa():
    state = create_mock_state()
    # E1 at (5, 5), Hostile at (5, 6)
    # E1 is EVASIVE
    e1 = create_mock_entity(1, (5.0, 5.0), faction=0)
    e1 = replace(e1, combat=replace(e1.combat, action_style=2)) # ActionStyle.EVASIVE
    
    e2 = create_mock_entity(2, (5.0, 6.0), faction=1)
    state.entities[1] = e1
    state.entities[2] = e2
    
    # E1 proposes to move to (4, 5) with RETREAT mode
    raw_update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(4.0, 5.0), movement_mode_set=MovementMode.RETREAT))
        }
    )
    
    # Resolve
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Check if E1 skipped OA
    upd1 = refined.entity_updates.get(1)
    assert upd1.combat is None or not upd1.combat.is_opportunity_attack

def test_regroup_movement():
    state = create_mock_state()
    # E1 at (10, 10), Group Anchor at (0, 0), Cohesion 5
    e1 = create_mock_entity(1, (10.0, 10.0))
    e1 = replace(e1, identity=replace(e1.identity, group_id=1))
    
    group = GroupRecord(
        id=1,
        leader_id=1,
        member_ids={1},
        anchor=(0.0, 0.0),
        cohesion_radius=5.0
    )
    state.groups[1] = group
    state.entities[1] = e1
    
    # TacticalDecisionSystem should trigger REGROUP
    from src.engine.tactical import TacticalDecisionSystem
    ent_upd = TacticalDecisionSystem.evaluate_entity_intent(state, e1)
    
    assert ent_upd.navigation.movement_mode_set == MovementMode.REGROUP
    assert ent_upd.navigation.target_set == (0.0, 0.0)
