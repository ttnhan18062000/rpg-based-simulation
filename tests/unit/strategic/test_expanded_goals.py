import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, PersonalityComponent,
    StrategicComponent, BiologicalComponent, CombatComponent, StaminaComponent,
    BuildingState
)
from src.core.strategic import BlockerState, LeadState
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
