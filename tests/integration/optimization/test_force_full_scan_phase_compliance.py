import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, ResourceNodeState, BuildingState, ItemStack, GroupRecord
from src.core.updates import StateUpdate, EntityUpdate, NavigationUpdate, InteractionUpdate, StrategicUpdate
from src.core.dirty import DirtySet
from src.core.builder import V2EntityBuilder
from src.core.strategic import (
    LeadState, ConcernState, ConcernKind, ProjectState, ObjectiveState, 
    ProjectKind, ObjectiveKind, ProjectStatus, ObjectiveStatus, BlockerState, BlockerKind,
    LeadCertainty
)
from src.engine.pipeline_phases.interactions import InteractionPhase
from src.engine.pipeline_phases.movement import MovementPhase
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
from src.engine.shop import ShopSystem
from src.engine.pipeline_phases.capacity_enforcement import CapacityEnforcementPhase
from src.engine.pipeline_phases.groups import GroupPhase
from src.systems.lifecycle import LifecycleSystem
from src.engine.cadence import SystemCadence


def test_interaction_phase_force_full_scan_processes_entity_with_empty_dirty_set():
    """
    Given:
        entity has navigation.target pointing to a resource node
        update.force_full_scan=True
        update.dirty_set is empty

    Expect:
        InteractionPhase still evaluates the entity.
    """
    state = AuthoritativeState(tick=1, seed=42)
    entity = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .navigation(target=(5.0, 5.0))
              .lifecycle(active=True)
              .combat(alive=True)
              .build())
    state = replace(state, entities={1: entity})
    
    node = ResourceNodeState(id=10, position=(5.0, 5.0), kind="WOOD", yields_item="wood_log", remaining_charges=10, max_charges=10, required_ticks=5)
    state = replace(state, resource_nodes={10: node})
    
    update = StateUpdate(force_full_scan=True, dirty_set=DirtySet(), entity_updates={})
    
    refined = InteractionPhase.route_interaction_intent(state, update)
    
    assert 1 in refined.entity_updates
    assert refined.entity_updates[1].interaction is not None
    assert refined.entity_updates[1].interaction.target_node_id == 10


def test_movement_phase_force_full_scan_processes_entity_with_target_and_empty_dirty_set():
    """
    Given:
        entity has navigation.target and different position
        update.force_full_scan=True
        dirty_set empty

    Expect:
        MovementPhase creates movement update.
    """
    state = AuthoritativeState(tick=1, seed=42)
    entity = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .navigation(target=(10.0, 0.0))
              .lifecycle(active=True)
              .combat(alive=True, readiness=100.0)
              .build())
    state = replace(state, entities={1: entity})
    
    update = StateUpdate(force_full_scan=True, dirty_set=DirtySet(), entity_updates={})
    
    refined = MovementPhase.resolve_position_swaps(state, update)
    refined = MovementPhase.route_movement_intent(state, refined)
    
    assert 1 in refined.entity_updates
    assert refined.entity_updates[1].new_position is not None
    assert refined.entity_updates[1].new_position != (0.0, 0.0)


def test_strategic_phase_force_full_scan_processes_active_project_entity_with_empty_dirty_set():
    """
    Given:
        entity has active strategic project with material blocker
        update.force_full_scan=True
        dirty_set empty

    Expect:
        strategic phase evaluates the entity.
    """
    state = AuthoritativeState(tick=1, seed=42)
    
    # Material blocker for 'iron_ore' and a location lead at '50.0,50.0'
    blocker = BlockerState(id="b1", kind=BlockerKind.MATERIAL, subject="iron_ore")
    lead = LeadState(id="l1", kind="location", subject="iron_ore", detail="50.0,50.0")
    
    entity = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .lifecycle(active=True)
              .combat(alive=True)
              .strategic(blockers={"b1": blocker}, leads={"l1": lead})
              .build())
    state = replace(state, entities={1: entity})
    
    # We pass a cadence where strategic_intelligence runs on tick 1 for entity 1 ((1+1)%1 == 0)
    cadence = SystemCadence(strategic_intelligence=1, concern_evaluation=1)
    update = StateUpdate(force_full_scan=True, dirty_set=DirtySet(), entity_updates={})
    
    refined = StrategicIntelligenceSystem.fused_strategic_pass(state, update, cadence)
    
    assert 1 in refined.entity_updates
    assert refined.entity_updates[1].navigation is not None
    assert refined.entity_updates[1].navigation.target_set == (50.0, 50.0)


