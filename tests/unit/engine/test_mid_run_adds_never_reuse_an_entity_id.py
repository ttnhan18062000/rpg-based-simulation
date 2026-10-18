"""An add never reuses an existing entity id (TCK-20261014-A-CONQUEST-STRONGHOLD-OVERWRITES-ENTITY-1).

A monster conquest's stronghold (removed by D71, TCK-20261014-A-CONQUEST-NO-LONGER-SPAWNS-A-STRONGHOLD-BODY-D71) came from a generator whose id counter started at 0, so it took id 1 and silently replaced entity 1, and
`next_entity_id` was never advanced for it. Every mid-run generator now comes from one factory (`EntityGenerator.for_state`), the apply refuses a
duplicate-id add with `DuplicateEntityIdError`, and every add advances `next_entity_id`.
"""
from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

import pytest

from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath, DuplicateEntityIdError
from src.systems.world_systems.generator import EntityGenerator
from tests.helpers.scenario import compile_world


def _world():
    return compile_world("frontier_living_world", 42)


def _monster_add(state, update=None):
    """The production sequence of a mid-run spawn: the factory generator, then a spawn."""
    generator = EntityGenerator.for_state(state, update)
    return StateUpdate(entities_add=[generator.spawn_monster((5.0, 5.0), state)])


def test_a_mid_run_spawn_gets_a_fresh_id_and_entity_one_survives():
    state = _world()
    assert 1 in state.entities and state.next_entity_id > 1
    added = _monster_add(state).entities_add
    assert len(added) == 1
    assert added[0].id not in state.entities and added[0].id == state.next_entity_id
    new_state = ApplyPath.apply_generation(state, StateUpdate(entities_add=added))
    assert new_state.entities[1].identity == state.entities[1].identity and new_state.entities[1].kind == state.entities[1].kind  # entity 1 is still entity 1
    assert new_state.entities[added[0].id].id == added[0].id


def test_every_add_advances_next_entity_id():
    state = _world()
    added = _monster_add(state).entities_add
    new_state = ApplyPath.apply_generation(state, StateUpdate(entities_add=added))
    assert new_state.next_entity_id == added[0].id + 1 > state.next_entity_id


def test_a_duplicate_id_add_is_refused_loudly():
    state = _world()
    clone = replace(state.entities[1])
    with pytest.raises(DuplicateEntityIdError):
        ApplyPath.apply_generation(state, StateUpdate(entities_add=[clone]))


def test_two_adds_in_one_update_with_the_same_id_are_refused():
    state = _world()
    added = _monster_add(state).entities_add
    with pytest.raises(DuplicateEntityIdError):
        ApplyPath.apply_generation(state, StateUpdate(entities_add=added + added))


def test_a_generator_built_after_an_earlier_add_in_the_same_tick_takes_the_next_id():
    state = _world()
    first = _monster_add(state)
    second = _monster_add(state, update=first)
    ids = [e.id for e in first.entities_add] + [e.id for e in second.entities_add]
    assert len(ids) == len(set(ids)) == 2


def test_the_factory_is_deterministic():
    state = _world()
    a = _monster_add(state).entities_add[0]
    b = _monster_add(state).entities_add[0]
    assert a.id == b.id and a.navigation.position == b.navigation.position


def test_no_mid_run_site_builds_a_generator_by_hand():
    """The id base cannot be forgotten at a site that does not construct the generator: only the factory and the engine's own start-up sites do."""
    root = Path(__file__).resolve().parents[3] / "src"
    allowed = {"api/engine_manager.py", "certification/scenarios.py", "systems/world_systems/generator.py"}
    offenders = [str(p.relative_to(root)) for p in root.rglob("*.py")
                 if str(p.relative_to(root)) not in allowed and re.search(r"\bEntityGenerator\(", p.read_text())]
    assert offenders == []
