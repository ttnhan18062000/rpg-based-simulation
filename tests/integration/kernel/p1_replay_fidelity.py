"""
P1 Semantic Hardening: Event-Level Replay Fidelity.
- RPG-0073: deterministic_replay_delta
- RPG-1431: Strategic state appears in replay/fingerprint
- RPG-0081: test_arena_structural_determinism
- RPG-0094: test_resource_isolation_bounded_growth
"""
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, ResourceNodeState, ItemStack, InventoryComponent, StrategicComponent, TaskComponent, IntentResult
from src.core.enums import EntityRole
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent, StrategicUpdate
from src.core.strategic import ProjectState, ProjectStatus, LeadState, LeadCertainty

def create_mock_entity(id, pos=(0,0)):
    return EntityState(
        id=id,
        kind="ACTOR",
        position=pos,
        identity=IdentityComponent(faction="HERO_FACTION", role=EntityRole.HERO),
        combat=CombatComponent(hp=100, max_hp=100, atk=10, range=1, alive=True),
        readiness=100.0,
        active=True,
        inventory=InventoryComponent(max_slots=10, max_weight=100.0),
        strategic=StrategicComponent(),
        task=TaskComponent()
    )

def test_event_level_replay_fidelity():
    """
    Law: Replaying identical seeds/inputs must produce identical event sequences.
    Verifies that StrategicUpdates and IntentResults are deterministic.
    """
    # 1. Setup
    e1 = create_mock_entity(1, pos=(0,0))
    node = ResourceNodeState(id=10, kind="iron_ore", position=(0,0), remaining_charges=1, max_charges=1, yields_item="iron_ore", required_ticks=1)
    state = AuthoritativeState(tick=1, seed=42, entities={1: e1}, resource_nodes={10: node})
    
    # Lead for detour
    town_lead = LeadState(id="town", kind="location", subject="town", detail="(10,10)", certainty=LeadCertainty.PRECISE)
    # Active project
    p_harvest = ProjectState(id="p_harvest", kind="quest", status=ProjectStatus.ACTIVE)
    state.entities[1] = replace(state.entities[1], strategic=replace(state.entities[1].strategic, 
        leads={"town": town_lead},
        projects={"p_harvest": p_harvest},
        current_project_id="p_harvest"
    ))
    
    # 2. TICK 1: Successful Harvest
    intent1 = ResourceTransferIntent(source_id=10, source_kind="NODE", items_add=[ItemStack("iron_ore", 1)], transfer_kind="HARVEST")
    # Fill inventory to trigger blocker next tick
    state.entities[1] = replace(state.entities[1], inventory=replace(state.entities[1].inventory, items=[ItemStack("junk", 1)]*9))
    
    upd1 = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[intent1])})
    
    # Run once
    refined1 = AuthoritativeApplyPipeline.refine(state, upd1)
    state_v2 = ApplyPath.apply_generation(state, refined1, next_tick=2)
    
    # Record event sequence
    trace1 = list(refined1.transaction_trace)
    intent_res1 = state_v2.entities[1].latest_intent_results
    
    # 3. TICK 2: Failed Harvest (Full Inventory) -> Detour Trigger
    # Manually inject failure into state_v2 to simulate what AI sees after Tick 2 failure
    failure = IntentResult(transaction_id="t2", accepted=False, reason="INVENTORY_FULL", source_kind="NODE", source_id=10)
    state_v2.entities[1] = replace(state_v2.entities[1], latest_intent_results=[failure])
    
    # First, we need to infer the blocker from the failure in state_v2
    from src.systems.strategic import StrategicIntelligenceSystem
    upd_blocker = StrategicIntelligenceSystem.infer_blockers(state_v2.entities[1], "ENTITY_ACT", {"action": "INTERACT", "target_id": 10})
    state_v2.entities[1] = replace(state_v2.entities[1], strategic=replace(state_v2.entities[1].strategic, blockers={b.id: b for b in upd_blocker.blockers_add_or_update}))
    
    # Now simulate AI decision
    upd2 = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[intent1])})
    strat_upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state_v2, state_v2.entities[1])
    
    # Apply Tick 2
    refined2 = AuthoritativeApplyPipeline.refine(state_v2, upd2)
    # Merge strategic update into refined2
    refined2 = replace(refined2, entity_updates={1: replace(refined2.entity_updates[1], strategic=strat_upd)})
    
    state_v3 = ApplyPath.apply_generation(state_v2, refined2, next_tick=3)
    
    trace2 = list(refined2.transaction_trace)
    intent_res2 = state_v3.entities[1].latest_intent_results
    strat_state2 = state_v3.entities[1].strategic
    
    # 4. REPLAY
    # Re-run Tick 1
    refined1_r = AuthoritativeApplyPipeline.refine(state, upd1)
    state_v2_r = ApplyPath.apply_generation(state, refined1_r, next_tick=2)
    
    assert list(refined1_r.transaction_trace) == trace1
    assert state_v2_r.entities[1].latest_intent_results == intent_res1
    
    # Re-run Tick 2
    failure_r = IntentResult(transaction_id="t2", accepted=False, reason="INVENTORY_FULL", source_kind="NODE", source_id=10)
    state_v2_r.entities[1] = replace(state_v2_r.entities[1], latest_intent_results=[failure_r])
    
    upd_blocker_r = StrategicIntelligenceSystem.infer_blockers(state_v2_r.entities[1], "ENTITY_ACT", {"action": "INTERACT", "target_id": 10})
    state_v2_r.entities[1] = replace(state_v2_r.entities[1], strategic=replace(state_v2_r.entities[1].strategic, blockers={b.id: b for b in upd_blocker_r.blockers_add_or_update}))
    
    upd2_r = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[intent1])})
    
    strat_upd_r = StrategicIntelligenceSystem.evaluate_strategic_intent(state_v2_r, state_v2_r.entities[1])
    refined2_r = AuthoritativeApplyPipeline.refine(state_v2_r, upd2_r)
    refined2_r = replace(refined2_r, entity_updates={1: replace(refined2_r.entity_updates[1], strategic=strat_upd_r)})
    
    state_v3_r = ApplyPath.apply_generation(state_v2_r, refined2_r, next_tick=3)
    
    assert list(refined2_r.transaction_trace) == trace2
    assert state_v3_r.entities[1].latest_intent_results == intent_res2
    assert state_v3_r.entities[1].strategic == strat_state2
    
    # Final check: Detour project should be present in both
    detour = next((p for p in state_v3_r.entities[1].strategic.projects.values() if p.kind == "detour"), None)
    assert detour is not None
    assert state_v3_r.entities[1].strategic.current_project_id == detour.id