def test_shop_phase_force_full_scan_processes_inventory_entity_with_empty_dirty_set():
    """
    Given:
        entity at shop building tile with sellable items in inventory
        update.force_full_scan=True
        dirty_set empty

    Expect:
        ShopSystem creates auto-sell resource transfer intent.
    """
    state = AuthoritativeState(tick=1, seed=42)
    entity = (V2EntityBuilder(1)
              .location(1.0, 1.0)
              .navigation(position=(1.0, 1.0))
              .lifecycle(active=True)
              .combat(alive=True)
              .inventory(items=[ItemStack("wood", 10)])
              .build())
    state = replace(state, entities={1: entity})
    
    building = BuildingState(id=100, kind="shop", position=(1, 1), functional=True)
    state = replace(state, building_tiles={(1, 1): "shop"}, buildings={100: building})
    
    update = StateUpdate(force_full_scan=True, dirty_set=DirtySet(), entity_updates={})
    
    refined = ShopSystem.enforce(state, update)
    
    assert 1 in refined.entity_updates
    assert len(refined.entity_updates[1].resource_transfers) > 0
    assert refined.entity_updates[1].resource_transfers[0].source_kind == "SHOP_SELL"


def test_capacity_phase_force_full_scan_processes_all_inventory_entities():
    """
    Given:
        entity with strategic leads exceeding profile.max_leads
        dirty_set empty
        force_full_scan=True

    Expect:
        CapacityEnforcementPhase trims excess leads.
    """
    state = AuthoritativeState(tick=1, seed=42)
    
    # Create 10 leads (CognitionProfile default max_leads is 8)
    leads = {f"l{i}": LeadState(id=f"l{i}", kind="location", subject="iron_ore", certainty=LeadCertainty.VAGUE) for i in range(10)}
    
    entity = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .lifecycle(active=True)
              .combat(alive=True)
              .strategic(leads=leads)
              .build())
    state = replace(state, entities={1: entity})
    
    # Propose a strategic update (CapacityEnforcement runs on proposed strategic updates)
    strat_up = StrategicUpdate(leads_add_or_update=[LeadState(id="l_new", kind="location", subject="gold")])
    update = StateUpdate(
        force_full_scan=True, 
        dirty_set=DirtySet(), 
        entity_updates={1: EntityUpdate(entity_id=1, strategic=strat_up)}
    )
    
    refined = CapacityEnforcementPhase.enforce(state, update)
    
    assert 1 in refined.entity_updates
    assert refined.entity_updates[1].strategic is not None
    # Verify that capacity trimming scheduled lead removals
    assert len(refined.entity_updates[1].strategic.leads_remove) > 0


def test_group_phase_force_full_scan_processes_ungrouped_entities():
    """
    Given:
        two ungrouped entities close to each other with an active social contract
        dirty_set empty
        force_full_scan=True

    Expect:
        GroupPhase forms a group between them.
    """
    from src.core.strategic import ContractState, ContractKind, ContractStatus
    
    state = AuthoritativeState(tick=1, seed=42)
    contract = ContractState(
        id="c1", kind=ContractKind.RECRUITMENT, source_id=1, target_id=2, status=ContractStatus.ACTIVE
    )
    
    ent1 = (V2EntityBuilder(1)
            .location(0.0, 0.0)
            .lifecycle(active=True)
            .combat(alive=True)
            .strategic(contracts={"c1": contract})
            .build())
            
    ent2 = (V2EntityBuilder(2)
            .location(1.0, 0.0)
            .lifecycle(active=True)
            .combat(alive=True)
            .build())
            
    state = replace(state, entities={1: ent1, 2: ent2})
    update = StateUpdate(force_full_scan=True, dirty_set=DirtySet(), entity_updates={})
    
    refined = GroupPhase.resolve(state, update)
    
    assert len(refined.groups_add_or_update) > 0
    assert 1 in refined.entity_updates
    assert 2 in refined.entity_updates
    assert refined.entity_updates[1].group_id_set is not None


def test_lifecycle_phase_force_full_scan_processes_old_age_entities():
    """
    Given:
        entity reaching max age ticks
        dirty_set empty
        force_full_scan=True

    Expect:
        LifecycleSystem marks entity as permadeath.
    """
    state = AuthoritativeState(tick=1, seed=42)
    ent = (V2EntityBuilder(1)
           .location(0.0, 0.0)
           .lifecycle(active=True, age_ticks=1000, max_age_ticks=1000)
           .combat(alive=True)
           .build())
    state = replace(state, entities={1: ent})
    
    update = StateUpdate(force_full_scan=True, dirty_set=DirtySet(), entity_updates={})
    
    refined = LifecycleSystem.resolve_lifecycle(state, update)
    
    assert 1 in refined.entity_updates
    assert refined.entity_updates[1].active is False
    assert refined.entity_updates[1].lifecycle is not None
    assert refined.entity_updates[1].lifecycle.is_permadeath_set is True
