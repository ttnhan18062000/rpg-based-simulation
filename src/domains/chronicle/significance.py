"""
src/domains/chronicle/significance.py
────────────────────────────────────────────────────────────────────────────────
EventSignificanceScorer — classifies NarrativeLedgerEntry objects for inclusion
in the Chronicle Compiler pipeline.

Implemented by E51A (TCK-20260619-E51A-SIGNIFICANCE).
Gates E51B (Grouper), E51C (Naming), E51D (Renderer), E51E (REST API).

Design constraints:
  - Pure stateless classifier. No durable state. No engine imports.
  - score() and is_chronicle_worthy() are deterministic given the same entry.
  - Hero bonus (+0.3) applies when entry.payload["entity_role"] == "HERO".
  - Score is capped at 1.0.
"""
from __future__ import annotations

from src.domains.campaigns.state import NarrativeLedgerEntry

# Base significance weights per event type.
# Unknown event types fall back to 0.1 (below CHRONICLE_THRESHOLD).
BASE_SIGNIFICANCE: dict[str, float] = {
    "entity_death": 0.5,        # HERO death → 0.8 via hero_bonus
    "faction_destroyed": 0.9,
    "quest_completed": 0.7,
    "calamity": 0.85,
    "LEGENDARY_ARRIVAL": 0.75,
    "KNOWN_TRAITOR_SPOTTED": 0.6,
    "betrayal_desertion": 0.7,
    "INFLATION_SPIRAL": 0.5,
    # Faction war / diplomatic events (E53D)
    "war_declared":          0.95,
    "siege_begins":          0.80,
    "territory_transferred": 0.85,
    "alliance_formed":       0.80,
    "peace_treaty":          0.75,
    "betrayal":              0.85,
}

# Events scoring at or above this threshold appear in the chronicle.
CHRONICLE_THRESHOLD: float = 0.5


class EventSignificanceScorer:
    """Stateless classifier for NarrativeLedgerEntry chronicle worthiness.

    Usage::

        scorer = EventSignificanceScorer()
        score = EventSignificanceScorer.score(entry)
        if EventSignificanceScorer.is_chronicle_worthy(entry):
            ...
    """

    @staticmethod
    def score(entry: NarrativeLedgerEntry) -> float:
        """Return a significance score in [0.0, 1.0] for the given entry.

        The score is derived from BASE_SIGNIFICANCE[event_type] (default 0.1)
        plus a hero_bonus of 0.3 when entry.payload["entity_role"] == "HERO".
        The result is capped at 1.0.

        Args:
            entry: A frozen NarrativeLedgerEntry from the campaign ledger.

        Returns:
            float in [0.0, 1.0].
        """
        base = BASE_SIGNIFICANCE.get(entry.event_type, 0.1)
        hero_bonus = 0.3 if entry.payload.get("entity_role") == "HERO" else 0.0
        return min(1.0, base + hero_bonus)

    @staticmethod
    def is_chronicle_worthy(entry: NarrativeLedgerEntry) -> bool:
        """Return True if the entry's score meets the chronicle inclusion threshold.

        Args:
            entry: A frozen NarrativeLedgerEntry from the campaign ledger.

        Returns:
            True if score(entry) >= CHRONICLE_THRESHOLD.
        """
        return EventSignificanceScorer.score(entry) >= CHRONICLE_THRESHOLD
