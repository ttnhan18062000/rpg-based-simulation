"""AGENCY-06: regional dread scales with trauma / the Bible 05 section 2 instability threshold, saturates
there, and never makes a subject flee on its own. A threat to the subject itself still can
(TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE)."""
import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import PersonalityComponent
from src.engine.cognition import (
    FLEE_PANIC_THRESHOLD,
    REGIONAL_DREAD_MAX,
    AppraisalSystem,
    regional_dread,
)
from src.engine.world_dynamics import HAZARD_GROWTH_TRAUMA_THRESHOLD

SATURATED = HAZARD_GROWTH_TRAUMA_THRESHOLD


def _subject(hp: int, bravery: float = 0.0):
    return (V2EntityBuilder(1).kind("HERO").combat(hp=hp, max_hp=100)
            .identity(personality=PersonalityComponent(bravery=bravery)).build())


def test_dread_at_saturation_alone_does_not_flee():
    profile = AppraisalSystem.evaluate_emotional_state(_subject(hp=100), [], region_trauma=SATURATED)
    assert profile.panic_level == pytest.approx(REGIONAL_DREAD_MAX)
    assert not profile.is_fleeing


@pytest.mark.parametrize("trauma", [0.0, 1.0, 2.0, 25.0, 50.0, 500.0, 1e9])
def test_no_regional_trauma_value_flees_alone(trauma):
    """The invariant over the whole input range, not just the saturation point (bravery 0 is the
    worst case: bravery only lowers panic)."""
    assert not AppraisalSystem.evaluate_emotional_state(_subject(hp=100), [], region_trauma=trauma).is_fleeing


def test_the_old_two_deaths_input_no_longer_floods_flight():
    """Two deaths (trauma 2.0) used to add +1.0 and flee at any bravery. It now adds 0.012."""
    assert regional_dread(2.0) == pytest.approx(REGIONAL_DREAD_MAX * 2.0 / SATURATED)
    assert not AppraisalSystem.evaluate_emotional_state(_subject(hp=100), [], region_trauma=2.0).is_fleeing


def test_near_death_control_still_flees_alone():
    """A threat to the subject itself (health below 10%) decides flight with no regional dread."""
    profile = AppraisalSystem.evaluate_emotional_state(_subject(hp=5), [], region_trauma=0.0)
    assert profile.panic_level == pytest.approx(0.8)
    assert profile.is_fleeing


def test_dread_tips_a_threat_over_the_line_but_is_not_the_whole_reason():
    """Health below 40% adds 0.2 (no flee alone); saturated dread adds 0.3 on top (flees)."""
    wounded = _subject(hp=35)
    assert not AppraisalSystem.evaluate_emotional_state(wounded, [], region_trauma=0.0).is_fleeing
    assert AppraisalSystem.evaluate_emotional_state(wounded, [], region_trauma=SATURATED).is_fleeing


def test_dread_saturates_and_is_monotonic_and_bounded():
    values = [regional_dread(t) for t in (0.0, 1.0, 10.0, 25.0, SATURATED)]
    assert values == sorted(values)
    assert values[0] == 0.0
    assert regional_dread(SATURATED) == regional_dread(SATURATED * 100) == REGIONAL_DREAD_MAX
    assert regional_dread(-5.0) == 0.0


def test_dread_ceiling_is_between_the_weakest_threat_term_and_the_flee_line():
    """The constraint that fixes REGIONAL_DREAD_MAX: it can tip the weakest threat term (0.2) yet
    stays strictly below the flee threshold."""
    assert 0.2 < REGIONAL_DREAD_MAX < FLEE_PANIC_THRESHOLD
