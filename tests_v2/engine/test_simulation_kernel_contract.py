from dataclasses import dataclass
from typing import List
import pytest
from src_v2.engine.phases import TickPhase, get_authoritative_phases


def test_authoritative_phase_list():
    """Ensure the authoritative phase list matches the Milestone 1 contract."""
    phases = get_authoritative_phases()
    expected = [
        TickPhase.INIT,
        TickPhase.SCHEDULING,
        TickPhase.COLLECTION,
        TickPhase.RESOLUTION,
        TickPhase.CLEANUP,
        TickPhase.ADVANCEMENT
    ]
    assert phases == expected


def test_phase_existence():
    """Ensure all required phases are present in the Enum."""
    assert TickPhase.INIT
    assert TickPhase.SCHEDULING
    assert TickPhase.COLLECTION
    assert TickPhase.RESOLUTION
    assert TickPhase.CLEANUP
    assert TickPhase.ADVANCEMENT
    assert TickPhase.PERSISTENCE
