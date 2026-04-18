import pytest
from unittest.mock import MagicMock
from src_v2.engine.phases import TickPhase, get_authoritative_phases


def test_phase_order_frozen():
    """Verify that the phase order is exactly as defined in the contract."""
    # This is a redundant double-check of the contract law.
    phases = list(TickPhase)
    assert phases[0] == TickPhase.INIT
    assert phases[1] == TickPhase.SCHEDULING
    assert phases[2] == TickPhase.COLLECTION
    assert phases[3] == TickPhase.RESOLUTION
    assert phases[4] == TickPhase.CLEANUP
    assert phases[5] == TickPhase.ADVANCEMENT
    assert phases[6] == TickPhase.PERSISTENCE


def test_contractual_phase_sequence():
    """The get_authoritative_phases helper must return the exact sequence."""
    seq = get_authoritative_phases()
    assert len(seq) == 6
    assert seq[0] == TickPhase.INIT
    assert seq[-1] == TickPhase.ADVANCEMENT
