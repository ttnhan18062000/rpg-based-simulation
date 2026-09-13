"""
tests/unit/domains/combat_engagement/test_learning_outcome.py

TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

Unit tests for src/domains/combat_engagement/learning_outcome.py -- the declared Sec 13.5a
CombatUpdate.outcome_kind -> CombatLearning.learn() mapping.
"""

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent
from src.core.combat_constants import NEAR_DEATH_HP_RATIO
from src.domains.combat_engagement.learning_outcome import (
    classify_defender_outcome,
    classify_attacker_outcome,
    apply_combat_learning,
)
from src.domains.combat_engagement.phase import opponent_subject_key


def _entity(e_id, hp=100, max_hp=100):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=max_hp, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(evolution_level=1)
    return b.build()


# ---------------------------------------------------------------------------
# classify_defender_outcome
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("outcome_kind", ["KILL", "DEFEAT", "PERMADEATH", "REBIRTH"])
def test_defeated_defender_learns_lost(outcome_kind):
    assert classify_defender_outcome(outcome_kind) == "LOST"


@pytest.mark.parametrize("outcome_kind", ["SURVIVE", "REJECTED", "SUCCESS"])
def test_surviving_or_rejected_defender_learns_nothing(outcome_kind):
    assert classify_defender_outcome(outcome_kind) is None


# ---------------------------------------------------------------------------
# classify_attacker_outcome
# ---------------------------------------------------------------------------

def test_attacker_who_wins_at_high_hp_learns_won_easy():
    assert classify_attacker_outcome("KILL", attacker_hp_ratio=0.9) == "WON_EASY"


def test_attacker_who_wins_at_low_hp_learns_near_death():
    """
    The user's own worked scenario: engage, take a beating, win, remember the target as far
    stronger than estimated.
    """
    assert classify_attacker_outcome("KILL", attacker_hp_ratio=0.1) == "NEAR_DEATH"


def test_near_death_threshold_boundary_matches_shared_constant():
    just_above = classify_attacker_outcome("KILL", attacker_hp_ratio=NEAR_DEATH_HP_RATIO + 0.01)
    just_below = classify_attacker_outcome("KILL", attacker_hp_ratio=NEAR_DEATH_HP_RATIO - 0.01)
    assert just_above == "WON_EASY"
    assert just_below == "NEAR_DEATH"


def test_attacker_learns_nothing_from_survive_or_rejected():
    assert classify_attacker_outcome("SURVIVE", attacker_hp_ratio=0.1) is None
    assert classify_attacker_outcome("REJECTED", attacker_hp_ratio=0.1) is None


# ---------------------------------------------------------------------------
# apply_combat_learning -- both participants, order-independence
# ---------------------------------------------------------------------------

def test_kill_updates_both_participants_opponent_models():
    attacker = _entity(1, hp=15, max_hp=100)  # near-death, hard-won kill
    defender = _entity(2, hp=0, max_hp=100)

    new_attacker_cognition, new_defender_cognition = apply_combat_learning(
        attacker, defender, outcome_kind="KILL", damage_taken=40.0, tick=5,
    )

    assert new_attacker_cognition is not None
    assert new_defender_cognition is not None

    attacker_model = new_attacker_cognition.memory.combat.opponent_stats[opponent_subject_key(defender.id)]
    assert attacker_model.outcomes[-1] == "NEAR_DEATH"

    defender_model = new_defender_cognition.memory.combat.opponent_stats[opponent_subject_key(attacker.id)]
    assert defender_model.outcomes[-1] == "LOST"


def test_survive_produces_no_learning_for_either_participant():
    attacker = _entity(1, hp=80, max_hp=100)
    defender = _entity(2, hp=70, max_hp=100)

    new_attacker_cognition, new_defender_cognition = apply_combat_learning(
        attacker, defender, outcome_kind="SURVIVE", damage_taken=20.0, tick=5,
    )

    assert new_attacker_cognition is None
    assert new_defender_cognition is None


def test_rejected_produces_no_learning_for_either_participant():
    attacker = _entity(1, hp=100, max_hp=100)
    defender = _entity(2, hp=100, max_hp=100)

    new_attacker_cognition, new_defender_cognition = apply_combat_learning(
        attacker, defender, outcome_kind="REJECTED", damage_taken=0.0, tick=5,
    )

    assert new_attacker_cognition is None
    assert new_defender_cognition is None


def test_both_writes_are_order_independent():
    """
    Classifying/applying the attacker's own outcome before or after the defender's own outcome
    must produce identical results either way -- each reads only its own participant's real,
    already-resolved fields.
    """
    attacker = _entity(1, hp=15, max_hp=100)
    defender = _entity(2, hp=0, max_hp=100)

    attacker_outcome = classify_attacker_outcome("KILL", attacker.combat.hp / attacker.combat.max_hp)
    defender_outcome = classify_defender_outcome("KILL")

    # Neither classification depends on the other having already run.
    assert attacker_outcome == "NEAR_DEATH"
    assert defender_outcome == "LOST"

    result_a = apply_combat_learning(attacker, defender, "KILL", 40.0, tick=5)
    result_b = apply_combat_learning(attacker, defender, "KILL", 40.0, tick=5)
    assert result_a[0].memory.combat.opponent_stats == result_b[0].memory.combat.opponent_stats
    assert result_a[1].memory.combat.opponent_stats == result_b[1].memory.combat.opponent_stats
