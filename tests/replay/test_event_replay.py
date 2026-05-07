import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, ResourceNodeState, ItemStack, InventoryComponent
from src.core.enums import EntityRole, Faction
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent

def create_mock_entity(id, faction=Faction.HERO_GUILD, role=EntityRole.HERO, pos=(0,0), hp=100):
    return (V2EntityBuilder(id)
        .kind("hero")
        .location(pos[0], pos[1])
        .identity(faction=faction, role=role)
        .combat(hp=hp, max_hp=100, atk=10, attack_range=1, alive=hp > 0, readiness=100.0)
        .inventory(max_slots=10, max_weight=100.0)
        .lifecycle(active=True)
        .build())

def test_event_replay_fidelity():
    """
    Law: Replaying the same inputs must produce the same sequence of fine-grained events.
    Proof: This test runs a scenario, captures the event log, and then re-runs it ensuring identity.
    """
    # 1. Setup Initial State
    e1 = create_mock_entity(1, pos=(1,1))
    node = ResourceNodeState(id=10, kind="iron_ore", position=(1,1), remaining_charges=1, max_charges=1, yields_item="iron_ore", required_ticks=1)
    state = AuthoritativeState(tick=1, seed=42, entities={1: e1}, resource_nodes={10: node})
    
    # 2. Run Tick 1: Harvest Node (Success)
    intent = ResourceTransferIntent(source_id=10, source_kind="NODE", items_add=[ItemStack("iron_ore", 1)], transfer_kind="HARVEST")
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[intent])})
    
    refined1 = AuthoritativeApplyPipeline.refine(state, update)
    log1 = list(refined1.transaction_trace)
    
    # 3. Run Tick 2: Try to harvest again (Failure - Depleted)
    # Note: refined1 results in a state where node is depleted
    from src.engine.apply import ApplyPath
    next_state = ApplyPath.apply_generation(state, refined1, next_tick=2)
    
    refined2 = AuthoritativeApplyPipeline.refine(next_state, update)
    log2 = list(refined2.transaction_trace)
    
    full_log_original = log1 + log2
    
    # 4. REPLAY: Re-run from initial state
    refined_replay1 = AuthoritativeApplyPipeline.refine(state, update)
    log_replay1 = list(refined_replay1.transaction_trace)
    
    next_state_replay = ApplyPath.apply_generation(state, refined_replay1, next_tick=2)
    refined_replay2 = AuthoritativeApplyPipeline.refine(next_state_replay, update)
    log_replay2 = list(refined_replay2.transaction_trace)
    
    full_log_replay = log_replay1 + log_replay2
    
    # 5. Assert Fidelity
    assert full_log_original == full_log_replay
    assert any("TRANS_ACCEPT" in event for event in log1)
    assert any("TRANS_FAIL" in event for event in log2)
