import pytest
from src.engine.cadence import should_run, SystemCadence


def test_should_run_cadence_1():
    # Cadence 1 should always run
    assert should_run(1, None, 1) is True
    assert should_run(2, None, 1) is True
    assert should_run(1, 123, 1) is True
    assert should_run(1, None, 0) is True  # Edge case


def test_should_run_global_cadence():
    # Global system (entity_id=None)
    cadence = 10
    assert should_run(0, None, cadence) is True
    assert should_run(5, None, cadence) is False
    assert should_run(10, None, cadence) is True
    assert should_run(20, None, cadence) is True


def test_should_run_staggered_entity_cadence():
    # Entity-specific system
    cadence = 10
    
    # Entity 0
    assert should_run(0, 0, cadence) is True
    assert should_run(10, 0, cadence) is True
    
    # Entity 1
    assert should_run(0, 1, cadence) is False
    assert should_run(9, 1, cadence) is True   # (9 + 1) % 10 == 0
    assert should_run(19, 1, cadence) is True
    
    # Entity 5
    assert should_run(5, 5, cadence) is True   # (5 + 5) % 10 == 0
    assert should_run(15, 5, cadence) is True


def test_system_cadence_defaults():
    cadence = SystemCadence()
    assert cadence.movement == 1
    assert cadence.strategic_intelligence == 10
    assert cadence.world_dynamics == 50
