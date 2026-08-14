import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, PersonalityComponent,
    StrategicComponent, BiologicalComponent, CombatComponent, StaminaComponent,
    BuildingState
)
from src.core.strategic import BlockerState, LeadState, GoalKind
from src.core.builder import V2EntityBuilder
from src.core.updates import StrategicUpdate, EntityUpdate
from src.systems.strategic import StrategicIntelligenceSystem
from src.ai.goals import GoalRegistry
from src.ai.goals.scorers import (
    CombatEngageScorer, CombatRetreatScorer, RecoverScorer, ResolveBlockerScorer
)


@pytest.fixture
def base_state():
    return AuthoritativeState(tick=100, seed=42)


def test_combat_engage_scorer_no_threat(base_state):
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .location(0.0, 0.0)
              .identity(personality=PersonalityComponent(bravery=1.0))
              .build())
    scorer = CombatEngageScorer()
    score = scorer.score(entity, base_state)
    assert score.utility == 0.0


def test_combat_engage_scorer_threat_and_bravery_bias(base_state):
    # Setup state with threat
    hostile = (V2EntityBuilder(2)
               .kind("goblin")
               .location(2.0, 2.0)
               .build())
    
    # We must mock faction differences
    hostile = replace(hostile, identity=replace(hostile.identity, faction=2))
    
    brave_entity = (V2EntityBuilder(1)
                    .kind("hero")
                    .location(0.0, 0.0)
                    .identity(personality=PersonalityComponent(bravery=1.0))
                    .build())
                    
    coward_entity = (V2EntityBuilder(3)
                     .kind("hero")
                     .location(0.0, 0.0)
                     .identity(personality=PersonalityComponent(bravery=-1.0))
                     .build())

    # Add hostile and entities to state
    state = replace(base_state, entities={1: brave_entity, 2: hostile, 3: coward_entity})
    
    scorer = CombatEngageScorer()
    
    score_brave = scorer.score(brave_entity, state)
    score_coward = scorer.score(coward_entity, state)
    
    assert score_brave.utility > score_coward.utility
    assert score_brave.target_id == "2"
    assert score_brave.target_pos == (2.0, 2.0)


def test_combat_retreat_scorer(base_state):
    # Full HP, no threat -> 0 retreat utility
    entity_healthy = (V2EntityBuilder(1)
                      .kind("hero")
                      .location(0.0, 0.0)
                      .build())
    scorer = CombatRetreatScorer()
    score_healthy = scorer.score(entity_healthy, base_state)
    assert score_healthy.utility == 0.0

    # Low HP, threat present -> high retreat utility, influenced by bravery
    hostile = (V2EntityBuilder(2)
               .kind("goblin")
               .location(2.0, 2.0)
               .build())
    hostile = replace(hostile, identity=replace(hostile.identity, faction=2))
    
    brave_entity = (V2EntityBuilder(1)
                    .kind("hero")
                    .location(0.0, 0.0)
                    .combat(hp=10, max_hp=100)
                    .identity(personality=PersonalityComponent(bravery=1.0))
                    .build())
                    
    coward_entity = (V2EntityBuilder(3)
                     .kind("hero")
                     .location(0.0, 0.0)
                     .combat(hp=10, max_hp=100)
                     .identity(personality=PersonalityComponent(bravery=-1.0))
                     .build())

    state = replace(base_state, entities={1: brave_entity, 2: hostile, 3: coward_entity}, town_center=(0.0, 0.0))
    
    score_brave = scorer.score(brave_entity, state)
    score_coward = scorer.score(coward_entity, state)
    
    assert score_coward.utility > score_brave.utility
    assert score_brave.target_id == "town_center"
    assert score_brave.target_pos == (0.0, 0.0)


def test_recover_scorer(base_state):
    # Perfect shape -> 0 recover utility
    entity_perfect = (V2EntityBuilder(1)
                      .kind("hero")
                      .location(0.0, 0.0)
                      .build())
    scorer = RecoverScorer()
    score_perfect = scorer.score(entity_perfect, base_state)
    assert score_perfect.utility == 0.0

    # Low HP/stamina -> high recover utility, targets Inn if present
    entity_weak = (V2EntityBuilder(1)
                   .kind("hero")
                   .location(0.0, 0.0)
                   .combat(hp=20, max_hp=100)
                   .build())
    # Mock low stamina
    entity_weak = replace(entity_weak, stamina=StaminaComponent(current=10.0, max_stamina=100.0))

    inn = BuildingState(id=10, kind="inn", position=(5.0, 5.0))
    state_with_inn = replace(base_state, buildings={10: inn})
    
    score = scorer.score(entity_weak, state_with_inn)
    assert score.utility > 0.0
    assert score.target_id == "10"
    assert score.target_pos == (5.0, 5.0)


