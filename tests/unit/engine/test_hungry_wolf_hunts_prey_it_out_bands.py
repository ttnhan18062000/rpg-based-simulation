"""Decisions 44 to 49 (hunting by appraisal), split out of the species-hostility metamorphic test
(TCK-20261011-SPECIES-HOSTILITY-METAMORPHIC-TEST-USES-A-PAIR-SPECIES-RELATIONS-STILL-GOVERNS).

A wolf is a wild creature, so species_relations and faction verdicts never decide whom it fights: appraisal does. A hungry wolf regards prey it
out-bands as PREDATION and a sated one regards it as nothing. By the designer's ruling (a), a wolf never hunts a PERSON in M0: a tie in kind
bands resolves to cannot-overcome, so a person is not prey to it. The check is therefore wolves against the herd, not against people.
Entities come from the compiled `frontier_living_world`, so no synthetic kinds stand in for content."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.engine.appraisal import HUNT_HUNGER, Relation, appraise
from tests.helpers.scenario import compile_world

HUNGRY = HUNT_HUNGER + 40.0
SATED = 0.0


def _species(state, species):
    return next(e for e in state.entities.values() if (e.identity.properties or {}).get("species_id") == species)


def _beside(target, wolf, dx):
    x, y = wolf.navigation.position
    return replace(target, navigation=replace(target.navigation, position=(x + dx, y)))


@pytest.fixture(scope="module")
def world():
    return compile_world("frontier_living_world", 42)


def _with_hunger(entity, hunger):
    return replace(entity, biological=replace(entity.biological, hunger=hunger))


def test_a_hungry_wolf_regards_the_herd_as_prey_and_a_sated_one_does_not(world):
    wolf = _species(world, "wolf")
    herd = _beside(_species(world, "small_plant_eater"), wolf, 2.0)
    assert appraise(_with_hunger(wolf, HUNGRY), herd) is Relation.PREDATION
    assert appraise(_with_hunger(wolf, SATED), herd) is not Relation.PREDATION


def test_a_hungry_wolf_does_not_regard_a_person_as_prey_because_a_tie_in_kind_bands_cannot_be_overcome(world):
    wolf = _with_hunger(_species(world, "wolf"), HUNGRY)
    person = _beside(_species(world, "human"), wolf, 2.0)
    assert appraise(wolf, person) is not Relation.PREDATION
