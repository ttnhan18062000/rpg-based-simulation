"""AC3 wiring test: FidelityExporter.export() runs from the same
CampaignOrchestrator._advance_state() call site as CultureDriftExporter.export().

Follows tests/unit/domains/campaigns/test_orchestrator_plan_wiring.py's
precedent of calling orch._advance_state() directly with a synthetic
AuthoritativeState.
"""

from unittest.mock import MagicMock

from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
from src.domains.campaigns.state import EpisodeSummary, NarrativeLedgerEntry


def _make_manifest() -> CampaignManifest:
    return CampaignManifest(id="test_campaign", episodes=[MagicMock()])


def test_fidelity_exporter_runs_alongside_culture_drift_exporter_in_advance_state():
    manifest = _make_manifest()
    orch = CampaignOrchestrator(manifest)

    # Pre-seed narrative_ledger with a chronicle-worthy calamity entry so
    # ChronicleGrouper().group() in _advance_state() produces a non-empty
    # hierarchy for both exporters to consume.
    orch.state.narrative_ledger.append(
        NarrativeLedgerEntry(
            episode=0,
            tick=1,
            event_type="calamity",
            subject_id="world",
            payload={"region_id": "r1"},
            significance=0.85,
            entry_id="0:1:calamity:world",
        )
    )

    final_state = MagicMock()
    final_state.entities = {}
    final_state.recent_world_events = []

    summary = EpisodeSummary(episode_index=0, completed_tick=10)
    orch._advance_state(final_state, summary)

    assert "r1" in orch.state.region_cultures
    assert "0:1:calamity:world" in orch.state.historical_drift
    assert orch.state.historical_drift["0:1:calamity:world"].derived_episode == 0
