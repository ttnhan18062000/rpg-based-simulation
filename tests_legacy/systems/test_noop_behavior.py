import pytest
from src_legacy.core.state import AuthoritativeState
from src_legacy.core.updates import StateUpdate
from src_legacy.engine.apply import ApplyPath

def test_empty_world_tick():
    """
    Z16: Empty world tick does not crash.
    Z16: Empty world tick advances passive time.
    """
    state = AuthoritativeState(tick=1, seed=42)
    update = StateUpdate()
    
    # Apply no-op update
    new_state = ApplyPath.apply_generation(state, update, next_tick=2, next_world_time=1)
    
    # 1. State advanced correctly
    assert new_state.tick == 2
    assert new_state.world_time == 1
    
    # 2. No entities or structures were unexpectedly created
    assert len(new_state.entities) == 0
    assert len(new_state.regions) == 0
    
def test_noop_update_preserves_hash():
    """
    Z16: No-op update preserves state hash except allowed time/metadata changes.
    """
    # Setup state with some data to ensure deep dict hashes are consistent
    from src_legacy.world.generation import WorldGenerator
    state = WorldGenerator.generate_world(seed=42, num_entities=5)
    
    # Force hazards to 0 so no passive damage occurs
    from dataclasses import replace
    for r_id, region in state.regions.items():
        state.regions[r_id] = replace(region, hazard_level=0.0)
        
    update = StateUpdate()
    
    # Get fingerprint before
    fingerprint_before = state.fingerprint()
    
    # Apply no-op update
    new_state = ApplyPath.apply_generation(state, update, next_tick=state.tick + 1)
    
    # Get fingerprint after
    fingerprint_after = new_state.fingerprint()
    
    # Print raw_data from both to see the diff
    def get_raw(st):
        entity_parts = []
        for eid in sorted(st.entities.keys()):
            ent = st.entities[eid]
            entity_parts.append(
                f"{eid}:{ent.kind}:{ent.position}:{ent.combat.hp}:"
                f"{ent.inventory.gold}:{ent.strategic.current_project_id}:"
                f"{len(ent.strategic.projects)}:{len(ent.identity.learned_skills)}"
            )
        entity_ident = "|".join(entity_parts)
        resource_ident = "|".join(f"{k}:{v}" for k, v in sorted(st.global_resources.items()))
        region_parts = []
        for rid in sorted(st.regions.keys()):
            r = st.regions[rid]
            region_parts.append(f"{rid}:{r.owner_faction_id}:{r.influence}:{r.hazard_level}")
        region_ident = "|".join(region_parts)
        scar_ident = "|".join(f"{sid}:{s.severity}" for sid, s in sorted(st.local_scars.items()))
        macro_ident = f"{st.maturity}:{st.last_calamity_tick}:{st.movement_count}"
        return f"{st.seed}|{entity_ident}|{resource_ident}|{region_ident}|{scar_ident}|{macro_ident}"
        
    print(f"\nBefore: {get_raw(state)}")
    print(f"After: {get_raw(new_state)}")
    
    # We expect tick to differ, but the underlying state hash to be identical
    assert fingerprint_before["state_hash"] == fingerprint_after["state_hash"]
