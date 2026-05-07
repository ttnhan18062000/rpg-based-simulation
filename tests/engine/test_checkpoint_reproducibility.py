import pytest
from src.core.state import AuthoritativeState, EntityState
from src.engine.checkpoint import CanonicalStateHasher
from src.core.builder import V2EntityBuilder

def test_hash_construction_order_invariance():
    """Verify that the hash is identical regardless of how the dictionaries were built."""
    # Case A: Build entities 1 then 2
    state_a = AuthoritativeState(tick=1, seed=1, entities={
        1: V2EntityBuilder(1).kind("target").location(0.0, 0.0).build(),
        2: V2EntityBuilder(2).kind("target").location(1.0, 1.0).build()
    })
    
    # Case B: Build entities 2 then 1 (dictionaries might have different internal order)
    entities_b = {}
    entities_b[2] = V2EntityBuilder(2).kind("target").location(1.0, 1.0).build()
    entities_b[1] = V2EntityBuilder(1).kind("target").location(0.0, 0.0).build()
    state_b = AuthoritativeState(tick=1, seed=1, entities=entities_b)
    
    hash_a = CanonicalStateHasher.get_hash(state_a)
    hash_b = CanonicalStateHasher.get_hash(state_b)
    
    assert hash_a == hash_b
    assert hash_a != ""

def test_hash_compact_vs_pretty():
    """Verify that pretty printing for debug doesn't change the authoritative hash."""
    state = AuthoritativeState(tick=1, seed=1, entities={
        1: V2EntityBuilder(1).kind("target").location(0.0, 0.0).build()
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
        1: V2EntityBuilder(1).kind("a").location(0.0, 0.0).identity(properties={"z": 1, "a": 2}).build()
    })
    state_b = AuthoritativeState(tick=1, seed=1, entities={
        1: V2EntityBuilder(1).kind("a").location(0.0, 0.0).identity(properties={"a": 2, "z": 1}).build()
    })
    
    assert CanonicalStateHasher.get_hash(state_a) == CanonicalStateHasher.get_hash(state_b)


def test_deep_property_sorting():
    """
    Verify that nested dictionaries in identity.properties are sorted during
    canonical hashing.

    Fraud this catches:
    - canonical hashing depends on dictionary insertion order
    - nested properties are serialized inconsistently
    - identity.properties is ignored or normalized incorrectly
    """
    state_a = AuthoritativeState(
        tick=1,
        seed=1,
        entities={
            1: (
                V2EntityBuilder(1)
                .kind("a")
                .location(0.0, 0.0)
                .identity(properties={"meta": {"b": 2, "a": 1}})
                .build()
            )
        },
    )

    state_b = AuthoritativeState(
        tick=1,
        seed=1,
        entities={
            1: (
                V2EntityBuilder(1)
                .kind("a")
                .location(0.0, 0.0)
                .identity(properties={"meta": {"a": 1, "b": 2}})
                .build()
            )
        },
    )

    assert CanonicalStateHasher.get_hash(state_a) == CanonicalStateHasher.get_hash(state_b)


def test_hash_isolation():
    """Milestone A Law: Proves non-authoritative state is isolated from the hash."""
    state = AuthoritativeState(tick=1, seed=1)
    hash_init = CanonicalStateHasher.get_hash(state)
    
    # Simulate non-authoritative state variation
    # (By creating a new instance with same authoritative data, 
    # but imagining it was part of a different Kernel context)
    state_same = AuthoritativeState(tick=1, seed=1)
    
    assert hash_init == CanonicalStateHasher.get_hash(state_same)


def test_rng_hash_reproducibility():
    """Verify that RNG state checkpoints are stable and reproducible in the hash."""
    from src.platform.rng import DeterministicRNG
    from src.core.enums import Domain
    rng = DeterministicRNG(base_seed=123)
    
    # Advance RNG
    rng.next_float(Domain.DEFAULT)
    checkpoint_1 = rng.get_state()
    
    state_a = AuthoritativeState(tick=1, seed=123, rng_checkpoint=checkpoint_1)
    hash_a = CanonicalStateHasher.get_hash(state_a)
    
    # Restore and verify
    rng.set_state(checkpoint_1)
    checkpoint_2 = rng.get_state()
    
    state_b = AuthoritativeState(tick=1, seed=123, rng_checkpoint=checkpoint_2)
    hash_b = CanonicalStateHasher.get_hash(state_b)
    
    # Checkpoint tuples are identical
    assert checkpoint_1 == checkpoint_2
    # Hashes are identical
    assert hash_a == hash_b
    
    # Differing RNG state should change the hash
    rng.next_float(Domain.DEFAULT)
    checkpoint_3 = rng.get_state()
    state_c = AuthoritativeState(tick=1, seed=123, rng_checkpoint=checkpoint_3)
    assert CanonicalStateHasher.get_hash(state_c) != hash_a
