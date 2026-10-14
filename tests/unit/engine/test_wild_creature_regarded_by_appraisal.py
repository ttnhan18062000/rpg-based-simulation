"""Decision 47 (raiders by appraisal): a faction verdict never decides a fight with a wild creature; appraisal does.

A wild creature is a body with a diet whose faction has the wild alignment. The shipped kinds are read from content, so the five monster kinds
that keep faction hostility (and the people-kinds) are asserted too: the rule widens by content, never by a kind list in code.
"""
from __future__ import annotations

import pytest

from src.content.repository import CatalogRepository
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.engine import behavior_consumers
from src.engine.hostility import attack_allowed, faction_hostile, is_wild_creature

FACTION_OF = {
    "wolf": "wild_beast_pack", "spider": "wild_beast_pack", "small_plant_eater": "wild_fauna",
    "human": "town_council", "goblin": "goblin_warband", "orc": "orc_clan",
    "troll": "orc_clan", "undead": "undead_remnants", "dragonkin": "dragon_cult", "slime": "wild_beast_pack", "spirit": "spirit_court",
}


@pytest.fixture(scope="module", autouse=True)
def _content():
    repo = CatalogRepository("data/content")
    repo.load_all()
    behavior_consumers.configure_behavior_consumers(repo)
    yield
    behavior_consumers.reset_behavior_consumers()


def _entity(eid, species, pos=(10.0, 10.0)):
    return (V2EntityBuilder(eid).kind("monster").location(*pos)
            .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE,
                      properties={"species_id": species, "faction_id": FACTION_OF[species]})
            .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True).lifecycle(active=True).build())


@pytest.mark.parametrize("species", ["wolf", "spider", "small_plant_eater"])
def test_animals_of_the_wild_alignment_are_wild_creatures(species):
    assert is_wild_creature(_entity(1, species))


@pytest.mark.parametrize("species", ["human", "goblin", "orc", "troll", "undead", "dragonkin", "spirit"])
def test_people_and_monsters_are_not_wild_creatures_so_they_keep_faction_hostility_among_themselves(species):
    assert not is_wild_creature(_entity(1, species))


def test_a_raider_and_a_wolf_have_no_faction_verdict_either_way():
    raider, wolf = _entity(1, "goblin"), _entity(2, "wolf", (10.0, 11.0))
    assert not faction_hostile(raider, wolf)
    assert not faction_hostile(wolf, raider)


def test_a_faction_verdict_cannot_make_an_attack_on_a_wild_creature_legal():
    raider, plant_eater = _entity(1, "goblin"), _entity(2, "small_plant_eater", (10.0, 11.0))
    assert not attack_allowed(raider, plant_eater, True)  # not hungry: no PREDATION, and no faction verdict counts
