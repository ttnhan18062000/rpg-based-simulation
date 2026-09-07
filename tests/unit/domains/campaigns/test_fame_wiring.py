"""AC2 wiring test: FameExporter.export() runs from the same
CampaignOrchestrator._advance_state() call site as CultureDriftExporter.export()
and FidelityExporter.export().

Mirrors tests/unit/domains/campaigns/test_fidelity_wiring.py's exact pattern,
extended to assert region_cultures, historical_drift, and entity_fame are all
populated from one _advance_state() call.
"""

from unittest.mock import MagicMock

from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
from src.domains.campaigns.state import EntityCarryForward, EpisodeSummary, NarrativeLedgerEntry
from src.domains.fame.model import FameCarryForward, FameState


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


# --- TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING: entity_legend_facts bridge ------------------
# Import-side counterpart to the export-side test above: proves _build_initial_state() itself
# (not just a hand-constructed AuthoritativeState) turns CampaignState.entity_fame into the
# bridged entity_legend_facts snapshot via the real LegendFactService.for_entity() threshold gate.


def test_build_initial_state_bridges_entity_fame_above_threshold_into_entity_legend_facts():
    manifest = _make_manifest()
    orch = CampaignOrchestrator(manifest)

    # One subject above FAME_THRESHOLD (0.5), one below -- proves the bridge reuses
    # LegendFactService.for_entity()'s own gate rather than dumping raw fame unconditionally.
    orch.state.entity_fame["hero_1"] = FameCarryForward(
        subject_id="hero_1", fame=FameState(fame=0.7), derived_episode=0,
    )
    orch.state.entity_fame["hero_2"] = FameCarryForward(
        subject_id="hero_2", fame=FameState(fame=0.2), derived_episode=0,
    )
    # An alive carry-forward entity is required for _build_initial_state() to reach the bridge
    # logic at all -- with none, it early-returns a bare fresh AuthoritativeState (episode-0 path).
    orch.state.persistent_entities[1] = EntityCarryForward(
        entity_id=1, level=1, xp=0, equipment={}, reputation=1.0, alive=True,
    )

    state = orch._build_initial_state(episode_seed=1)

    assert "hero_1" in state.entity_legend_facts
    assert state.entity_legend_facts["hero_1"].fame == 0.7
    assert "hero_2" not in state.entity_legend_facts
