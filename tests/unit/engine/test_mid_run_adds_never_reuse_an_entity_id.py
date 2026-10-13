"""An add never reuses an existing entity id (TCK-20261014-A-CONQUEST-STRONGHOLD-OVERWRITES-ENTITY-1).

A monster conquest's stronghold came from a generator whose id counter started at 0, so it took id 1 and silently replaced entity 1, and
`next_entity_id` was never advanced for it. Every mid-run generator now comes from one factory (`EntityGenerator.for_state`), the apply refuses a
duplicate-id add with `DuplicateEntityIdError`, and every add advances `next_entity_id`.
"""
from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

import pytest

from src.core.enums import Faction
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate, WorldUpdate
from src.engine.apply import ApplyPath, DuplicateEntityIdError
from src.systems.lifecycle_systems.lifecycle import LifecycleSystem  # noqa: F401  (the conquest call site)
from src.systems.world_systems.generator import EntityGenerator
from src.world.influence import FactionInfluenceService
from tests.helpers.scenario import compile_world


def _world():
    state = compile_world("frontier_living_world", 42)
    region_id = next(iter(state.regions))
    return state, region_id


def _conquest_update(region_id):
    return StateUpdate(world_updates={region_id: WorldUpdate(region_id=region_id, owner_faction_id_set=Faction.MONSTER_HORDE)})


def _stronghold_add(state, region_id, update=None):
    """The production sequence of the lifecycle call site: the factory generator, then the conquest lifecycle."""
    generator = EntityGenerator.for_state(state, update)
    return FactionInfluenceService.process_conquest_lifecycle(state, _conquest_update(region_id), generator)


def test_the_conquest_stronghold_gets_a_fresh_id_and_entity_one_survives():
    state, region_id = _world()
    assert 1 in state.entities and state.next_entity_id > 1
    added = _stronghold_add(state, region_id).entities_add
    assert len(added) == 1 and added[0].kind == "stronghold"
    assert added[0].id not in state.entities and added[0].id == state.next_entity_id
    new_state = ApplyPath.apply_generation(state, StateUpdate(entities_add=added))
    assert new_state.entities[1].identity == state.entities[1].identity and new_state.entities[1].kind == state.entities[1].kind != "stronghold"  # entity 1 is still entity 1
    assert new_state.entities[added[0].id].kind == "stronghold"


def test_every_add_advances_next_entity_id():
    state, region_id = _world()
    added = _stronghold_add(state, region_id).entities_add
    new_state = ApplyPath.apply_generation(state, StateUpdate(entities_add=added))
    assert new_state.next_entity_id == added[0].id + 1 > state.next_entity_id


def test_a_duplicate_id_add_is_refused_loudly():
    state, _ = _world()
    clone = replace(state.entities[1])
    with pytest.raises(DuplicateEntityIdError):
        ApplyPath.apply_generation(state, StateUpdate(entities_add=[clone]))


def test_two_adds_in_one_update_with_the_same_id_are_refused():
    state, region_id = _world()
    added = _stronghold_add(state, region_id).entities_add
    with pytest.raises(DuplicateEntityIdError):
        ApplyPath.apply_generation(state, StateUpdate(entities_add=added + added))


def test_a_generator_built_after_an_earlier_add_in_the_same_tick_takes_the_next_id():
    state, region_id = _world()
    first = _stronghold_add(state, region_id)
    second = _stronghold_add(state, region_id, update=first)
    ids = [e.id for e in first.entities_add] + [e.id for e in second.entities_add]
    assert len(ids) == len(set(ids)) == 2


def test_the_factory_is_deterministic():
    state, region_id = _world()
    a = _stronghold_add(state, region_id).entities_add[0]
    b = _stronghold_add(state, region_id).entities_add[0]
    assert a.id == b.id and a.navigation.position == b.navigation.position


def test_no_mid_run_site_builds_a_generator_by_hand():
    """The id base cannot be forgotten at a site that does not construct the generator: only the factory and the engine's own start-up sites do."""
    root = Path(__file__).resolve().parents[3] / "src"
    allowed = {"api/engine_manager.py", "certification/scenarios.py", "systems/world_systems/generator.py"}
    offenders = [str(p.relative_to(root)) for p in root.rglob("*.py")
                 if str(p.relative_to(root)) not in allowed and re.search(r"\bEntityGenerator\(", p.read_text())]
    assert offenders == []
