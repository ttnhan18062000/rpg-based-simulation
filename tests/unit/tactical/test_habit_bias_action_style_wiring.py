"""
tests/unit/tactical/test_habit_bias_action_style_wiring.py

TCK-20260831-HABIT-BIAS-WIRING (Step 4a): TacticalDecisionSystem.evaluate_entity_intent's
kiting-distance branch re-derives ActionStyle live from habit-biased bravery when
ENABLE_HABIT_BIAS_ACTION_STYLE is ON, and stays bit-identical to the frozen construction-time
ActionStyle when the flag is OFF (the default). Mirrors
tests/unit/combat/test_tactical_legality.py::test_tactical_blocked_kite's entity setup (the real
kiting-distance consumer named by SUB-381), extended with a personality/habit fixture.
"""
from dataclasses import replace

from src.core.cognition import HabitMemory
from src.core.state import AuthoritativeState, PersonalityComponent
from src.core.builder import V2EntityBuilder
from src.engine.tactical import TacticalDecisionSystem


def _build_skirmisher_evasive_with_aggressive_habit():
    """Frozen construction-time action_style = EVASIVE(2); raw bravery=0.5 alone stays BALANCED,
    but a strongly positive combat_engagement habit bias pushes effective bravery to
    0.5 + (1.0 - 0.5) * 0.4 = 0.7, at/above the 0.65 AGGRESSIVE threshold."""
    attacker = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0.0, 0.0)
        .combat(readiness=100.0, attack_range=5, tactical_role="SKIRMISHER", action_style=2)
        .identity(faction=1, personality=PersonalityComponent(bravery=0.5))
        .build()
    )
    attacker = replace(
        attacker,
        cognition=replace(
            attacker.cognition,
            memory=replace(
                attacker.cognition.memory,
                habit=HabitMemory(patterns={"combat_engagement": 1.0}),
            ),
        ),
    )
    target = (
        V2EntityBuilder(2)
        .kind("monster")
        .location(1.0, 0.0)
        .identity(faction=2)
        .combat(hp=100)
        .build()
    )
    return attacker, target


def test_habit_bias_shifts_action_style_when_flag_on():
    attacker, target = _build_skirmisher_evasive_with_aggressive_habit()
    initial_state = AuthoritativeState(tick=100, seed=42)
    state = replace(
        initial_state,
        entities={1: attacker, 2: target},
        feature_flags={"ENABLE_HABIT_BIAS_ACTION_STYLE": "ON"},
    )

    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)

    assert update.task is not None
    assert update.task.payload_set.get("reason") == "KITING"
    # AGGRESSIVE-derived kite_dist = 2 (+2 SKIRMISHER bonus) = 4, away from target at (1,0).
    assert update.task.payload_set.get("target_position") == (-4.0, 0.0)


def test_habit_bias_flag_off_preserves_construction_time_action_style():
    attacker, target = _build_skirmisher_evasive_with_aggressive_habit()
    initial_state = AuthoritativeState(tick=100, seed=42)
    # feature_flags left empty -> ENABLE_HABIT_BIAS_ACTION_STYLE defaults OFF.
    state = replace(initial_state, entities={1: attacker, 2: target})

    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)

    assert update.task is not None
    assert update.task.payload_set.get("reason") == "KITING"
    # Frozen EVASIVE-derived kite_dist = 6 (+2 SKIRMISHER bonus) = 8, unaffected by the habit bias.
    assert update.task.payload_set.get("target_position") == (-8.0, 0.0)
