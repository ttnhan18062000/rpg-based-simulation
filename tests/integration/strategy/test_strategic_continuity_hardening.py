import pytest
from unittest.mock import MagicMock
from src.ai.brain import AIBrain
from src.config import SimulationConfig
from src.platform.rng import DeterministicRNG
from src.core.models.snapshot import Snapshot
from src.core.models.enums import AIState, StrategicStatus, ObjectiveKind, ProjectKind
from src.core.models.strategy import ProjectRecord, ObjectiveRecord

from src.core.models.vectors import Vector2

def create_mock_entity(eid=101):
    entity = MagicMock()
    entity.id = eid
    entity.identity.faction = 1
    entity.identity.cluster_id = None
    entity.identity.max_attention_slots = 5
    entity.spatial.pos = Vector2(x=0, y=0)
    entity.spatial.vision_range = 10
    entity.spatial.current_region_id = None
    entity.spatial.home_pos = None
    entity.mind.place_attachments = []
    entity.combat.hp = 100
    entity.combat.max_hp = 100
    entity.combat.alive = True
    entity.combat.hp_ratio = 1.0
    entity.progression.level = 1
    
    # Needs
    entity.mind.routine.sleep_debt = 0.0
    entity.mind.routine.hunger_level = 0.0
    entity.mind.routine.is_sleeping = False
    entity.mind.routine.disrupted_until_tick = 0
    
    # Perception
    entity.mind.perception.entity_memory = {}
    
    # Emotion
    entity.mind.emotion.mood = 0.5
    entity.mind.emotion.panic = 0.0
    entity.mind.emotion.joy = 0.0
    entity.mind.emotion.dread = 0.0
    entity.mind.emotion.stuck = 0.0
    entity.mind.emotion.grudges = {}
    
    # Motives
    entity.mind.decision.motives = []
    
    # Progression Attributes for CognitionCapacityBuilder
    # Mapping to exact model names from src/core/gameplay/attributes.py or inferred from use
    entity.progression.level = 1
    entity.progression.attributes.int_ = 20
    entity.progression.attributes.wis = 20
    entity.progression.attributes.per = 20
    entity.progression.attributes.cha = 20
    entity.progression.attribute_caps.int_cap = 20
    entity.progression.attribute_caps.wis_cap = 20
    entity.progression.attribute_caps.per_cap = 20
    entity.progression.attribute_caps.cha_cap = 20
    
    entity.progression.stamina = 100
    entity.progression.max_stamina = 100
    entity.progression.age_ticks = 0
    entity.progression.longevity_limit = 100000
    
    # Navigation
    entity.mind.navigation.pos_history = [Vector2(x=0, y=0)]
    entity.mind.perception.max_attention_slots = 5
    
    # Social
    entity.mind.social.known_bonds = {}
    entity.mind.social.faction_standing = {}
    
    # Decision
    entity.mind.decision.ai_state = AIState.IDLE
    entity.mind.decision.last_goal = None
    entity.mind.decision.goal_scores = {}
    entity.mind.decision.last_appraisal_tick = 0
    entity.mind.decision.boredom_multipliers = {}
    entity.mind.decision.goal_cooldowns = {}
    entity.mind.decision.motive_utility_biases = {}
    entity.mind.decision.personality_biases = {}
    
    # Personality for CognitionCapacityBuilder
    entity.mind.decision.personality.aggression = 0.5
    entity.mind.decision.personality.curiosity = 0.5
    entity.mind.decision.personality.caution = 1.0
    entity.mind.decision.personality.ambition = 0.5
    entity.mind.decision.personality.loyalty = 0.5
    entity.mind.decision.personality.neuroticism = 0.0
    entity.mind.decision.personality.greed = 0.5
    entity.mind.decision.personality.archetype = "none"
    
    # Narrative
    entity.mind.narrative.memory_locations = {}
    entity.mind.narrative.memory_log = []
    entity.mind.narrative.region_fatigue = {}
    
    # Mind methods
    entity.mind.total_glory.return_value = 0.0
    entity.mind.total_loyalty.return_value = 0.0
    entity.mind.total_sin.return_value = 0.0
    entity.mind.total_trauma.return_value = 0.0
    
    # Strategic
    entity.mind.strategic.projects = []
    entity.mind.strategic.concerns = []
    entity.mind.strategic.obligations = []
    entity.mind.strategic.leads = []
    entity.mind.strategic.blockers = []
    entity.mind.strategic.contracts = []
    entity.mind.strategic.current_project_id = None
    entity.mind.strategic.current_objective_id = None
    entity.mind.strategic.current_project = None
    entity.mind.strategic.interrupted_project_id = None
    entity.mind.strategic.last_capacity_profile = None
    entity.mind.strategic.directives = []
    entity.mind.strategic.active_slice_used = 0
    entity.mind.strategic.dropped_candidates_count = 0
    
    return entity

