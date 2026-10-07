"""KNOW-04: a subject starts with declared common knowledge about a recognisable kind.

TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY. The catalog declares folk belief next to a species; every
subject is seeded once at spawn with one low-confidence fact per DECLARED species, in all three spawn paths, and the facts
survive canonical serialization. Decision logic only reads them.
"""
from __future__ import annotations

import dataclasses

import pytest

from src.cognition.capability_estimate import COMMON_KNOWLEDGE_CERTAINTY
from src.cognition.common_knowledge import (
    COMMON_KNOWLEDGE_SOURCE_ID, combat_capability_against, danger_fact_key, default_self_model)
from src.content.schema import CommonKnowledgeDefinition
from src.core.builder import V2EntityBuilder
from src.core.self_model import KnowledgeFact, KnowledgeModelComponent
from src.engine import behavior_consumers


def _catalog():
    if behavior_consumers._catalog is None:
        behavior_consumers._auto_init()
    return behavior_consumers._catalog


def _declared():
    return {sid: sp.common_knowledge.danger for sid, sp in _catalog().species.items() if sp.common_knowledge}


def test_the_catalog_declares_folk_belief_only_for_hostile_species_and_leaves_the_rest_uninformed():
    declared = _declared()
    assert declared == {"goblin": "low", "human": "medium", "lizardfolk": "medium", "orc": "high",
                        "spider": "medium", "undead": "high", "wolf": "medium"}
    assert _catalog().species["dragonkin"].common_knowledge is None


def test_an_undeclared_danger_level_is_rejected():
    with pytest.raises(ValueError):
        CommonKnowledgeDefinition(danger="terrifying")


def test_default_common_knowledge_is_one_weak_fact_per_declared_species_with_visible_provenance():
    facts = default_self_model().knowledge.facts
    assert sorted(facts) == sorted(danger_fact_key(s) for s in _declared())
    for sid, fact in ((f.subject, f) for f in facts.values()):
        assert fact.fact_type == "danger_rating" and fact.source_id == COMMON_KNOWLEDGE_SOURCE_ID
        assert fact.certainty == COMMON_KNOWLEDGE_CERTAINTY and fact.details == {"danger_level": _declared()[sid]}


def test_compiler_path_seeds_every_subject():
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository
    spec, ctx = WorldRepository("data/worlds").load_world_with_context("crowded_frontier")
    state, _ = WorldCompiler.compile(spec, seed=42, context=ctx)
    assert state.entities
    expected = sorted(danger_fact_key(s) for s in _declared())
    assert all(sorted(e.self_model.knowledge.facts) == expected for e in state.entities.values())


def test_archetype_factory_path_seeds_the_subject():
    from tests.unit.entities.test_archetype_entity_factory import FACTORY, _contract, _spawn
    entity = FACTORY.build_entity(1, _contract(), _spawn())
    assert sorted(entity.self_model.knowledge.facts) == sorted(danger_fact_key(s) for s in _declared())


def test_legacy_guard_spawner_path_seeds_the_subject():
    from src.worldassembly.entity_spawner import WorldEntitySpawner
    from tests.unit.worldassembly.test_entity_spawner_legacy_guard import _profile, _spawn_ctx
    entity = WorldEntitySpawner()._spawn_legacy_guard(1, _profile(), _spawn_ctx(), seed=42)
    assert sorted(entity.self_model.knowledge.facts) == sorted(danger_fact_key(s) for s in _declared())


def test_facts_round_trip_through_the_canonical_dict_and_change_the_state_hash():
    seeded = V2EntityBuilder(1).replace_self_model(default_self_model()).build()
    bare = V2EntityBuilder(1).build()
    canonical = seeded.self_model.knowledge.to_canonical_dict()
    assert canonical["facts"][danger_fact_key("wolf")] == {
        "fact_type": "danger_rating", "certainty": COMMON_KNOWLEDGE_CERTAINTY, "source_id": COMMON_KNOWLEDGE_SOURCE_ID,
        "recorded_tick": 0, "details": {"danger_level": "medium"}}
    rebuilt = KnowledgeModelComponent(facts={
        k: KnowledgeFact(subject=k.removeprefix("danger."), fact_type=v["fact_type"], details=v["details"],
                         certainty=v["certainty"], source_id=v["source_id"], recorded_tick=v["recorded_tick"])
        for k, v in canonical["facts"].items()})
    assert rebuilt.to_canonical_dict()["facts"] == canonical["facts"]
    assert seeded.to_canonical_dict() != bare.to_canonical_dict()


def _hostile(species_id):
    return V2EntityBuilder(2).kind("raider").identity(properties={"species_id": species_id}).build()


def test_a_hostile_of_an_undeclared_species_is_estimated_neutrally_and_a_declared_one_by_folk_belief():
    entity = V2EntityBuilder(1).combat(hp=100, max_hp=100, atk=10, def_stat=5).replace_self_model(default_self_model()).build()
    low, high = combat_capability_against(entity, _hostile("goblin")), combat_capability_against(entity, _hostile("orc"))
    neutral = combat_capability_against(entity, _hostile("dragonkin"))
    assert low > neutral > high   # goblins believed weak, orcs believed dangerous, dragonkin uninformed


def test_every_human_gets_one_shared_prior_so_a_raider_and_a_guard_are_not_told_apart():
    entity = V2EntityBuilder(1).combat(hp=100, max_hp=100, atk=10, def_stat=5).replace_self_model(default_self_model()).build()
    raider = V2EntityBuilder(2).kind("raider").identity(properties={"species_id": "human"}).build()
    guard = V2EntityBuilder(3).kind("guard").identity(properties={"species_id": "human"}).build()
    assert combat_capability_against(entity, raider) == combat_capability_against(entity, guard)
