"""Integration test for CampaignOrchestrator progression plan export wiring (E61B)."""

from unittest.mock import MagicMock

from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
from src.domains.campaigns.progression_plan import BuildGoal, ProgressionPlan
from src.domains.campaigns.state import EpisodeSummary


def _make_manifest() -> CampaignManifest:
    return CampaignManifest(id="test_campaign", episodes=[MagicMock()])


def _make_mock_entity(entity_id: int, alive: bool) -> MagicMock:
    e = MagicMock()
    e.identity.evolution_level = 3
    e.identity.evolution_points = 0
    e.identity.faction = 1
    e.lifecycle.active = alive
    e.social.public_reputation = 1.0
    e.equipment.slots = {}
    e.equipment.durability = {}
    return e


def _make_plan(entity_id: int) -> ProgressionPlan:
    return ProgressionPlan(
        entity_id=entity_id,
        goal_queue=(
            BuildGoal(
                goal_id="g1",
                target_route_family="QUEST_OPPORTUNITY",
                target_item_id=None,
                target_level=5,
                status="pending",
            ),
        ),
        milestone_checks=(),
        revision_triggers=(),
        created_episode=0,
        last_revised_episode=0,
    )


def test_orchestrator_exports_plan_at_episode_end():
    """After _advance_state(): alive entity plan kept; dead entity plan dropped."""
    manifest = _make_manifest()
    orch = CampaignOrchestrator(manifest)

    # Pre-seed plans: entity 1 alive, entity 2 dead
    plan_alive = _make_plan(entity_id=1)
    plan_dead = _make_plan(entity_id=2)
    orch.state.progression_plans[1] = plan_alive
    orch.state.progression_plans[2] = plan_dead

    final_state = MagicMock()
    final_state.entities = {
        1: _make_mock_entity(1, alive=True),
        2: _make_mock_entity(2, alive=False),
    }
    final_state.recent_world_events = []

    summary = EpisodeSummary(episode_index=0, completed_tick=10)
    orch._advance_state(final_state, summary)

    # Alive entity plan persists
    assert 1 in orch.state.progression_plans
    assert orch.state.progression_plans[1] == plan_alive

    # Dead entity plan is dropped
    assert 2 not in orch.state.progression_plans
