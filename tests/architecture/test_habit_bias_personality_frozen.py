"""
tests/architecture/test_habit_bias_personality_frozen.py

TCK-20260831-HABIT-BIAS-WIRING: architecture guard proving the habit-bias-into-ActionStyle
wiring introduced no live mutation path for PersonalityComponent. There is no `_delta`/`_set`
update field for personality anywhere in EntityUpdate (confirmed no PersonalityUpdate type
exists), and this wiring must not invent one -- tactical.py/movement.py only shadow a local
`style` variable fed by a live re-derivation; they never write back to CombatComponent or
PersonalityComponent.
"""
import inspect

from src.core.state import PersonalityComponent
from src.core import updates as updates_module
from src.engine import tactical as tactical_module
from src.engine import movement as movement_module


def test_no_personality_update_type_exists():
    assert not hasattr(updates_module, "PersonalityUpdate")
    assert "PersonalityUpdate" not in inspect.getsource(updates_module)


def test_personality_component_stays_frozen_dataclass():
    assert PersonalityComponent.__dataclass_params__.frozen is True


def test_habit_bias_wiring_never_constructs_personality_component():
    tactical_source = inspect.getsource(tactical_module.TacticalDecisionSystem.evaluate_entity_intent)
    movement_source = inspect.getsource(movement_module.MovementSystem.resolve_move)
    assert "PersonalityComponent(" not in tactical_source
    assert "PersonalityComponent(" not in movement_source
