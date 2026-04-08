"""Public reputation profile — how the world sees an entity. [PHASE 2]

Reputation is public-facing state, separate from private belief and memory.
It represents social memory: defender, coward, looter, boss-slayer.
Reputation changes behavior by affecting who gets help, better offers,
priority quests, and social standing.
"""

from __future__ import annotations

from pydantic import Field, ConfigDict
from src.core.models.base import SimulationModel


class ReputationProfile(SimulationModel):
    """Multi-dimensional public reputation for an entity. [PHASE 2]

    Each dimension is bounded [-10.0, 10.0]. Tags provide additional
    categorical labels like "town_defender" or "known_looter".
    """
    model_config = ConfigDict(extra='forbid')

    defender_score: float = Field(default=0.0, ge=-10.0, le=10.0)
    cowardice_score: float = Field(default=0.0, ge=-10.0, le=10.0)
    greed_score: float = Field(default=0.0, ge=-10.0, le=10.0)
    heroism_score: float = Field(default=0.0, ge=-10.0, le=10.0)
    threat_notoriety: float = Field(default=0.0, ge=-10.0, le=10.0)
    trustworthiness: float = Field(default=0.0, ge=-10.0, le=10.0)
    reputation_tags: list[str] = Field(default_factory=list)


# Pydantic model rebuild
ReputationProfile.model_rebuild()
