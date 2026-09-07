"""
src/systems/social_systems/loyalty_drift.py
───────────────────────────────────────────────────────────────────────────────
LoyaltyDriftService — derives a per-region loyalty-pressure signal from Culture
Drift's already-live `region_cultures` output (idea 56, M6 Political Identity).

Ticket: TCK-20260905-DRIFTING-LOYALTY-SIGNAL

Builds no new Culture Drift derivation/bias-application machinery — reuses
`faction_conflict_exposure` (an existing CultureState axis, "Derived from
war_declared, territory_transferred, faction_destroyed events. Raises entity
caution, lowers loyalty.") and CultureDriftImporter.get_culture()'s existing
None-safe lookup exactly as they already exist.

Feeds into PartyLifecycleService.effective_defection_threshold() as an
optional, backward-compatible parameter (idea 39's mutation-trigger
condition) — see docs/world/culture_drift_contract.md for the full
mechanism. Bridged into the live per-tick GroupPhase.resolve() call site by
TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE (AuthoritativeState.
region_loyalty_pressure, populated once per episode by
CampaignOrchestrator._build_initial_state()) — this signal is now live in
any Campaign-mode run past episode 0, not a no-op.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domains.campaigns.state import CampaignState


class LoyaltyDriftService:
    """Pure-static, read-only service deriving loyalty pressure from region_cultures."""

    @staticmethod
    def compute_loyalty_pressure(campaign_state: "CampaignState", region_id: str) -> float:
        """
        Return the loyalty-pressure signal for `region_id`, derived from that
        region's carried-forward `faction_conflict_exposure` culture axis.

        Contract:
            - Read-only: never mutates campaign_state or any durable structure.
            - None-safe: returns 0.0 (no pressure) if the region has no
              region_cultures entry yet, or if region_id is falsy.
            - Deterministic: pure function of (campaign_state, region_id).
        """
        if not region_id:
            return 0.0

        from src.domains.culture.exporter import CultureDriftImporter

        culture = CultureDriftImporter.get_culture(campaign_state, region_id)
        if culture is None:
            return 0.0
        return culture.faction_conflict_exposure
