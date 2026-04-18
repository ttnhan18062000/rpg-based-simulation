from __future__ import annotations

from enum import IntEnum, auto


class TickPhase(IntEnum):
    """
    The authoritative order of operations inside a single simulation tick.
    This order is frozen by the Milestone 1 contract.
    """
    INIT = auto()           # Context setup, request handling
    SCHEDULING = auto()     # Entity eligibility check
    COLLECTION = auto()     # Proposal gathering
    RESOLUTION = auto()     # Validation and Apply
    CLEANUP = auto()        # State finalization, lifecycle
    ADVANCEMENT = auto()    # Increment world tick
    PERSISTENCE = auto()    # Non-authoritative logging/replay (Last)


def get_authoritative_phases() -> list[TickPhase]:
    """Returns only the phases required for core simulation semantics."""
    return [
        TickPhase.INIT,
        TickPhase.SCHEDULING,
        TickPhase.COLLECTION,
        TickPhase.RESOLUTION,
        TickPhase.CLEANUP,
        TickPhase.ADVANCEMENT
    ]
