import pytest
from src_legacy.core.logic.routine_service import RoutineService
from src_legacy.core.models.enums import GoalType
from unittest.mock import MagicMock

def test_routine_service_sleep_bias():
    entity = MagicMock()
    # Mock routine state
    entity.mind.routine.sleep_debt = 0.8
    entity.mind.routine.hunger_level = 0.1
    entity.mind.routine.active_start_hour = 8
    entity.mind.routine.active_end_hour = 22
    entity.mind.routine.disrupted_until_tick = 0
    entity.mind.emotion.panic = 0.0
    entity.mind.routine_profiles = []
    entity.mind.place_attachments = []
    
    # Active hour (12:00)
    biases = RoutineService.calculate_routine_biases(entity, 12, 100)
    
    # Sleep debt 0.8 is above 0.5 threshold
    assert GoalType.SLEEP in biases
    assert biases[GoalType.SLEEP] > 1.0

def test_routine_service_forced_rest_during_off_hours():
    entity = MagicMock()
    entity.mind.routine.sleep_debt = 0.2
    entity.mind.routine.hunger_level = 0.1
    entity.mind.routine.active_start_hour = 8
    entity.mind.routine.active_end_hour = 22
    entity.mind.routine.disrupted_until_tick = 0
    entity.mind.emotion.panic = 0.0
    entity.mind.routine_profiles = []
    entity.mind.place_attachments = []
    
    # Off hour (2:00 AM)
    biases = RoutineService.calculate_routine_biases(entity, 2, 100)
    
    assert GoalType.SLEEP in biases
    assert biases[GoalType.SLEEP] == 2.0 # Night bonus
    assert biases[GoalType.COMBAT] == 0.6 # Night penalty

def test_routine_service_hunger_bias():
    entity = MagicMock()
    entity.mind.routine.sleep_debt = 0.1
    entity.mind.routine.hunger_level = 0.9
    entity.mind.routine.active_start_hour = 8
    entity.mind.routine.active_end_hour = 22
    entity.mind.routine.disrupted_until_tick = 0
    entity.mind.emotion.panic = 0.0
    entity.mind.routine_profiles = []
    entity.mind.place_attachments = []
    
    biases = RoutineService.calculate_routine_biases(entity, 12, 100)
    
    assert GoalType.EAT in biases
    assert biases[GoalType.EAT] > 3.0
    assert GoalType.LOOT in biases
    assert biases[GoalType.LOOT] > 1.0 # Hunger drives looting for food
