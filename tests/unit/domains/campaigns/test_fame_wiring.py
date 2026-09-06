"""AC2 wiring test: FameExporter.export() runs from the same
CampaignOrchestrator._advance_state() call site as CultureDriftExporter.export()
and FidelityExporter.export().

Mirrors tests/unit/domains/campaigns/test_fidelity_wiring.py's exact pattern,
extended to assert region_cultures, historical_drift, and entity_fame are all
populated from one _advance_state() call.
"""

from unittest.mock import MagicMock

from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
from src.domains.campaigns.state import EpisodeSummary, NarrativeLedgerEntry


def _make_manifest() -> CampaignManifest:
    return CampaignManifest(id="test_campaign", episodes=[MagicMock()])


def test_fame_wiring_advance_state_calls_fame_exporter_alongside_culture_and_fidelity():
    manifest = _make_manifest()
    orch = CampaignOrchestrator(manifest)

    # Pre-seed narrative_ledger with a quest_completed entry (Option B fame source)
    # attributed to a subject, and a calamity entry so region_cultures/historical_drift
    # are also populated by the same _advance_state() call.
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
    orch.state.narrative_ledger.append(
        NarrativeLedgerEntry(
            episode=0,
            tick=2,
            event_type="quest_completed",
            subject_id="hero_1",
            payload={},
            significance=0.7,
            entry_id="0:2:quest_completed:hero_1",
        )
    )

    final_state = MagicMock()
    final_state.entities = {}
    final_state.recent_world_events = []

    summary = EpisodeSummary(episode_index=0, completed_tick=10)
    orch._advance_state(final_state, summary)

    assert "r1" in orch.state.region_cultures
    assert "0:1:calamity:world" in orch.state.historical_drift
    assert "hero_1" in orch.state.entity_fame
    assert orch.state.entity_fame["hero_1"].derived_episode == 0
    assert orch.state.entity_fame["hero_1"].fame.fame > 0.0
