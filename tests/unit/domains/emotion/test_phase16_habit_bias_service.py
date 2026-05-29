import pytest
from src.core.cognition import HabitMemory
from src.domains.emotion.habit_service import HabitBiasService

def test_habit_bias_service():
    memory = HabitMemory(patterns={"crafting": 0.5})
    
    # Successful outcome increases bias
    updated = HabitBiasService.record_outcome(memory, "crafting", success=True)
    assert updated.patterns["crafting"] > 0.5
    
    # Failed outcome decreases bias
    updated_failed = HabitBiasService.record_outcome(memory, "crafting", success=False)
    assert updated_failed.patterns["crafting"] < 0.5
