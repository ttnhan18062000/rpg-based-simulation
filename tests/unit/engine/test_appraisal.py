"""Decisions 44-50 (commit ii): relations are derived from declared properties, never from a predator/prey label.

Generic synthetic kinds stand in for the archetypes (no real species, no exact figures): every case asserts a band relation or a
precedence, never a number. The same-faction setup makes the faction path say "not hostile", so only the appraisal speaks.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.content.schema import CommonKnowledgeDefinition
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import TaskComponent
from src.engine import appraisal, behavior_consumers
from src.engine.appraisal import THREAT_RANGE, WARY_DISTANCE, Relation
from src.engine.hostility import perceived_hostile, relation
from src.engine.legality import LegalityServiceV2
from src.content.common_knowledge_seed import seeded_knowledge
from src.core.self_model import SelfModelBundle

HUNGRY, SATED = 99.0, 0.0


def _kind(repo, kind_id, *, power, danger, diet, edible_as, base="wolf"):
    body = repo.body_models["quadruped_predator"].model_copy(
        update={"id": f"{kind_id}_body", "diet": diet, "edible_as": edible_as, "size": "medium"})
    repo.body_models[body.id] = body
    repo.species[kind_id] = repo.species[base].model_copy(update={
        "id": kind_id, "body_model": body.id, "power": power, "wits": "small",
        "common_knowledge": CommonKnowledgeDefinition(danger=danger) if danger else None})


@pytest.fixture(scope="module", autouse=True)
def _kinds():
    from src.content.repository import CatalogRepository

    repo = CatalogRepository("data/content")
    repo.load_all()
    _kind(repo, "meat_eater_medium", power="medium", danger="medium", diet=["meat"], edible_as=["meat"])
    _kind(repo, "meat_eater_large", power="large", danger="high", diet=["meat"], edible_as=["meat"])
    _kind(repo, "meat_eater_small", power="small", danger="low", diet=["meat"], edible_as=["meat"])
    _kind(repo, "plant_eater_small", power="small", danger="low", diet=["plant"], edible_as=["meat"])
    _kind(repo, "plant_eater_medium", power="medium", danger="medium", diet=["plant"], edible_as=["meat"])
    _kind(repo, "plant_eater_unknown", power="medium", danger=None, diet=["plant"], edible_as=["meat"])
    _kind(repo, "inedible_large", power="large", danger="extreme", diet=["plant"], edible_as=[])
    behavior_consumers.configure_behavior_consumers(repo)
    yield
    behavior_consumers.reset_behavior_consumers()


def _entity(eid, species, pos, *, hunger=SATED, faction=None, payload=None, last_position=None):
    # Two distinct, mutually non-hostile factions by default, so only the appraisal speaks (a faction never hunts its own).
    faction = faction or (Faction.NEUTRAL if eid == 1 else Faction.TOWN_COUNCIL)
    catalog = behavior_consumers._catalog
    builder = (V2EntityBuilder(eid).kind("monster").location(*pos)
               .identity(role=EntityRole.MONSTER, faction=faction, properties={"species_id": species})
               .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True)
               .lifecycle(active=True).biological(hunger=hunger)
               .replace_self_model(SelfModelBundle(knowledge=seeded_knowledge(catalog))))
    if last_position is not None:
        builder = builder.navigation(last_position=last_position)
    entity = builder.build()
    return replace(entity, task=TaskComponent(work_kind="ENTITY_ACT", payload=payload or {}))


def test_predation_needs_hunger_an_overlapping_diet_and_a_believed_advantage():
    prey = _entity(2, "plant_eater_small", (10.0, 12.0))
    assert relation(_entity(1, "meat_eater_medium", (10.0, 10.0), hunger=HUNGRY), prey) is Relation.PREDATION
    assert relation(_entity(1, "meat_eater_medium", (10.0, 10.0), hunger=SATED), prey) is not Relation.PREDATION
    # the diet gate: a plant diet never overlaps another plant-eater's meat-only edibility
    assert relation(_entity(1, "plant_eater_medium", (10.0, 10.0), hunger=HUNGRY), prey) is Relation.NONE
    # an inedible body feeds nobody
    assert relation(_entity(1, "meat_eater_large", (10.0, 10.0), hunger=HUNGRY), _entity(2, "inedible_large", (10.0, 12.0))) is Relation.NONE


def test_overcoming_is_a_strict_comparison_of_own_power_against_the_believed_danger():
    eater = lambda species: _entity(1, species, (10.0, 10.0), hunger=HUNGRY)  # noqa: E731
    equal = _entity(2, "plant_eater_medium", (10.0, 12.0))
    assert appraisal.can_overcome(eater("meat_eater_medium"), equal) is False  # a tie is "cannot"
    assert appraisal.can_overcome(eater("meat_eater_large"), equal) is True  # large beats a medium belief
    assert appraisal.can_overcome(eater("meat_eater_small"), _entity(2, "plant_eater_small", (10.0, 12.0))) is False  # small beats nothing
    assert appraisal.can_overcome(eater("meat_eater_large"), _entity(2, "inedible_large", (10.0, 12.0))) is False  # extreme is never overcome
    unknown = _entity(2, "plant_eater_unknown", (10.0, 12.0))
    assert appraisal.can_overcome(eater("meat_eater_medium"), unknown) == appraisal.can_overcome(eater("meat_eater_medium"), equal)  # no belief = medium


def test_wary_reads_what_the_other_is_and_never_the_subjects_hunger():
    meat_eater = _entity(2, "meat_eater_medium", (10.0, 16.0))
    for hunger in (SATED, HUNGRY):
        assert relation(_entity(1, "plant_eater_medium", (10.0, 10.0), hunger=hunger), meat_eater) is Relation.WARY
    # a creature the meat-eater cannot eat is no concern, and one the subject can overcome is not worrying
    assert relation(_entity(1, "inedible_large", (10.0, 10.0)), meat_eater) is Relation.NONE
    assert relation(_entity(1, "meat_eater_large", (10.0, 10.0)), meat_eater) is Relation.NONE


def test_threatening_needs_proximity_and_either_its_target_or_a_closing_step():
    me = _entity(1, "plant_eater_medium", (10.0, 10.0))
    near, far = (10.0, 10.0 + THREAT_RANGE), (10.0, 10.0 + THREAT_RANGE + 2)
    assert relation(me, _entity(2, "meat_eater_medium", near, payload={"target_id": 1})) is Relation.THREATENING
    closing = _entity(2, "meat_eater_medium", near, last_position=(near[0], near[1] + 1.0))
    assert relation(me, closing) is Relation.THREATENING
    assert relation(me, _entity(2, "meat_eater_medium", near)) is Relation.WARY  # near but idle: wary only
    assert relation(me, _entity(2, "meat_eater_medium", far, payload={"target_id": 1})) is Relation.WARY  # coming but not near


def test_a_faction_verdict_beats_predation():
    hero = _entity(1, "meat_eater_medium", (10.0, 10.0), hunger=HUNGRY, faction=Faction.HERO_GUILD)
    prey = _entity(2, "plant_eater_small", (10.0, 12.0), faction=Faction.MONSTER_HORDE)
    assert relation(hero, prey) is Relation.FACTION_HOSTILE


def test_a_plant_eater_never_gets_a_meat_eater_in_its_hostile_list():
    me = _entity(1, "plant_eater_medium", (10.0, 10.0), hunger=HUNGRY)
    meat_eater = _entity(2, "meat_eater_medium", (10.0, 11.0), payload={"target_id": 1})
    assert relation(me, meat_eater) is Relation.THREATENING
    assert perceived_hostile(me, meat_eater) is False


def test_predation_permits_the_attack_when_factions_refuse_and_a_sated_one_does_not():
    prey = _entity(2, "plant_eater_small", (10.0, 11.0))
    hungry = _entity(1, "meat_eater_medium", (10.0, 10.0), hunger=HUNGRY)
    sated = _entity(1, "meat_eater_medium", (10.0, 10.0), hunger=SATED)
    assert perceived_hostile(hungry, prey) is True
    assert perceived_hostile(sated, prey) is False
    from src.content_semantics.relation import RelationContext
    context = RelationContext(combat_engaged=True)
    assert LegalityServiceV2._attack_permitted(hungry, prey, context) is True
    assert LegalityServiceV2._attack_permitted(sated, prey, context) is False


def test_wary_distance_exceeds_the_threat_range():
    assert WARY_DISTANCE > THREAT_RANGE


def test_a_faction_does_not_hunt_its_own_members():
    hungry = _entity(1, "meat_eater_large", (10.0, 10.0), hunger=HUNGRY, faction=Faction.NEUTRAL)
    kin = _entity(2, "plant_eater_small", (10.0, 12.0), faction=Faction.NEUTRAL)
    other = _entity(2, "plant_eater_small", (10.0, 12.0), faction=Faction.TOWN_COUNCIL)
    assert relation(hungry, kin) is Relation.NONE
    assert relation(hungry, other) is Relation.PREDATION


def test_a_kind_never_hunts_its_own_species_whatever_its_faction():
    hungry = _entity(1, "meat_eater_large", (10.0, 10.0), hunger=HUNGRY, faction=Faction.NEUTRAL)
    same_kind = _entity(2, "meat_eater_large", (10.0, 12.0), faction=Faction.TOWN_COUNCIL)
    assert relation(hungry, same_kind) is Relation.NONE


def test_prey_may_fight_back_against_what_is_hunting_it_but_not_start_a_fight():
    from src.content_semantics.relation import RelationContext
    context = RelationContext(combat_engaged=True)
    hunter = _entity(1, "meat_eater_medium", (10.0, 10.0), hunger=HUNGRY, payload={"target_id": 2})
    prey = _entity(2, "plant_eater_small", (10.0, 11.0))
    assert LegalityServiceV2._attack_permitted(hunter, prey, context) is True
    assert LegalityServiceV2._attack_permitted(prey, hunter, context) is True  # counter-attack against its hunter
    idle = replace(hunter, task=TaskComponent(work_kind="ENTITY_ACT", payload={}))
    assert LegalityServiceV2._attack_permitted(prey, idle, context) is False  # no un-engaged first strike


def test_a_hungry_wolf_gets_predation_on_the_plant_eater_as_compiled_from_content():
    """Positive end-to-end relation from compiled content: no synthetic kinds. The plant-eater shares no faction with the wolf (it would silently
    stop every hunt), is hostile to nobody by faction, and the wolf's relation is the appraisal's PREDATION, while the plant-eater is WARY of the wolf."""
    from tests.helpers.scenario import compile_world

    state = compile_world("frontier_living_world", 42)
    wolf = next(e for e in state.entities.values() if (e.identity.properties or {}).get("species_id") == "wolf")
    eater = next(e for e in state.entities.values() if (e.identity.properties or {}).get("species_id") == "small_plant_eater")
    x, y = wolf.navigation.position
    wolf = replace(wolf, biological=replace(wolf.biological, hunger=HUNGRY))
    eater = replace(eater, navigation=replace(eater.navigation, position=(x + 2.0, y)))
    assert wolf.identity.properties["faction_id"] != eater.identity.properties["faction_id"]
    assert relation(wolf, eater) is Relation.PREDATION
    assert relation(replace(wolf, biological=replace(wolf.biological, hunger=SATED)), eater) is not Relation.PREDATION
    assert relation(eater, wolf) is Relation.WARY
