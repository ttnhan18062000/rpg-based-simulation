from src_v2.platform.rng import DeterministicRNG


def test_rng_reproducibility():
    """Seed 42 must yield the same 1k sequence every time."""
    seed = 42
    rng1 = DeterministicRNG(seed)
    rng2 = DeterministicRNG(seed)
    
    seq1 = [rng1.next_float() for _ in range(1000)]
    seq2 = [rng2.next_float() for _ in range(1000)]
    
    assert seq1 == seq2
    assert len(set(seq1)) > 900  # Ensure basic entropy


def test_rng_isolation():
    """Instances must not share state."""
    rng1 = DeterministicRNG(1)
    rng2 = DeterministicRNG(2)
    
    val1 = rng1.next_float()
    val2 = rng2.next_float()
    
    assert val1 != val2


def test_rng_state_persistence():
    """State capture and restoration must be byte-identical."""
    rng = DeterministicRNG(123)
    [rng.next_float() for _ in range(10)]
    
    state = rng.get_state()
    expected = rng.next_float()
    
    # Restore and verify
    rng.set_state(state)
    actual = rng.next_float()
    
    assert actual == expected
