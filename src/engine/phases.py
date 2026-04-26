from __future__ import annotations

from enum import IntEnum, auto


class TickPhase(IntEnum):
    """
    The authoritative order of operations inside a single simulation tick.
    Status: FROZEN (Resource Phase 4 Milestone 1)
    
    Locked by the Phase 4 Baseline Freeze Contract.
    """
    INIT = auto()           # Context setup, policy/governance evaluation
    SCHEDULING = auto()     # Work selection and budgeting
    COLLECTION = auto()     # Proposal/Work-packet gathering
    RESOLUTION = auto()     # Validation and Apply (Authoritative)
    CLEANUP = auto()        # State finalization and lifecycle
    ADVANCEMENT = auto()    # Increment world tick (Closure)
    
    # Non-authoritative hooks (must not influence authoritative state)
    PERSISTENCE = auto()    # Post-tick logging, replay emission, snapshots


def get_authoritative_phases() -> list[TickPhase]:
    """Returns exactly the 6 phases required for authoritative simulation semantics."""
    return [
        TickPhase.INIT,
        TickPhase.SCHEDULING,
        TickPhase.COLLECTION,
        TickPhase.RESOLUTION,
        TickPhase.CLEANUP,
        TickPhase.ADVANCEMENT
    ]
