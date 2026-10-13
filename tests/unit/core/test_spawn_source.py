# tests/unit/core/test_spawn_source.py
# TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS (M0 gate V8: every mid-run entity add has a declared source)
import pytest

from src.core.builder import V2EntityBuilder
from src.core.spawn_source import SpawnKind, SpawnSource
from src.core.state import AuthoritativeState, LifeStage
from src.core.updates import StateUpdate
from src.systems.world_systems.generator import EntityGenerator
from src.world.reproduction_humanoid import HumanoidReproductionService


def _add(entity_id, source):
    return StateUpdate(entities_add=[V2EntityBuilder(entity_id).build()], entity_spawn_sources={entity_id: source})


def test_a_birth_source_names_its_parents():
    assert SpawnSource(SpawnKind.BIRTH, parent_ids=(1, 2)).parent_ids == (1, 2)
    with pytest.raises(ValueError):
        SpawnSource(SpawnKind.BIRTH)


def test_only_a_birth_has_parent_ids():
    for kind in (SpawnKind.INITIAL, SpawnKind.AUTHORED_ARRIVAL):
        with pytest.raises(ValueError):
            SpawnSource(kind, parent_ids=(1,), rule_kind="camp", rule_id="x")


def test_an_authored_arrival_names_its_rule():
    assert SpawnSource(SpawnKind.AUTHORED_ARRIVAL, rule_kind="camp", rule_id="goblin_camp").rule_id == "goblin_camp"
    for kwargs in ({}, {"rule_kind": "camp"}, {"rule_id": "goblin_camp"}):
        with pytest.raises(ValueError):
            SpawnSource(SpawnKind.AUTHORED_ARRIVAL, **kwargs)


def test_initial_needs_nothing_else():
    assert SpawnSource(SpawnKind.INITIAL).kind is SpawnKind.INITIAL


def test_merge_unions_the_sources_of_both_updates():
    a = _add(7, SpawnSource(SpawnKind.BIRTH, parent_ids=(1, 2)))
    b = _add(8, SpawnSource(SpawnKind.AUTHORED_ARRIVAL, rule_kind="camp", rule_id="c"))
    merged = a.merge(b)
    assert set(merged.entity_spawn_sources) == {7, 8}


def test_merge_keeps_one_source_when_two_producers_declare_the_same_one():
    s = SpawnSource(SpawnKind.BIRTH, parent_ids=(1, 2))
    assert _add(7, s).merge(_add(7, s)).entity_spawn_sources == {7: s}


def test_merge_refuses_two_different_sources_for_one_id_rather_than_drop_one():
    a = _add(7, SpawnSource(SpawnKind.BIRTH, parent_ids=(1, 2)))
    b = _add(7, SpawnSource(SpawnKind.BIRTH, parent_ids=(3, 4)))
    with pytest.raises(ValueError):
        a.merge(b)


def test_the_humanoid_birth_path_tags_the_child_with_its_two_parents():
    parents = {i: V2EntityBuilder(i).kind("villager").location(5.0, 5.0).build() for i in (1, 2)}
    state = AuthoritativeState(tick=200, seed=42, entities=parents)
    generator = EntityGenerator(seed=42)
    generator._last_id = state.next_entity_id - 1
    update = HumanoidReproductionService.process_reproduction(state, generator)
    (child,) = [e for e in update.entities_add if e.identity.life_stage == LifeStage.CHILD]
    assert update.entity_spawn_sources[child.id] == SpawnSource(SpawnKind.BIRTH, parent_ids=(1, 2))


def test_an_add_without_a_declared_source_is_unsourced():
    update = StateUpdate(entities_add=[V2EntityBuilder(9).build()])
    assert 9 not in update.entity_spawn_sources
