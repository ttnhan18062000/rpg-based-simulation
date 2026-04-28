import pytest
from src.core.enums import Domain
from src.platform.rng import DeterministicRNG

def test_stateless_rng_determinism():
    """
    Proves that calling get_float or get_int out of order
    for different entities still produces deterministic results.
    """
    seed = 12345
    tick = 10
    rng = DeterministicRNG(seed)

    # Test that order of evaluation doesn't matter
    
    # Sequential evaluation
    val1_seq = rng.get_float(Domain.TACTICAL, tick, entity_id=1)
    val2_seq = rng.get_float(Domain.TACTICAL, tick, entity_id=2)
    val3_seq = rng.get_float(Domain.TACTICAL, tick, entity_id=3)

    # Reverse evaluation order
    val3_rev = rng.get_float(Domain.TACTICAL, tick, entity_id=3)
    val2_rev = rng.get_float(Domain.TACTICAL, tick, entity_id=2)
    val1_rev = rng.get_float(Domain.TACTICAL, tick, entity_id=1)

    assert val1_seq == val1_rev
    assert val2_seq == val2_rev
    assert val3_seq == val3_rev

    # Same entity, different ticks should be different
    val1_tick11 = rng.get_float(Domain.TACTICAL, 11, entity_id=1)
    assert val1_seq != val1_tick11

    # Same tick, different domains should be different
    val1_spawn = rng.get_float(Domain.SPAWN, tick, entity_id=1)
    assert val1_seq != val1_spawn

def test_stateless_rng_sub_id():
    """
    Proves that multiple rolls for the same entity and tick are distinct 
    if sub_id is provided.
    """
    seed = 12345
    tick = 10
    rng = DeterministicRNG(seed)

    roll_1 = rng.get_float(Domain.TACTICAL, tick, entity_id=1, sub_id=0)
    roll_2 = rng.get_float(Domain.TACTICAL, tick, entity_id=1, sub_id=1)
    roll_3 = rng.get_float(Domain.TACTICAL, tick, entity_id=1, sub_id=2)

    assert roll_1 != roll_2
    assert roll_2 != roll_3
    assert roll_1 != roll_3
