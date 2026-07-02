"""
src/api/presenters/chronicle.py
────────────────────────────────────────────────────────────────────────────────
Presenter layer for chronicle REST responses.

Enforces the API boundary rule: no raw domain models are exposed from routes.
All responses go through these Pydantic read models.

Implemented for E51E (TCK-20260619-E51E-REST-API).
"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel


class ChronicleEraPresenter(BaseModel):
    """Shaped read model for a single era entry in chronicle.json."""

    id: str
    ordinal: int
    name: str
    significance: float
    episode_ids: List[str]


class ChronicleEpisodePresenter(BaseModel):
    """Shaped read model for a single episode entry in chronicle.json."""

    id: str
    index: int
    significance: float
    incident_ids: List[str]


class ChronicleMilestonePresenter(BaseModel):
    """Shaped read model for a single named milestone in chronicle.json."""

    name: str
    tick: int
    episode: int
    event_type: str
    significance: float
    entry_id: str


class ChronicleResponse(BaseModel):
    """Shaped read model for GET /api/v1/chronicle/{campaign_id} response.

    Mirrors the chronicle.json schema produced by ChronicleRenderer.render_json().
    """

    campaign_id: str
    eras: List[ChronicleEraPresenter]
    episodes: List[ChronicleEpisodePresenter]
    named_milestones: List[ChronicleMilestonePresenter]

    @classmethod
    def from_dict(cls, campaign_id: str, data: dict) -> "ChronicleResponse":
        """Construct from a chronicle.json dict (as returned by ChronicleCompiler).

        Args:
            campaign_id: The campaign identifier (used as response key).
            data: The raw dict from chronicle.json / ChronicleRenderer.render_json().

        Returns:
            ChronicleResponse with fully shaped presenter sub-objects.
        """
        eras = [
            ChronicleEraPresenter(
                id=e["id"],
                ordinal=e["ordinal"],
                name=e["name"],
                significance=e["significance"],
                episode_ids=list(e.get("episode_ids", [])),
            )
            for e in data.get("eras", [])
        ]
        episodes = [
            ChronicleEpisodePresenter(
                id=ep["id"],
                index=ep["index"],
                significance=ep["significance"],
                incident_ids=list(ep.get("incident_ids", [])),
            )
            for ep in data.get("episodes", [])
        ]
        milestones = [
            ChronicleMilestonePresenter(
                name=m["name"],
                tick=m["tick"],
                episode=m["episode"],
                event_type=m["event_type"],
                significance=m["significance"],
                entry_id=m["entry_id"],
            )
            for m in data.get("named_milestones", [])
        ]
        return cls(
            campaign_id=campaign_id,
            eras=eras,
            episodes=episodes,
            named_milestones=milestones,
        )


class ErasSummaryResponse(BaseModel):
    """Shaped read model for GET /api/v1/chronicle/{campaign_id}/eras/{era_id}/summary."""

    era_id: str
    name: str
    milestone_count: int
    named_milestones: List[str]
