import pytest
from unittest.mock import MagicMock, patch
from io import StringIO
import sys
from src.ui.cli.inspector import EntityInspector
from src.core.entities.entity import Entity
from src.core.models.enums import AIState, GoalType
from src.core.models.vectors import Vector2

def test_inspector_curated_output():
    # Setup mock entity with nested mocks
    entity = MagicMock(spec=Entity)
    entity.id = 1
    entity.identity = MagicMock()
    entity.identity.display_name = "Test Hero"
    entity.identity.tier = 1
    entity.identity.faction = "Highland"
    
    # Personality labels
    entity.identity.archetype = MagicMock()
    entity.identity.archetype.name = "SLAYER"
    entity.identity.openness = 0.8 # Creative
    entity.identity.conscientiousness = 0.2 # Easygoing
    entity.identity.extraversion = 0.5 # Average
    entity.identity.agreeableness = 0.9 # Compassionate
    entity.identity.neuroticism = 0.1 # Resilient
    
    # Goal scores
    entity.mind = MagicMock()
    entity.mind.decision = MagicMock()
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
    
    entity.mind.navigation = MagicMock()
    entity.mind.perception = MagicMock()
    
    entity.progression = MagicMock()
    entity.progression.level = 5
    
    entity.combat = MagicMock()
    entity.combat.hp = 100
    entity.combat.max_hp = 100
    
    entity.spatial = MagicMock()
    entity.spatial.pos = Vector2(10.0, 20.0)
    
    # Narrative log
    from src.core.aspects.mind import InterpretedEvent
    e1 = InterpretedEvent(tick=10, type="combat", impact=1.2, details={"desc": "Killed a Dragon"})
    entity.mind.narrative = MagicMock()
    entity.mind.narrative.memory_log = [e1]
    
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
    assert "Creative" in output
    assert "Easygoing" in output
    
    assert "LIKELY NEXT CHOICES" in output
    assert "1. COMBAT" in output
    assert "Dominant Drive" in output
    
    assert "ONGOING ARC" in output
    assert "MAJOR VICTORY" in output
    assert "Killed a Dragon" in output
