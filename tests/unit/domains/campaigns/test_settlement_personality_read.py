"""
tests/unit/domains/campaigns/test_settlement_personality_read.py
────────────────────────────────────────────────────────────────────────────────
Tests for CampaignOrchestrator.describe_settlement_personality() (idea 61 read-side
consumer, TCK-20260904-SETTLEMENT-CULTURE-READ).

Verifies the new method is a pure read over already-populated CampaignState:
never touches _build_initial_state()/_advance_state(), never mutates
episode_index/persistent_entities/narrative_ledger.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
from src.domains.culture.model import CultureCarryForward, CultureState
from src.domains.culture.settlement_personality import SettlementPersonalityDescriptor


def _make_orchestrator(n_episodes: int = 1) -> CampaignOrchestrator:
    episodes = [MagicMock() for _ in range(n_episodes)]
    manifest = CampaignManifest(id="camp_personality", episodes=episodes, base_seed=0)
    return CampaignOrchestrator(manifest)


def test_describe_settlement_personality_with_populated_region_cultures():
    orchestrator = _make_orchestrator()
    culture = CultureState(fatalism=0.8)
    orchestrator.state.region_cultures["r1"] = CultureCarryForward(
        region_id="r1", culture=culture, derived_episode=0
    )

    result = orchestrator.describe_settlement_personality("r1")

    assert isinstance(result, SettlementPersonalityDescriptor)
    assert result.is_neutral is False
    assert "fatalistic" in result.traits


def test_describe_settlement_personality_with_unknown_region_returns_neutral_descriptor():
    orchestrator = _make_orchestrator()

    result = orchestrator.describe_settlement_personality("no_such_region")

    assert isinstance(result, SettlementPersonalityDescriptor)
    assert result.is_neutral is True
    assert result.traits == ()


def test_describe_settlement_personality_does_not_mutate_campaign_state():
    orchestrator = _make_orchestrator()
    culture = CultureState(hero_veneration=0.7)
    orchestrator.state.region_cultures["r1"] = CultureCarryForward(
        region_id="r1", culture=culture, derived_episode=0
    )

    episode_index_before = orchestrator.state.episode_index
    persistent_entities_before = dict(orchestrator.state.persistent_entities)
    narrative_ledger_before = list(orchestrator.state.narrative_ledger)

    orchestrator.describe_settlement_personality("r1")
    orchestrator.describe_settlement_personality("unknown_region")

    assert orchestrator.state.episode_index == episode_index_before
    assert orchestrator.state.persistent_entities == persistent_entities_before
    assert orchestrator.state.narrative_ledger == narrative_ledger_before
