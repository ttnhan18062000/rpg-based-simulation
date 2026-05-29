import pytest
from src.core.cognition import HabitMemory

def test_habit_memory_model():
    model = HabitMemory()
    assert model.patterns == {}
