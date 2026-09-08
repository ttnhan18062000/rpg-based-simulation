"""3-episode integration test for the Progression Planner (E61D, AC5).

Episode 0: entity 1 alive (level 1, mentor entity 2 alive) → initial plan generated.
Episode 1: entity 1 alive (level 3), entity 2 still alive → plan carried, no revision.
Episode 2: entity 1 alive (level 4), entity 2 dead → mentor_dead trigger fires,
           plan revised, plan_revision NarrativeLedgerEntry added.
"""

from unittest.mock import MagicMock, patch

from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
from src.domains.campaigns.social_memory import SocialMemoryRecord
from src.domains.campaigns.state import EpisodeSummary


def _make_manifest(n_episodes: int = 3) -> CampaignManifest:
    # TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY: _build_initial_state() now really
    # compiles spec.world_composition (WorldRepository + WorldCompiler), so each
    # episode spec needs a real string world_id -- a bare MagicMock's
    # .world_composition is another MagicMock and fails world-id validation.
    episodes = []
    for _ in range(n_episodes):
        ep = MagicMock()
        ep.world_composition = "unit_faction_tension"
        episodes.append(ep)
    return CampaignManifest(id="prog_test", episodes=episodes)


def _make_entity(entity_id: int, level: int, alive: bool) -> MagicMock:
    e = MagicMock()
    e.identity.evolution_level = level
    e.identity.evolution_points = 0
    e.identity.faction = 1
    e.lifecycle.active = alive
    e.social.public_reputation = 1.0
    e.equipment.slots = {}
    e.equipment.durability = {}
    return e


def _run_episode(orch: CampaignOrchestrator, entities: dict, tick: int = 10) -> EpisodeSummary:
    final_state = MagicMock()
    final_state.entities = entities
    final_state.recent_world_events = []
    mock_svc = MagicMock()
    mock_svc.final_state = final_state
    mock_svc.tick = tick
    with patch("src.engine.scenario_runtime.ScenarioRuntimeService", return_value=mock_svc):
        return orch.run_episode()


def test_hero_pursues_craft_upgrade_across_three_episodes():
    """
    Episode 0: both alive → persistent_entities seeded.
    Episode 1: entity 2 dies → _advance_state marks entity 2 dead in persistent_entities.
    Episode 2: _build_initial_state detects dead mentor → revision fires.

    Revision fires in _build_initial_state() of the episode AFTER the mentor dies,
    because persistent_entities is updated by _advance_state() at episode end.
    """
    orch = CampaignOrchestrator(_make_manifest(n_episodes=3))

    # Episode 0: both alive → persistent_entities populated with both alive.
    _run_episode(orch, {
        1: _make_entity(1, level=1, alive=True),
        2: _make_entity(2, level=5, alive=True),
    })

    # Episode 1: entity 2 dies.
    # _build_initial_state (start of ep 1) sees entity 2 still alive → no revision.
    # _advance_state (end of ep 1) marks persistent_entities[2].alive = False.
    _run_episode(orch, {
        1: _make_entity(1, level=3, alive=True),
        2: _make_entity(2, level=5, alive=False),
    })

    # Inject mentor relationship AFTER episode 1's _advance_state has run.
    # SocialMemoryExporter.export() from mock entities produces empty relationship_scores;
    # injecting here ensures _build_initial_state for episode 2 sees {2: 0.9}.
    orch.state.social_memories[1] = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={2: 0.9},
    )

    # Episode 2: _build_initial_state now sees persistent_entities[2].alive=False
    # and social_memories[1].relationship_scores={2: 0.9} → mentor_dead trigger fires.
    _run_episode(orch, {
        1: _make_entity(1, level=4, alive=True),
    })

    # AC1: entity 1 has a plan
    assert 1 in orch.state.progression_plans
    plan = orch.state.progression_plans[1]
    assert plan is not None
    assert len(plan.goal_queue) > 0

    # AC2: the plan was revised — craft_upgrade moved to tail as blocked
    blocked = [g for g in plan.goal_queue if g.status == "blocked"]
    assert len(blocked) >= 1
    assert blocked[0].target_route_family == "craft_upgrade"

    # AC3: narrative_ledger contains a plan_revision entry for entity 1
    revision_entries = [
        e for e in orch.state.narrative_ledger
        if e.event_type == "plan_revision"
    ]
    assert len(revision_entries) >= 1
    assert revision_entries[0].subject_id == "1"