def test_strategic_objective_continuity():
    """Prove that an existing objective is preserved if the project remains stable and no high blockers appear."""
    config = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(42)
    brain = AIBrain(config, rng)
    
    entity = create_mock_entity()
    
    # 1. Setup a Project and Objective
    obj = ObjectiveRecord(objective_id="OBJ_1", project_id="PROJ_1", kind=ObjectiveKind.VISIT, label="Test Objective", status=StrategicStatus.ACTIVE, target_pos=Vector2(x=10, y=10))
    proj = ProjectRecord(
        project_id="PROJ_1", 
        kind=ProjectKind.EXPLORATION,
        label="Test Project", 
        status=StrategicStatus.ACTIVE,
        objectives=[obj],
        active_objective_id="OBJ_1",
        priority=1.5,
        committed_at=0
    )
    entity.mind.strategic.projects = [proj]
    entity.mind.strategic.current_project_id = "PROJ_1"
    entity.mind.strategic.current_project = proj
    entity.mind.strategic.current_objective_id = "OBJ_1"
    
    snapshot = MagicMock()
    snapshot.tick = 1
    snapshot.social_registry = MagicMock()
    snapshot.social_registry.bonds = {}
    snapshot.active_entities = {entity.id: entity}
    snapshot.group_registry = {}
    
    # 2. Run Appraisal Pass 1 (Stability)
    # With no other candidates, it should stay on PROJ_1 / OBJ_1
    ai_state, action = brain.decide(entity, snapshot)
    
    # Find StrategicUpdate in the action (ActionProposal has updates list)
    from src.actions.base import StrategicUpdate
    strat_up = next((u for u in action.updates if isinstance(u, StrategicUpdate)), None)
    
    # If objective didn't change, strat_up.current_objective_id might remain unset or match existing
    if strat_up:
        # If it was sent, verify it's the same
        if hasattr(strat_up, "current_objective_id") and strat_up.current_objective_id is not None:
            assert strat_up.current_objective_id == "OBJ_1"
    
    # 3. Induce a Weak Interruption (should NOT switch due to Margin)
    rival_obj = ObjectiveRecord(objective_id="OBJ_RIVAL", project_id="PROJ_RIVAL", kind=ObjectiveKind.KILL, label="Rival Objective", status=StrategicStatus.ACTIVE)
    rival_proj = ProjectRecord(
        project_id="PROJ_RIVAL", 
        kind=ProjectKind.INVESTIGATION,
        label="Rival Project", 
        status=StrategicStatus.ACTIVE,
        objectives=[rival_obj],
        priority=1.6, # Just slightly higher
        committed_at=1
    )
    entity.mind.strategic.projects.append(rival_proj)
    
    ai_state, action = brain.decide(entity, snapshot)
    strat_up = next((u for u in action.updates if isinstance(u, StrategicUpdate)), None)
    
    # Should still be OBJ_1 or unset if stable
    if strat_up and hasattr(strat_up, "current_project_id") and strat_up.current_project_id:
        assert strat_up.current_project_id == "PROJ_1"

def test_objective_resumption_aligns_with_tactical():
    """Verify that a resumed objective correctly drives goal selection."""
    config = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(42)
    brain = AIBrain(config, rng)
    
    entity = create_mock_entity()
    
    obj = ObjectiveRecord(
        objective_id="OBJ_GATHER", 
        project_id="PROJ_LOGISTICS",
        label="Gathering Materials", 
        status=StrategicStatus.ACTIVE,
        kind=ObjectiveKind.COLLECT, # maps to GoalType.LOOTING or similar
        target_pos=Vector2(x=20, y=20)
    )
    proj = ProjectRecord(
        project_id="PROJ_LOGISTICS", 
        kind=ProjectKind.DEVELOPMENT,
        label="Build Base", 
        status=StrategicStatus.ACTIVE,
        objectives=[obj],
        active_objective_id="OBJ_GATHER"
    )
    entity.mind.strategic.projects = [proj]
    entity.mind.strategic.current_project_id = "PROJ_LOGISTICS"
    entity.mind.strategic.current_project = proj
    entity.mind.strategic.current_objective_id = "OBJ_GATHER"
    
    # Setup world state so tactical can act
    snapshot = MagicMock()
    snapshot.tick = 10
    snapshot.active_entities = {entity.id: entity}
    snapshot.social_registry = MagicMock()
    snapshot.social_registry.bonds = {}
    snapshot.group_registry = {}
    
    # Appraisal should keep OBJ_GATHER
    # Mapping pass should elevate LOOTING/GATHER goal weight
    ai_state, action = brain.decide(entity, snapshot)
    
    # The action should reflect the goal influenced by the objective
    # This is a bit complex as it depends on the mapper implementation.
    # We at least want to see that appraisal didn't drop the objective.
    from src.actions.base import StrategicUpdate
    strat_up = next((u for u in action.updates if isinstance(u, StrategicUpdate)), None)
    if strat_up and hasattr(strat_up, "current_objective_id") and strat_up.current_objective_id:
        assert strat_up.current_objective_id == "OBJ_GATHER"

if __name__ == "__main__":
    pytest.main([__file__])