def test_resolve_blocker_scorer(base_state):
    # No blockers -> 0 utility
    entity_no_blockers = (V2EntityBuilder(1)
                          .kind("hero")
                          .location(0.0, 0.0)
                          .build())
    scorer = ResolveBlockerScorer()
    score = scorer.score(entity_no_blockers, base_state)
    assert score.utility == 0.0

    # Active access blocker -> high utility, resolves to subject coordinates
    blocker = BlockerState(id="b1", kind="access", subject="(3.0, 4.0)", severity=0.8)
    entity_blocked = (V2EntityBuilder(1)
                      .kind("hero")
                      .location(0.0, 0.0)
                      .strategic(blockers={"b1": blocker})
                      .build())
                      
    score_blocked = scorer.score(entity_blocked, base_state)
    assert score_blocked.utility == 80.0
    assert score_blocked.target_pos == (3.0, 4.0)


# ── target_position fallback, end-to-end (TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG) ──
# TownScorer/RecoverScorer(no-inn)/ResolveBlockerScorer(non-coordinate blocker id) all set
# target_id to a value TacticalDecisionSystem._resolve_target_position can't parse into a
# position (a bare string like "town_center", or a blocker id like "b1"). Prior to the fix, a
# project built from any of these scorers' GoalScores would win the goal competition but the
# entity would never actually navigate anywhere -- these tests drive the real production path
# (StrategicIntelligenceSystem.evaluate_strategic_intent -> TacticalDecisionSystem
# .evaluate_entity_intent) end-to-end to confirm real navigation now results.

def test_town_return_project_now_produces_real_navigation():
    from src.engine.tactical import TacticalDecisionSystem

    entity = (V2EntityBuilder(1)
              .kind("hero")
              .location(50.0, 50.0)
              .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
              .lifecycle(active=True)
              .biological(hunger=90.0, sleep_debt=90.0)
              .build())
    state = AuthoritativeState(tick=10, seed=1, entities={1: entity}, town_center=(0.0, 0.0))

    strat_upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
    assert strat_upd.projects_add_or_update, "TownScorer should have won and created a project"
    project = strat_upd.projects_add_or_update[0]
    assert project.kind == GoalKind.TOWN_RETURN
    obj = project.objectives[0]
    assert obj.target == "town_center"
    assert obj.target_position == (0.0, 0.0)

    entity_with_project = (V2EntityBuilder(1)
                            .kind("hero")
                            .location(50.0, 50.0)
                            .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
                            .lifecycle(active=True)
                            .biological(hunger=90.0, sleep_debt=90.0)
                            .strategic(projects={project.id: project}, current_project_id=project.id,
                                       current_objective_id=obj.id)
                            .build())
    state2 = AuthoritativeState(tick=10, seed=1, entities={1: entity_with_project}, town_center=(0.0, 0.0))

    tac_upd = TacticalDecisionSystem.evaluate_entity_intent(state2, entity_with_project, neighbors=[])
    assert tac_upd.navigation is not None and tac_upd.navigation.target_set == (0.0, 0.0), (
        "town_return objective did not resolve a real navigation target — "
        "the target_position fallback did not fire"
    )


def test_deterministic_tie_breaking(base_state):
    # Setup state
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .location(0.0, 0.0)
              .build())
              
    # Fetch all registered goal scores
    scores = GoalRegistry.get_all_scores(entity, base_state)
    assert len(scores) > 0
    
    # We can force identical utility by modifying them, then sort
    from src.ai.goals.base import GoalScore
    score_a = GoalScore(kind="b_goal", utility=50.0, target_id="t", target_pos=(0, 0))
    score_b = GoalScore(kind="a_goal", utility=50.0, target_id="t", target_pos=(0, 0))
    
    list_scores = [score_a, score_b]
    list_scores.sort(key=lambda x: (-x.utility, x.kind))
    
    # Kind "a_goal" must be first due to alphabetical order tie-breaker
    assert list_scores[0].kind == "a_goal"
    assert list_scores[1].kind == "b_goal"


def test_integration_strategic_project_selection(base_state):
    # Setup state where combat_engage should be the highest scorer
    hostile = (V2EntityBuilder(2)
               .kind("goblin")
               .location(1.0, 1.0)
               .build())
    hostile = replace(hostile, identity=replace(hostile.identity, faction=2))
    
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .location(0.0, 0.0)
              .identity(personality=PersonalityComponent(bravery=1.0))
              .build())
              
    state = replace(base_state, entities={1: entity, 2: hostile})
    
    # Evaluate strategic intent
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    assert len(update.projects_add_or_update) > 0
    
    project = update.projects_add_or_update[0]
    assert project.kind == "combat_engage"
    assert project.active_objective_id is not None
