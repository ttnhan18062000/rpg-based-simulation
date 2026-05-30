"""
src/domains/commitment/pressure.py
───────────────────────────────────────────────────────────────────────────────
CommitmentPressureService for Phase 15.
"""

from __future__ import annotations
from src.core.cognition import CommitmentEntry

class CommitmentPressureService:
    """Computes pressure to fulfill or keep active commitments."""

    @staticmethod
    def compute_pressure(entry: CommitmentEntry, current_tick: int, hp_ratio: float) -> float:
        # Base pressure is from commitment strength
        pressure = entry.strength

        # If deadline is near, pressure increases
        if entry.deadline_tick is not None:
            ticks_left = entry.deadline_tick - current_tick
            if ticks_left <= 0:
                pressure = 0.0 # expired/failed
            elif ticks_left < 20:
                pressure += (20 - ticks_left) * 0.02

        # Survival threshold: low health heavily scales down commitment pressure
        if hp_ratio < 0.2:
            pressure *= 0.1

        return min(1.0, max(0.0, pressure))
