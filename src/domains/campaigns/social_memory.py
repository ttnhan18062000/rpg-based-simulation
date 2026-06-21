"""
src/domains/campaigns/social_memory.py
───────────────────────────────────────────────────────────────────────────────
SocialMemoryRecord and InteractionRecord — the data layer for cross-episode
social memory persistence (Epic 4.3).

Design constraints (same as state.py):
  - MUST NOT import from src.engine or src.core.state.
  - All sub-records are frozen (immutable after construction).
  - to_dict() / from_dict() provide JSON-safe round-trip.
  - Dict keys that are int are serialized as str for JSON compatibility.
  - Sorted dict keys for determinism.

Populated by: E43B SocialMemoryExporter (end-of-episode hook).
Consumed by:  E43B SocialMemoryImporter (start-of-episode hook).
Stored in:    CampaignState.social_memories (Dict[int, SocialMemoryRecord]).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# InteractionRecord
# ---------------------------------------------------------------------------

# Valid interaction kinds — used for validation and documentation only.
# Enforcement is intentionally loose (str) to allow forward extension by E43B.
INTERACTION_KINDS = frozenset({
    "helped",
    "betrayed",
    "traded",
    "fought_alongside",
    "conflict",
})


@dataclass(frozen=True)
class InteractionRecord:
    """Immutable record of one social event, persisted across episodes.

    Fields
    ------
    episode : int
        Zero-based episode index in which this interaction occurred.
    tick : int
        Simulation tick within that episode.
    kind : str
        Interaction type. One of INTERACTION_KINDS; extensible by later epics.
    other_entity_id : Optional[int]
        The other entity involved. None for faction-level events.
    faction_id : Optional[str]
        The faction involved. None for direct entity-only events.
    magnitude : float
        Strength of the interaction, clamped 0.0–1.0 by the caller (E43B).
    """

    episode: int
    tick: int
    kind: str
    other_entity_id: Optional[int]
    faction_id: Optional[str]
    magnitude: float

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "episode": self.episode,
            "tick": self.tick,
            "kind": self.kind,
            "other_entity_id": self.other_entity_id,
            "faction_id": self.faction_id,
            "magnitude": self.magnitude,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "InteractionRecord":
        return cls(
            episode=d["episode"],
            tick=d["tick"],
            kind=d["kind"],
            other_entity_id=d.get("other_entity_id"),
            faction_id=d.get("faction_id"),
            magnitude=d["magnitude"],
        )


# ---------------------------------------------------------------------------
# SocialMemoryRecord
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SocialMemoryRecord:
    """Durable per-entity cross-episode social snapshot.

    Holds the accumulated social state for one entity across multiple episodes.
    Written by SocialMemoryExporter (E43B) at episode end; read by
    SocialMemoryImporter (E43B) at the start of the next episode.
    Decay (E43C) is applied by the importer before applying reputation deltas.

    Fields
    ------
    entity_id : int
        The entity this record belongs to.
    interaction_history : Tuple[InteractionRecord, ...]
        Ordered log of significant social events across episodes.
    relationship_scores : Dict[int, float]
        entity_id → net relationship score. Positive = friendly, negative =
        hostile. Used by E43B importer to seed trust/grudge at episode start.
    faction_reputation : Dict[str, float]
        faction_id → reputation score in that faction's eyes. Replaces the
        per-episode-only `public_reputation` float for cross-episode continuity.
    last_betrayal_tick : Optional[int]
        Absolute tick of the most recent betrayal event. Used by E43C for
        grudge decay half-life calculation.
    last_cooperation_tick : Optional[int]
        Absolute tick of the most recent cooperation event. Used by E43C for
        friendship decay half-life calculation.
    """

    entity_id: int
    interaction_history: Tuple[InteractionRecord, ...] = field(default_factory=tuple)
    relationship_scores: Dict[int, float] = field(default_factory=dict)
    faction_reputation: Dict[str, float] = field(default_factory=dict)
    last_betrayal_tick: Optional[int] = None
    last_cooperation_tick: Optional[int] = None

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict. Dict keys sorted for determinism."""
        return {
            "entity_id": self.entity_id,
            "interaction_history": [r.to_dict() for r in self.interaction_history],
            "relationship_scores": {
                str(k): v
                for k, v in sorted(self.relationship_scores.items())
            },
            "faction_reputation": {
                k: v
                for k, v in sorted(self.faction_reputation.items())
            },
            "last_betrayal_tick": self.last_betrayal_tick,
            "last_cooperation_tick": self.last_cooperation_tick,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SocialMemoryRecord":
        """Reconstruct from a dict produced by to_dict(). Inverse of to_dict()."""
        return cls(
            entity_id=d["entity_id"],
            interaction_history=tuple(
                InteractionRecord.from_dict(r)
                for r in d.get("interaction_history", [])
            ),
            relationship_scores={
                int(k): v
                for k, v in d.get("relationship_scores", {}).items()
            },
            faction_reputation=dict(d.get("faction_reputation", {})),
            last_betrayal_tick=d.get("last_betrayal_tick"),
            last_cooperation_tick=d.get("last_cooperation_tick"),
        )
