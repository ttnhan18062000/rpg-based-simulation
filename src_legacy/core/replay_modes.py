from __future__ import annotations

from enum import IntEnum, auto


class ReplayMode(IntEnum):
    """
    Control modes for simulation forensics.
    M6 Law: Replay richness must be profile-aware and governor-controlled.
    """
    OFF = 0
    MINIMAL = 1
    DEBUG_WINDOWED = 2
    FORENSIC_SHORT_RUN = 3
