"""Decision 44 (commit iii, second half): the hunger need opens a way by scavenging a carcass or hunting, for a body whose diet includes meat.

Real corpus kinds stand in (wolf: meat-only, medium power; goblin: believed low danger, so a medium wolf can overcome it). Stage order and
relations only: the order the steps are tried in, what each points at, and that a fed subject stops.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

import src.core.registries  # noqa: F401
from src.ai.goals.base import OpeningStepKind
from src.ai.goals.opening_steps import first_open_step, opening_steps
from src.ai.goals.scorers import EatScorer
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, CorpseState, ItemStack, ResourceNodeState
from src.cognition.common_knowledge import default_self_model
from src.engine import behavior_consumers


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository

    repo = CatalogRepository("data/content")
    repo.load_all()
    behavior_consumers.configure_behavior_consumers(repo)
    yield
    behavior_consumers.reset_behavior_consumers()


def _kind(eid, species, pos, faction, hunger=0.0):
    return (V2EntityBuilder(eid).kind("monster").location(*pos)
            .identity(role=EntityRole.MONSTER, faction=faction, properties={"species_id": species})
            .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True).lifecycle(active=True)
            .biological(hunger=hunger).replace_self_model(default_self_model()).build())


def _state(*entities, corpses=(), nodes=()):
    return AuthoritativeState(tick=5, seed=1, entities={e.id: e for e in entities}, corpses={c.id: c for c in corpses},
                              resource_nodes={n.id: n for n in nodes})


def _wolf(hunger=60.0):
    return _kind(1, "wolf", (10.0, 10.0), Faction.NEUTRAL, hunger)


def _goblin(pos=(10.0, 13.0)):
    return _kind(2, "goblin", pos, Faction.TOWN_COUNCIL)


def _carcass(pos=(10.0, 15.0), items=(ItemStack("raw_meat", 2),), dead=3):
    return CorpseState(id=1000000 + dead, original_entity_id=dead, position=pos, items=list(items), decay_tick=100)


def test_a_meat_eater_with_no_food_node_scavenges_a_carcass_before_it_hunts():
    wolf, goblin, carcass = _wolf(), _goblin(), _carcass()
    step = first_open_step(wolf, _state(wolf, goblin, corpses=[carcass]))
    assert step.kind is OpeningStepKind.SCAVENGE and step.target_id == str(carcass.id) and step.target_pos == carcass.position


def test_with_no_carcass_it_hunts_the_creature_it_appraises_as_prey_and_names_it_as_a_typed_target():
    wolf, goblin = _wolf(), _goblin()
    step = first_open_step(wolf, _state(wolf, goblin))
    assert step.kind is OpeningStepKind.HUNT and step.target_entity_id == goblin.id
    goal = EatScorer().score(wolf, _state(wolf, goblin))
    assert goal.opening_step is OpeningStepKind.HUNT and goal.target_entity_id == goblin.id


def test_a_fed_subject_stops_hunting_because_predation_needs_hunger():
    goblin = _goblin()
    hunting = first_open_step(_wolf(hunger=60.0), _state(_wolf(hunger=60.0), goblin))
    fed = first_open_step(_wolf(hunger=0.0), _state(_wolf(hunger=0.0), goblin))
    assert hunting.kind is OpeningStepKind.HUNT and (fed is None or fed.kind is not OpeningStepKind.HUNT)


def test_it_never_hunts_what_it_cannot_overcome_or_its_own_species_and_never_scavenges_its_own_kind():
    wolf = _wolf()
    orc = _kind(2, "orc", (10.0, 13.0), Faction.TOWN_COUNCIL)  # believed high danger: a medium wolf cannot overcome it
    assert all(not s.available or s.kind is not OpeningStepKind.HUNT for s in opening_steps(wolf, _state(wolf, orc)))
    pack = _kind(2, "wolf", (10.0, 13.0), Faction.TOWN_COUNCIL)
    assert all(not s.available or s.kind is not OpeningStepKind.HUNT for s in opening_steps(wolf, _state(wolf, pack)))
    dead_wolf = _kind(3, "wolf", (10.0, 15.0), Faction.TOWN_COUNCIL)
    dead_wolf = replace(dead_wolf, combat=replace(dead_wolf.combat, alive=False))
    assert all(not s.available or s.kind is not OpeningStepKind.SCAVENGE for s in opening_steps(wolf, _state(wolf, dead_wolf, corpses=[_carcass()])))


def test_a_meat_only_body_does_not_forage_berries_but_a_person_does():
    berries = ResourceNodeState(id=10, kind="berry_thicket", position=(12.0, 10.0), yields_item="wild_berries",
                                remaining_charges=4, max_charges=8, required_ticks=8, cooldown_remaining=0)
    wolf, person = _wolf(), _kind(4, "human", (10.0, 10.0), Faction.HERO_GUILD, 60.0)
    assert all(not s.available or s.kind is not OpeningStepKind.FORAGE for s in opening_steps(wolf, _state(wolf, nodes=[berries])))
    assert first_open_step(person, _state(person, nodes=[berries])).kind is OpeningStepKind.FORAGE


def test_a_leashed_animal_hunts_and_scavenges_only_within_its_own_range():
    """A territorial animal is returned home every tick past its leash, so a target out there could never be reached: it ignores a carcass
    outside its range and goes for one inside it (and the same for a creature to hunt)."""
    wolf = _wolf()
    wolf = replace(wolf, navigation=replace(wolf.navigation, home_position=(10.0, 10.0), leash_radius=8.0))
    outside = _carcass(pos=(10.0, 19.0))  # nine tiles from home: beyond the leash, though within scavenge reach
    inside = _carcass(pos=(10.0, 17.0), dead=4)
    assert not [s for s in opening_steps(wolf, _state(wolf, corpses=[outside])) if s.available]
    step = first_open_step(wolf, _state(wolf, corpses=[outside, inside]))
    assert step.kind is OpeningStepKind.SCAVENGE and step.target_id == str(inside.id)
    far_goblin = _goblin(pos=(10.0, 19.0))
    assert all(not s.available or s.kind is not OpeningStepKind.HUNT for s in opening_steps(wolf, _state(wolf, far_goblin)))
    assert first_open_step(wolf, _state(wolf, _goblin(pos=(10.0, 14.0)))).kind is OpeningStepKind.HUNT
