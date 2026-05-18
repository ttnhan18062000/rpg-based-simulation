import pytest
from unittest.mock import MagicMock, patch
from io import StringIO
import sys
from src_legacy.ui.cli.inspector import EntityInspector
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.enums import AIState, GoalType
from src_legacy.core.models.vectors import Vector2

def test_inspector_curated_output():
    # Setup mock entity with nested mocks
    entity = MagicMock(spec=Entity)
    entity.id = 1
    entity.identity = MagicMock()
    entity.identity.display_name = "Test Hero"
    entity.identity.tier = 1
    entity.identity.faction = "Highland"
    entity.identity.archetype = MagicMock()
    entity.identity.archetype.name = "Warrior"
    entity.identity.reputation = MagicMock()
    entity.identity.reputation.reputation_tags = ["Hero"]
    entity.identity.reputation.defender_score = 5.0
    entity.identity.reputation.heroism_score = 5.0
    entity.identity.reputation.trustworthiness = 5.0
    entity.identity.reputation.greed_score = 5.0
    entity.identity.reputation.threat_notoriety = 5.0
    entity.identity.reputation.cowardice_score = 5.0
    
    # Personality traits
    entity.mind = MagicMock()
    entity.mind.decision = MagicMock()
    entity.mind.decision.personality = MagicMock()
    entity.mind.decision.personality.aggression = 0.8  # Aggressive
    entity.mind.decision.personality.greed = 0.9       # Greedy
    entity.mind.decision.personality.caution = 0.1     # Reckless
    entity.mind.decision.personality.ambition = 0.9    # Ambitious
    entity.mind.decision.personality.curiosity = 0.8   # Curious
    
    entity.mind.decision.goal_scores = {
        GoalType.COMBAT: 1.5,
        GoalType.LOOT: 0.9,
        GoalType.EXPLORE: 0.2
    }
    
    entity.mind.routine = MagicMock()
    entity.mind.routine.sleep_debt = 0.1
    entity.mind.routine.hunger_level = 0.1
    entity.mind.routine.is_sleeping = False
    entity.mind.routine.active_start_hour = 8
    entity.mind.routine.active_end_hour = 20
    
    entity.mind.decision.ai_state = AIState.IDLE
    entity.mind.navigation = MagicMock()
    entity.mind.perception = MagicMock()
    entity.mind.strategic = MagicMock()
    entity.mind.strategic.projects = []
    entity.mind.strategic.directives = []
    entity.mind.strategic.concerns = []
    entity.mind.strategic.leads = []
    entity.mind.strategic.candidate_zones = []
    entity.mind.strategic.hypotheses = []
    entity.mind.strategic.contracts = []
    entity.mind.strategic.offers = []
    entity.mind.strategic.obligations = []
    entity.mind.strategic.recent_drivers = []
    entity.mind.strategic.current_objective_id = None
    entity.mind.strategic.last_capacity_profile = None
    entity.mind.strategic.interrupted_project_id = None
    
    entity.progression = MagicMock()
    entity.progression.level = 5
    
    entity.combat = MagicMock()
    entity.combat.hp = 100
    entity.combat.max_hp = 100
    
    entity.spatial = MagicMock()
    entity.spatial.pos = Vector2(10.0, 20.0)
    
    # Narrative log
    from src_legacy.core.aspects.mind import InterpretedEvent
    e1 = InterpretedEvent(tick=10, type="combat", impact=1.5, details={"desc": "Killed a Dragon"})
    entity.mind.narrative = MagicMock()
    entity.mind.narrative.memory_log = [e1]
    entity.mind.narrative.turning_points = []
    
    # Mock registry
    registry = MagicMock()
    registry._current_tick = 20
    
    # Capture output
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    
    try:
        EntityInspector.inspect_full(entity, registry)
    finally:
        sys.stdout = old_stdout
    
    output = mystdout.getvalue()
    
    # VERIFY: Curation requirements
    assert "WHO IS THIS?" in output
    assert "Aggressive" in output
    assert "Greedy" in output
    assert "Reckless" in output
    assert "Ambitious" in output
    assert "Curious" in output
    
    assert "LIKELY NEXT CHOICES" in output
    assert "1. COMBAT" in output
    assert "Dominant Drive" in output
    
    assert "ONGOING ARC" in output
    assert "MAJOR VICTORY" in output
    assert "Killed a Dragon" in output
