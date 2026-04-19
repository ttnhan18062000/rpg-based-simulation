import pytest
from src_v2.core.state import AuthoritativeState, EntityState
from src_v2.engine.checkpoint import CanonicalStateHasher

def test_hash_construction_order_invariance():
    """Verify that the hash is identical regardless of how the dictionaries were built."""
    # Case A: Build entities 1 then 2
    state_a = AuthoritativeState(tick=1, seed=1, entities={
        1: EntityState(id=1, kind="target", position=(0.0, 0.0)),
        2: EntityState(id=2, kind="target", position=(1.0, 1.0))
    })
    
    # Case B: Build entities 2 then 1 (dictionaries might have different internal order)
    entities_b = {}
    entities_b[2] = EntityState(id=2, kind="target", position=(1.0, 1.0))
    entities_b[1] = EntityState(id=1, kind="target", position=(0.0, 0.0))
    state_b = AuthoritativeState(tick=1, seed=1, entities=entities_b)
    
    hash_a = CanonicalStateHasher.get_hash(state_a)
    hash_b = CanonicalStateHasher.get_hash(state_b)
    
    assert hash_a == hash_b
    assert hash_a != ""

def test_hash_compact_vs_pretty():
    """Verify that pretty printing for debug doesn't change the authoritative hash."""
    state = AuthoritativeState(tick=1, seed=1, entities={
        1: EntityState(id=1, kind="target", position=(0.0, 0.0))
    })
    
    compact_json = CanonicalStateHasher.to_canonical_json(state, pretty=False)
    pretty_json = CanonicalStateHasher.to_canonical_json(state, pretty=True)
    
    assert compact_json != pretty_json
    assert "  " in pretty_json
    assert "\n" in pretty_json
    
    # Authoritative hash must come from compact version
    import hashlib
    manual_hash = hashlib.sha256(compact_json.encode("utf-8")).hexdigest()
    assert CanonicalStateHasher.get_hash(state) == manual_hash

def test_property_sorting_in_hash():
    """Verify that entity properties are sorted before hashing."""
    state_a = AuthoritativeState(tick=1, seed=1, entities={
        1: EntityState(id=1, kind="a", position=(0,0), properties={"z": 1, "a": 2})
    })
    state_b = AuthoritativeState(tick=1, seed=1, entities={
        1: EntityState(id=1, kind="a", position=(0,0), properties={"a": 2, "z": 1})
    })
    
    assert CanonicalStateHasher.get_hash(state_a) == CanonicalStateHasher.get_hash(state_b)
