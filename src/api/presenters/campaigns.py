"""
src/api/presenters/campaigns.py
────────────────────────────────────────────────────────────────────────────────
Presenter layer for campaign REST responses.

Enforces the API boundary rule: no raw domain models are exposed from routes.
All responses go through these Pydantic read models.

Implemented for E32E (TCK-20260619-E32E-REST-HISTORY).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class NarrativeLedgerEntryPresenter(BaseModel):
    """Shaped read model for a single NarrativeLedgerEntry.

    Mirrors the 7-field NarrativeLedgerEntry schema but as a Pydantic model
    suitable for JSON serialization via FastAPI. No domain imports.
    """

    episode: int
    tick: int
    event_type: str
    subject_id: str
    payload: Dict[str, Any]
    significance: float
    entry_id: str

    @classmethod
    def from_domain(cls, entry: Any) -> "NarrativeLedgerEntryPresenter":
        """Construct from a NarrativeLedgerEntry domain object.

        Uses attribute access rather than importing the domain type directly,
        preserving the one-way dependency direction (presenter → domain is fine,
        domain → presenter is forbidden).
        """
        return cls(
            episode=entry.episode,
            tick=entry.tick,
            event_type=entry.event_type,
            subject_id=entry.subject_id,
            payload=dict(entry.payload),
            significance=entry.significance,
            entry_id=entry.entry_id,
        )


class CampaignHistoryResponse(BaseModel):
    """Shaped read model for GET /api/v1/campaigns/{id}/history response."""

    campaign_id: str
    entry_count: int
    entries: List[NarrativeLedgerEntryPresenter]


class SettlementPersonalityResponse(BaseModel):
    """Shaped read model for GET /api/v1/campaigns/{id}/regions/{region_id}/personality."""

    campaign_id: str
    region_id: str
    traits: List[str]
    tag_deltas: Dict[str, float]
    is_neutral: bool

    @classmethod
    def from_domain(
        cls, descriptor: Any, campaign_id: str, region_id: str
    ) -> "SettlementPersonalityResponse":
        """Construct from a SettlementPersonalityDescriptor domain object.

        Uses attribute access rather than importing the domain type directly,
        preserving the one-way dependency direction (presenter → domain is
        fine, domain → presenter is forbidden).
        """
        return cls(
            campaign_id=campaign_id,
            region_id=region_id,
            traits=list(descriptor.traits),
            tag_deltas=dict(descriptor.tag_deltas),
            is_neutral=descriptor.is_neutral,
        )
