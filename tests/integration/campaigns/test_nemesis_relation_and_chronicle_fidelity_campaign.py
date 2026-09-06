"""Campaign-mode test coverage for idea 55 (nemesis relation formation, cross-episode),
idea 62 (Chronicle fidelity decay), and idea 53 (reputation inheritance with drifted parent
values) — TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS, M9 ticket 1, AC2 pieces B/C.

Uses real CampaignOrchestrator machinery and real Kernel ticks (frontier_living_world,
hero_guild_perspective, matching tests/integration/scenarios/test_campaign_runtime.py's own
established pattern), with scripted CampaignState injections where the real mechanism (nemesis
antagonism history, an old narrative event) cannot be reliably forced through emergent AI
behavior within a short tick_limit — the same "real production logic, scripted inputs" technique
test_campaign_runtime.py itself already uses (monkey-patching _build_initial_state,
directly mutating orch.state.social_memories) and this repo's own established precedent for
un-forceable emergent behavior (see investigation.md).
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True, scope="module")
def _warmup_catalog():
    from src.engine.behavior_consumers import _auto_init
    _auto_init()


def _make_spec(spec_id: str = "test_ep", tick_limit: int = 10, **kwargs):
    from src.scenarios.schema import SimulationScenarioDefinition

    defaults = {
        "id": spec_id,
        "world_composition": "frontier_living_world",
        "perspective": "hero_guild_perspective",
        "victory_conditions": [{"kind": "tick_limit", "value": tick_limit}],
    }
    defaults.update(kwargs)
    return SimulationScenarioDefinition(**defaults)


@pytest.mark.slow
def test_nemesis_relation_forms_from_repeated_antagonism_across_real_campaign_episodes():
    """Idea 55 (cross-episode): CampaignState.nemesis_relations forms once an entity has
    NEMESIS_EPISODE_COUNT=2 distinct episodes of antagonism in its social_memories.

    _advance_nemesis_relations() is real production logic (src/domains/campaigns/orchestrator.py)
    invoked directly against a real CampaignOrchestrator's own state -- not mocked. Called directly
    (rather than via a full run_episode()) because the real per-episode social-memory EXTRACTION
    (_extract_social_memories) would overwrite hand-injected interaction_history with whatever a
    short, real Kernel run naturally produces, which cannot be reliably guaranteed to include a
    "betrayed"/"conflict" interaction within a small tick budget.
    """
    from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
    from src.domains.campaigns.social_memory import SocialMemoryRecord, InteractionRecord

    manifest = CampaignManifest(id="test_nemesis_campaign", episodes=[_make_spec("ep0")], base_seed=0)
    orch = CampaignOrchestrator(manifest)

    protagonist_id, antagonist_id = 1, 2
    orch.state.social_memories[protagonist_id] = SocialMemoryRecord(
        entity_id=protagonist_id,
        interaction_history=(
            InteractionRecord(episode=0, tick=5, kind="betrayed", other_entity_id=antagonist_id, faction_id=None, magnitude=0.8),
            InteractionRecord(episode=1, tick=7, kind="conflict", other_entity_id=antagonist_id, faction_id=None, magnitude=0.8),
        ),
        relationship_scores={antagonist_id: -0.9},
    )

    assert orch.state.nemesis_relations == {}, "precondition: no nemesis relation before advancing"

    orch._advance_nemesis_relations(episode_index=2, tick=0)

    key = f"{protagonist_id}:{antagonist_id}"
    assert key in orch.state.nemesis_relations, "expected a nemesis relation to form after 2 distinct episodes of antagonism"
    relation = orch.state.nemesis_relations[key]
    assert relation.protagonist_id == protagonist_id
    assert relation.antagonist_id == antagonist_id
    assert relation.antagonism_count == 2
    assert relation.strength > 0.0


@pytest.mark.slow
def test_chronicle_fidelity_decays_across_real_campaign_episodes():
    """Idea 62: an event from episode 0 shows fidelity < 1.0 once a real 4-episode Campaign has
    run and a 2nd Era has formed, via the real FidelityExporter.export()/FidelityDeriver.derive()
    path (src/domains/fidelity/).

    ChronicleGrouper._group_eras() batches ERA_EPISODE_MIN=3 *worthy episodes* (episodes with at
    least one chronicle-worthy event), not raw episode indices -- confirmed via direct read
    (src/domains/chronicle/grouper.py:199-226) -- so 4 distinct episodes each need a real,
    chronicle-worthy narrative event for a 2nd Era to actually form. All 4 episodes run for real
    through the Kernel; the triggering narrative events themselves are injected directly (a real,
    short-tick_limit Kernel run cannot be guaranteed to naturally emit a chronicle-worthy event on
    a specific episode/tick) and FidelityExporter.export() -- real production logic, not mocked --
    is invoked directly against the resulting real narrative_ledger + ChronicleHierarchy, exactly
    as CampaignOrchestrator._advance_state() itself would.
    """
    from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
    from src.domains.campaigns.state import NarrativeLedgerEntry
    from src.domains.chronicle.grouper import ChronicleGrouper
    from src.domains.fidelity.exporter import FidelityExporter

    episodes = [_make_spec(f"ep{i}", tick_limit=10) for i in range(4)]
    manifest = CampaignManifest(id="test_fidelity_campaign", episodes=episodes, base_seed=0)
    orch = CampaignOrchestrator(manifest)

    for _ in range(4):
        orch.run_episode()  # 4 real episodes, real Kernel ticks

    entry_id = "0:5:faction_destroyed:99"
    for ep in range(4):
        orch.state.narrative_ledger.append(NarrativeLedgerEntry(
            episode=ep, tick=5, event_type="faction_destroyed", subject_id="99",
            payload={}, significance=0.9, entry_id=f"{ep}:5:faction_destroyed:99",
        ))

    hierarchy = ChronicleGrouper().group(list(orch.state.narrative_ledger))
    assert len(hierarchy.eras) >= 2, "expected a 2nd Era to form once 4 distinct worthy episodes exist"
    FidelityExporter.export(orch.state, hierarchy, episode_index=3)

    carry_forward = orch.state.historical_drift.get(entry_id)
    assert carry_forward is not None, f"expected {entry_id} to have a real derived FidelityCarryForward"
    assert carry_forward.fidelity.fidelity < 1.0, "episode-0 event must show real fidelity decay once a 2nd Era exists"


def test_reputation_inheritance_uses_already_drifted_parent_values():
    """Idea 53: idea 53's own mechanism (ReputationService.combine_public_reputation /
    V2EntityBuilder.birth_record) works correctly with campaign-drifted (non-default) parent
    reputation values, not just fixture defaults -- the genuinely new thing this Campaign-mode
    coverage adds beyond idea 53's own original unit test."""
    from src.systems.social_systems.reputation import ReputationService
    from src.core.builder import V2EntityBuilder

    parent_a_reputation = 1.6  # drifted upward from campaign-play heroism
    parent_b_reputation = 0.4  # drifted downward from campaign-play notoriety

    expected = ReputationService.combine_public_reputation(parent_a_reputation, parent_b_reputation)
    assert expected == 1.0

    child = (
        V2EntityBuilder(3)
        .location(0.0, 0.0)
        .birth_record(
            parent_a_entity_id=1,
            parent_b_entity_id=2,
            parent_a_public_reputation=parent_a_reputation,
            parent_b_public_reputation=parent_b_reputation,
        )
        .build()
    )
    assert child.social.public_reputation == expected
    assert parent_b_reputation < child.social.public_reputation < parent_a_reputation
