"""Integration test: LoyaltyDriftService against a real Culture Drift pipeline run
(TCK-20260905-DRIFTING-LOYALTY-SIGNAL, idea 56).

Confirms `LoyaltyDriftService.compute_loyalty_pressure()` derives a real, non-default
value once `region_cultures` is genuinely populated by the real `CultureDriftExporter`
pipeline — the same synthetic-ledger, real-derivation-code approach as the existing
`test_culture_drift_acceptance.py` in this same directory (no full engine run; a full
multi-episode `campaign_life_arc.yaml` engine run is out of scope for a fast
integration test, matching that precedent).

`config/simulation_quality/profiles/campaign_life_arc.yaml` is the one real corpus
profile that enables multi-episode Campaign mode (confirmed hardcoded to world
`frontier_living_world`, not wired into standard CI) — this test exercises the same
real `war_declared`/`faction_conflict_exposure` derivation path that profile's own
multi-episode run would exercise, without paying the cost of a full engine run.
"""

from __future__ import annotations

import os

import pytest

from src.domains.campaigns.state import CampaignState, NarrativeLedgerEntry
from src.domains.chronicle.grouper import ChronicleGrouper
from src.domains.culture.exporter import CultureDriftExporter
from src.systems.social_systems.loyalty_drift import LoyaltyDriftService

_PROFILE_PATH = "config/simulation_quality/profiles/campaign_life_arc.yaml"


def test_campaign_life_arc_profile_exists():
    """The one real corpus profile this test's scenario represents must actually exist."""
    assert os.path.exists(_PROFILE_PATH), (
        f"{_PROFILE_PATH} not found -- this ticket's own AC targets this real profile"
    )


def _war_entry(region_id: str, episode: int, tick: int) -> NarrativeLedgerEntry:
    """A real `war_declared` entry -- the literal event_type CultureDeriver's own
    _CONFLICT_EVENTS matches, confirmed via src/domains/campaigns/orchestrator.py's
    _SIGNIFICANCE_MAP: FACTION_WAR_DECLARED -> ("war_declared", 0.95), a real,
    live-production world-event mapping, not a payload sub-field."""
    return NarrativeLedgerEntry(
        episode=episode,
        tick=tick,
        event_type="war_declared",
        subject_id="faction_a",
        payload={"region_id": region_id},
        significance=0.9,
        entry_id=f"{episode}:{tick}:war_declared:faction_a:{region_id}",
    )


def test_loyalty_pressure_derives_from_real_culture_drift_output():
    """A region with real, live-derived war/conflict events produces a real,
    non-zero loyalty-pressure signal -- proving the full pipeline (synthetic
    ledger -> ChronicleGrouper -> CultureDriftExporter -> region_cultures ->
    LoyaltyDriftService) works end to end, not just the unit-level mock."""
    state = CampaignState(campaign_id="loyalty_drift_it", episode_index=0)
    entries = [_war_entry("contested_region", episode=0, tick=t) for t in (10, 20, 30)]
    hierarchy = ChronicleGrouper().group(entries)

    CultureDriftExporter.export(state, hierarchy, episode_index=0)

    assert "contested_region" in state.region_cultures, (
        "Real CultureDriftExporter run should have populated region_cultures"
    )
    pressure = LoyaltyDriftService.compute_loyalty_pressure(state, "contested_region")
    assert pressure > 0.0, (
        "A region with real faction-conflict events should show real loyalty pressure"
    )


def test_loyalty_pressure_zero_for_untouched_region_in_same_campaign():
    """A region with zero recorded events in the same real Campaign run correctly
    yields zero loyalty pressure -- not a leaked/shared value from another region."""
    state = CampaignState(campaign_id="loyalty_drift_it", episode_index=0)
    entries = [_war_entry("contested_region", episode=0, tick=10)]
    hierarchy = ChronicleGrouper().group(entries)
    CultureDriftExporter.export(state, hierarchy, episode_index=0)

    assert LoyaltyDriftService.compute_loyalty_pressure(state, "peaceful_region") == 0.0
