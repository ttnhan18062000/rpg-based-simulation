"""
src/domains/information/trust.py
───────────────────────────────────────────────────────────────────────────────
Phase 5 — SourceTrustUpdateService

Handles slow, gradual adjustments to source trust entries clamped inside [0.0, 1.0].
"""

from __future__ import annotations
from typing import Optional

from src.core.state import EntityState
from src.core.strategic import SourceTrustEntry


class SourceTrustUpdateService:
    """
    Adjusts SourceTrustEntry values gradually.
    """

    @staticmethod
    def update(
        entity: EntityState,
        source_entity_id: int,
        outcome: str,  # "CONFIRMED" | "PARTIALLY_CONFIRMED" | "CONTRADICTED" | "NOT_VERIFIABLE"
        current_tick: int = 0,
    ) -> SourceTrustEntry:
        """
        Produce updated SourceTrustEntry for source.
        """
        # Load existing trust entry
        strat = getattr(entity, "strategic", None)
        trust_map = getattr(strat, "source_trust", {}) or {}
        entry = trust_map.get(source_entity_id)

        current_trust = 0.5
        interactions = 0
        if entry:
            current_trust = entry.trust
            interactions = entry.interactions

        delta = 0.0
        if outcome == "CONFIRMED":
            delta = 0.08
        elif outcome == "PARTIALLY_CONFIRMED":
            delta = 0.03
        elif outcome == "CONTRADICTED":
            delta = -0.12
        elif outcome == "DECEPTIVE_DETECTED":
            delta = -0.25

        new_trust = max(0.0, min(1.0, current_trust + delta))
        
        return SourceTrustEntry(
            entity_id=source_entity_id,
            trust=round(new_trust, 4),
            interactions=interactions + 1,
            last_outcome=outcome,
        )
