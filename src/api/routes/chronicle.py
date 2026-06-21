"""
src/api/routes/chronicle.py
────────────────────────────────────────────────────────────────────────────────
Chronicle REST endpoints.

Implemented for E51E (TCK-20260619-E51E-REST-API):
  GET /api/v1/chronicle/{campaign_id}
  GET /api/v1/chronicle/{campaign_id}/eras/{era_id}/summary

Architecture constraints:
  - No raw domain models from API — all responses go through the presenter layer.
  - Chronicle data is stored in a module-level registry (dict keyed by
    campaign_id). ChronicleCompiler callers register the compiled JSON dict here
    after a successful compile().
  - No filesystem reads at request time — data is pre-loaded at registration.
  - No dependency on V2EngineManager.
"""
from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, HTTPException

from src.api.presenters.chronicle import (
    ChronicleResponse,
    ErasSummaryResponse,
)

router = APIRouter(prefix="/chronicle", tags=["Chronicle"])

# ── Chronicle Registry ─────────────────────────────────────────────────────────
# Maps campaign_id → chronicle JSON dict (as returned by ChronicleRenderer.render_json()).
# Populated by register_chronicle() after a successful ChronicleCompiler.compile().
# In tests, inject directly via register_chronicle().
_CHRONICLE_REGISTRY: Dict[str, dict] = {}


def register_chronicle(campaign_id: str, data: dict) -> None:
    """Register a compiled chronicle dict for REST access.

    Call this after ChronicleCompiler.compile() completes to make the chronicle
    available via the /chronicle/{campaign_id} endpoints.

    Args:
        campaign_id: The campaign identifier (must match data["campaign_id"]).
        data: The JSON dict returned by ChronicleRenderer.render_json() or
              loaded from chronicle.json on disk.
    """
    _CHRONICLE_REGISTRY[campaign_id] = data


def unregister_chronicle(campaign_id: str) -> None:
    """Remove a chronicle from the registry."""
    _CHRONICLE_REGISTRY.pop(campaign_id, None)


def _clear_registry() -> None:
    """Clear all registered chronicles. Intended for test teardown only."""
    _CHRONICLE_REGISTRY.clear()


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.get(
    "/{campaign_id}",
    response_model=ChronicleResponse,
    summary="Get full chronicle for a campaign",
    description=(
        "Return the full structured chronicle (eras, episodes, named_milestones) "
        "for the specified campaign. Data is sourced from the compiled chronicle.json "
        "registered after ChronicleCompiler.compile()."
    ),
    responses={
        404: {"description": "Chronicle not found for campaign"},
        500: {"description": "Internal error"},
    },
)
async def get_chronicle(campaign_id: str) -> ChronicleResponse:
    """Return the full chronicle JSON for the given campaign as a shaped response.

    Returns:
        ChronicleResponse with campaign_id, eras, episodes, and named_milestones.

    Raises:
        HTTPException(404): If no chronicle is registered for the given campaign_id.
        HTTPException(500): On unexpected shape/parsing errors.
    """
    data = _CHRONICLE_REGISTRY.get(campaign_id)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Chronicle for campaign '{campaign_id}' not found.",
        )

    try:
        return ChronicleResponse.from_dict(campaign_id, data)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to shape chronicle for campaign '{campaign_id}': {exc}",
        ) from exc


@router.get(
    "/{campaign_id}/eras/{era_id}/summary",
    response_model=ErasSummaryResponse,
    summary="Get era summary with milestone names",
    description=(
        "Return a summary of a specific era: its name, milestone count, and list of "
        "named milestone strings. The era_id format is 'era:{ordinal}' (e.g. 'era:0')."
    ),
    responses={
        404: {"description": "Chronicle or era not found"},
        500: {"description": "Internal error"},
    },
)
async def get_era_summary(campaign_id: str, era_id: str) -> ErasSummaryResponse:
    """Return era summary with named milestones for the given era.

    Collects all named_milestones whose episode index falls within the era's
    episode_ids, then returns count and name strings.

    Args:
        campaign_id: The campaign identifier.
        era_id: The era identifier string (e.g. 'era:0', 'era:1').

    Returns:
        ErasSummaryResponse with era_id, name, milestone_count, named_milestones.

    Raises:
        HTTPException(404): If campaign or era_id not found.
        HTTPException(500): On unexpected errors.
    """
    data = _CHRONICLE_REGISTRY.get(campaign_id)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Chronicle for campaign '{campaign_id}' not found.",
        )

    try:
        # Find the era by id
        era_dict: dict | None = None
        for era in data.get("eras", []):
            if era.get("id") == era_id:
                era_dict = era
                break

        if era_dict is None:
            raise HTTPException(
                status_code=404,
                detail=f"Era '{era_id}' not found in chronicle for campaign '{campaign_id}'.",
            )

        era_name: str = era_dict.get("name", "")
        episode_ids: list[str] = era_dict.get("episode_ids", [])

        # Convert "episode:{index}" strings → set of int indices
        era_episode_indices: set[int] = set()
        for ep_id in episode_ids:
            # Format is "episode:{index}"
            parts = ep_id.split(":")
            if len(parts) == 2 and parts[1].isdigit():
                era_episode_indices.add(int(parts[1]))

        # Collect milestone names for episodes in this era
        milestone_names: list[str] = [
            m["name"]
            for m in data.get("named_milestones", [])
            if m.get("episode") in era_episode_indices
        ]

        return ErasSummaryResponse(
            era_id=era_id,
            name=era_name,
            milestone_count=len(milestone_names),
            named_milestones=milestone_names,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve era summary: {exc}",
        ) from exc
