"""Rule ENV-07 (owner decision 15): regional trauma counts deaths with a violent cause only.

The test is the recorded cause, not "has a killer". Adding a declared catastrophe later is a single
edit to ``VIOLENT_DEATH_OUTCOME_KINDS`` made by an owner decision.
"""
from __future__ import annotations

import pytest

from src.core.combat_constants import TERMINAL_COMBAT_OUTCOME_KINDS
from src.core.violent_cause import (
    VIOLENT_DEATH_OUTCOME_KINDS,
    is_violent_building_destruction,
    is_violent_death_cause,
)


@pytest.mark.parametrize("kind", ["KILL", "DEFEAT"])
def test_terminal_combat_outcomes_are_violent(kind: str) -> None:
    assert is_violent_death_cause(kind) is True


@pytest.mark.parametrize("kind", ["HAZARD", "SURVIVE", "REJECTED", "STARVATION", "", None])
def test_ambient_and_non_terminal_causes_are_not_violent(kind) -> None:
    assert is_violent_death_cause(kind) is False


def test_violent_set_is_derived_from_the_terminal_combat_outcomes() -> None:
    assert VIOLENT_DEATH_OUTCOME_KINDS == frozenset(TERMINAL_COMBAT_OUTCOME_KINDS)
    assert "HAZARD" not in VIOLENT_DEATH_OUTCOME_KINDS


def test_building_destruction_is_violent_only_with_a_damaging_delta() -> None:
    assert is_violent_building_destruction(-50) is True
    assert is_violent_building_destruction(0) is False
    assert is_violent_building_destruction(10) is False
