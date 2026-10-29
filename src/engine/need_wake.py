"""The cadence on which a pressing need, or a present threat, wakes a held action for a re-decision (decision 32 applied to the needs).

A leaf module so the scheduler (which wakes holders) and the threat tests (which read the same window) share one definition without importing each other."""
from __future__ import annotations

from src.engine.cadence import SystemCadence

NEED_WAKE_CADENCE: int = SystemCadence.model_fields["strategic_intelligence"].default
