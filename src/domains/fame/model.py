"""
src/domains/fame/model.py
───────────────────────────────────────────────────────────────────────────────
FameState and FameCarryForward — the data model for Chronicle-derived entity
fame (idea 57, "The Living Legend Feedback Loop").

Design constraints:
  - MUST NOT import from src.engine or src.core.state at module level.
  - All records are frozen (immutable after construction).
  - to_dict() / from_dict() provide JSON-safe round-trip.
  - fame clamped to [0.0, 1.0]; default 0.0 means no accumulated fame yet.
  - CampaignState stores Dict[str, FameCarryForward] keyed by
    NarrativeLedgerEntry.subject_id.

Populated by: FameDeriver / FameExporter (end-of-episode hook).
Consumed by:  FameImporter (no live caller yet -- LegendFactService is the
              intended reader, itself a lazy, non-durable read-model with no
              live perception/motivation wiring yet).
Stored in:    CampaignState.entity_fame (Dict[str, FameCarryForward]).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FameState:
    """Immutable snapshot of one subject's accumulated Chronicle-derived fame.

    fame: float in [0.0, 1.0]. 0.0 = no accumulated fame. Increases with
    quest_completed and HERO entity_death entries attributed to this subject
    (see FameDeriver).
    """

    fame: float = 0.0

    def to_dict(self) -> dict:
        return {"fame": self.fame}

    @classmethod
    def from_dict(cls, d: dict) -> "FameState":
        return cls(fame=d.get("fame", 0.0))


@dataclass(frozen=True, slots=True)
class FameCarryForward:
    """Durable per-subject fame snapshot carried across episodes.

    Fields
    ------
    subject_id : str
        The NarrativeLedgerEntry.subject_id this snapshot describes.
    fame : FameState
        The fame value as of derived_episode.
    derived_episode : int
        0-based index of the episode in which this snapshot was derived.
    """

    subject_id: str
    fame: FameState
    derived_episode: int

    def to_dict(self) -> dict:
        return {
            "subject_id": self.subject_id,
            "fame": self.fame.to_dict(),
            "derived_episode": self.derived_episode,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FameCarryForward":
        return cls(
            subject_id=d["subject_id"],
            fame=FameState.from_dict(d.get("fame", {})),
            derived_episode=d.get("derived_episode", 0),
        )
