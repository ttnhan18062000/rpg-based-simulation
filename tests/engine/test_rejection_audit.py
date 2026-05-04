import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, CombatComponent
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate, NavigationUpdate, ResourceTransferIntent
from src.core.enums import ReasonCode, EntityRole, Faction
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.builder import V2EntityBuilder

def test_rejection_audit_aggregation():
    # Setup state with two entities far apart and one incapacitated
    initial_state = AuthoritativeState(tick=100, seed=42)
    
    # Entity 1: Alive but out of range for attack
    e1 = (V2EntityBuilder(1)
          .kind("hero")
          .at((0, 0))
          .readiness(100.0)
          .faction(Faction.HERO_GUILD)
          .with_base_stats(hp=100)
          .build())
    
    # Entity 2: Far away target
    e2 = (V2EntityBuilder(2)
          .kind("monster")
          .at((10, 10))
          .faction(Faction.MONSTER_HORDE)
          .with_base_stats(hp=100)
          .build())
    
    # Entity 3: Dead (incapacitated)
    e3 = (V2EntityBuilder(3)
          .kind("hero")
          .at((5, 5))
          .with_base_stats(hp=0)
          .with_current_hp(0)
          .build())
    
    state = replace(initial_state, entities={1: e1, 2: e2, 3: e3})
    
    # Propose intents that will be rejected:
    # 1. Attack out of range (E1 -> E2)
    # Note: In V2, execute_action performs range check. 
    # But here we are injecting a manual TaskUpdate to the pipeline.
    e1_act_upd = EntityUpdate(
        entity_id=1,
        task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 2})
    )
    
    # 2. Move for E3 which is dead (GLOBAL_PROPOSAL rejection)
    e3_upd = EntityUpdate(
        entity_id=3,
        navigation=NavigationUpdate(target_set=(6, 6))
    )
    
    # 3. Resource rejection (E1 loot non-existent node)
    e1_res_intent = ResourceTransferIntent(
        source_id=999, source_kind="NODE", transfer_kind="HARVEST"
    )
    e1_upd = replace(e1_act_upd, resource_transfers=[e1_res_intent])
    
    raw_update = StateUpdate(entity_updates={1: e1_upd, 3: e3_upd})
    
    # Run pipeline
    refined_update = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Verify rejection events
    events = refined_update.rejection_events
    
    print(f"\nCaptured {len(events)} rejection events.")
    for ev in events:
        print(f"  Tick {ev.tick}: Actor {ev.actor_id} {ev.action_kind} rejected: {ev.reason} (Target: {ev.target_id})")

    # 1. E3 sanitized (GLOBAL_PROPOSAL)
    assert any(ev.actor_id == 3 and ev.action_kind == "GLOBAL_PROPOSAL" for ev in events)
    
    # 2. E1 Attack rejected (Range check in Phase 4 of pipeline/refine)
    # The refined_update will contain a rejection for E1 ATTACK
    assert any(ev.actor_id == 1 and ev.action_kind == "ATTACK" and ev.reason == ReasonCode.OUT_OF_RANGE for ev in events)
    
    # 3. E1 Resource rejected
    assert any(ev.actor_id == 1 and ev.action_kind == "HARVEST" and ev.reason == ReasonCode.TARGET_INVALID for ev in events)

    print(f"\nCaptured {len(events)} rejection events.")
    for ev in events:
        print(f"  Tick {ev.tick}: Actor {ev.actor_id} {ev.action_kind} rejected: {ev.reason} (Target: {ev.target_id})")
