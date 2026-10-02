"""Shaper and extractor must share one definition of the boss set and the spawn-cadence exclusion tuple."""
from __future__ import annotations

import src.observability.entity_kind_constants as ekc
import src.observability.event_extractor as event_extractor
import src.observability.event_shapers as event_shapers
from src.observability.event_shapers import WorldDynamicsShaper


def test_boss_kind_set_is_one_object_with_expected_membership():
    assert WorldDynamicsShaper._BOSS_KINDS is ekc.BOSS_ENTITY_KINDS
    assert event_extractor.BOSS_ENTITY_KINDS is ekc.BOSS_ENTITY_KINDS
    assert ekc.BOSS_ENTITY_KINDS == frozenset({"world_boss", "ancient_sentinel", "dragonkin"})


def test_spawn_cadence_exclusion_is_one_object_with_expected_membership():
    assert event_shapers.SPAWN_CADENCE_EXCLUDED_KINDS is ekc.SPAWN_CADENCE_EXCLUDED_KINDS
    assert event_extractor.SPAWN_CADENCE_EXCLUDED_KINDS is ekc.SPAWN_CADENCE_EXCLUDED_KINDS
    assert set(ekc.SPAWN_CADENCE_EXCLUDED_KINDS) == {
        None, "world_boss", "ancient_sentinel", "goblin_raider", "dragonkin",
    }


def test_goblin_raider_is_excluded_from_cadence_but_not_a_boss_kind():
    assert "goblin_raider" in ekc.SPAWN_CADENCE_EXCLUDED_KINDS
    assert "goblin_raider" not in ekc.BOSS_ENTITY_KINDS
    assert "dragonkin" in ekc.BOSS_ENTITY_KINDS
    assert "dragonkin" in ekc.SPAWN_CADENCE_EXCLUDED_KINDS
