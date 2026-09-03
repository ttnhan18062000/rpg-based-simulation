"""
src/api/routes/campaigns.py
────────────────────────────────────────────────────────────────────────────────
Campaign REST endpoints.

Implemented for E32E (TCK-20260619-E32E-REST-HISTORY):
  GET /api/v1/campaigns/{id}/history

Architecture constraints:
  - No raw domain models from API — all responses go through the presenter layer.
  - CampaignState is accessed via a module-level registry (dict keyed by
    campaign_id). CampaignOrchestrators register their state here after starting.
  - No dependency on V2EngineManager — campaigns are independent of the
    scenario runtime.
"""
from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from src.api.presenters.campaigns import (
    CampaignHistoryResponse,
    NarrativeLedgerEntryPresenter,
    SettlementPersonalityResponse,
)
from src.domains.campaigns.narrative_ledger import NarrativeLedger
from src.domains.culture.exporter import CultureDriftImporter
from src.domains.culture.settlement_personality import SettlementPersonalityService

# Import only the type for annotation; avoid circular state at module level.
from src.domains.campaigns.state import CampaignState

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

# ── Campaign Registry ──────────────────────────────────────────────────────────
# Maps campaign_id → CampaignState. Populated by register_campaign().
# In production, CampaignOrchestrator calls register_campaign() after creation.
# In tests, inject directly via register_campaign().
_CAMPAIGN_REGISTRY: Dict[str, CampaignState] = {}


def register_campaign(campaign_id: str, state: CampaignState) -> None:
    """Register a CampaignState for REST access.

    Call this after creating a CampaignOrchestrator to make its state
    available via the /campaigns/{id}/history endpoint.

    Args:
        campaign_id: The campaign identifier (must match CampaignState.campaign_id).
        state: The mutable CampaignState owned by the orchestrator.
    """
    _CAMPAIGN_REGISTRY[campaign_id] = state


def unregister_campaign(campaign_id: str) -> None:
    """Remove a campaign from the registry (e.g., after campaign completion)."""
    _CAMPAIGN_REGISTRY.pop(campaign_id, None)


def _clear_registry() -> None:
    """Clear all registered campaigns. Intended for test teardown only."""
    _CAMPAIGN_REGISTRY.clear()


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get(
    "/{campaign_id}/history",
    response_model=CampaignHistoryResponse,
    summary="Get campaign narrative history",
    description=(
        "Return the structured NarrativeLedger for the specified campaign. "
        "Supports optional filtering by event_type, min_significance, and episode."
    ),
    responses={
        404: {"description": "Campaign not found"},
        500: {"description": "Internal error"},
    },
)
async def get_campaign_history(
    campaign_id: str,
    event_type: Optional[str] = Query(
        default=None,
        description="Filter by event type (e.g. 'entity_death', 'quest_completed', 'faction_shift')",
    ),
    min_significance: float = Query(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum significance threshold (inclusive). 0.0 returns all entries.",
    ),
    episode: Optional[int] = Query(
        default=None,
        ge=0,
        description="Filter by episode index (0-based).",
    ),
) -> CampaignHistoryResponse:
    """Return the NarrativeLedger for the given campaign as a shaped JSON response.

    Filters are applied server-side via NarrativeLedger.query(). All three
    filter parameters are optional and combinable.

    Returns:
        CampaignHistoryResponse with campaign_id, entry_count, and shaped entries.

    Raises:
        HTTPException(404): If no campaign with the given ID is registered.
        HTTPException(500): On unexpected errors.
    """
    state = _CAMPAIGN_REGISTRY.get(campaign_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign '{campaign_id}' not found.",
        )

    try:
        ledger = NarrativeLedger(entries=state.narrative_ledger)
        matched = ledger.query(
            event_type=event_type,
            min_significance=min_significance,
            episode=episode,
        )
        entries = [NarrativeLedgerEntryPresenter.from_domain(e) for e in matched]
        return CampaignHistoryResponse(
            campaign_id=campaign_id,
            entry_count=len(entries),
            entries=entries,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve campaign history: {exc}",
        ) from exc


@router.get(
    "/{campaign_id}/regions/{region_id}/personality",
    response_model=SettlementPersonalityResponse,
    summary="Get settlement personality signal for a region",
    description=(
        "Return a Culture-Drift-derived personality signal for a region within the "
        "specified campaign, or a neutral descriptor if no culture data has been "
        "derived for that region yet."
    ),
    responses={
        404: {"description": "Campaign not found"},
        500: {"description": "Internal error"},
    },
)
async def get_settlement_personality(
    campaign_id: str, region_id: str
) -> SettlementPersonalityResponse:
    """Return the settlement-personality signal for a region as a shaped JSON response.

    Reads CampaignState directly from _CAMPAIGN_REGISTRY, mirroring
    get_campaign_history's exact lookup pattern.

    Returns:
        SettlementPersonalityResponse with campaign_id, region_id, traits,
        tag_deltas, and is_neutral.

    Raises:
        HTTPException(404): If no campaign with the given ID is registered.
        HTTPException(500): On unexpected errors.
    """
    state = _CAMPAIGN_REGISTRY.get(campaign_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign '{campaign_id}' not found.",
        )

    try:
        culture = CultureDriftImporter.get_culture(state, region_id)
        descriptor = SettlementPersonalityService.describe(culture)
        return SettlementPersonalityResponse.from_domain(descriptor, campaign_id, region_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve settlement personality: {exc}",
        ) from exc
