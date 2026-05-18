import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, BiologicalComponent
from src_legacy.core.serialization import StateDeserializer
from src_legacy.engine.checkpoint import CanonicalStateHasher

def test_state_serialization_roundtrip():
    """
    Law: Serialized state must be perfectly restorable.
    """
    e1 = EntityState(
        id=1, kind="HERO", position=(10.5, 20.2), 
        biological=BiologicalComponent(hunger=50.0, sleep_debt=10.0)
    )
    state = AuthoritativeState(
        tick=100, seed=42, 
        entities={1: e1},
        global_resources={"gold_pool": 1000.0}
    )
    
    # 1. Convert to dict (via CanonicalStateHasher)
    data = CanonicalStateHasher.to_canonical_data(state)
    
    # 2. Convert back to state (via StateDeserializer)
    restored_state = StateDeserializer.deserialize_state(data)
    
    # 3. Verify parity
    assert restored_state.tick == state.tick
    assert restored_state.seed == state.seed
    assert restored_state.entities[1].id == state.entities[1].id
    assert restored_state.entities[1].position == state.entities[1].position
    assert restored_state.entities[1].biological.hunger == state.entities[1].biological.hunger
    assert restored_state.global_resources["gold_pool"] == state.global_resources["gold_pool"]
    
    # 4. Verify hash parity
    hash_orig = CanonicalStateHasher.get_hash(state)
    hash_restored = CanonicalStateHasher.get_hash(restored_state)
    assert hash_orig == hash_restored

def test_update_serialization_roundtrip():
    """
    Law: Trace events containing updates must be restorable.
    """
    from src_legacy.core.updates import StateUpdate, EntityUpdate, AttributeUpdate
    
    upd = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, attributes=AttributeUpdate(strength_delta=5))
        },
        maturity_set=2
    )
    
    # Simple asdict for updates (since they don't have a canonical format yet)
    from dataclasses import asdict
    data = asdict(upd)
    
    # Manually clean data to simulate JSON (convert int keys to str)
    json_data = {
        "entity_updates": {"1": data["entity_updates"][1]},
        "maturity_set": 2
    }
    
    restored_upd = StateDeserializer.deserialize_update(json_data)
    
    assert restored_upd.maturity_set == 2
    assert 1 in restored_upd.entity_updates
    assert restored_upd.entity_updates[1].attributes.strength_delta == 5
