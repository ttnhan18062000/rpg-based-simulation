"""D67/D70 (divergence 2.122): a region never adds a monster to reach a density target. The retired `SpawnService.process_spawns` topped each region up to
area x density x (1 + hazard) with parentless, costless bodies; it was dead under every corpus world (no region kind matched its pools) and is removed so
it cannot wake. A run adds no region-sourced entity: a region of the old pool kinds, empty of monsters, stays empty."""
from dataclasses import replace

import pytest

from src.core.state import AuthoritativeState, RegionState
from src.engine.cadence import SystemCadence
from src.engine.world_dynamics import WorldDynamicsSystem
from src.systems.world_systems.generator import EntityGenerator
from src.core.updates import StateUpdate


def _state(kind: str, tick: int) -> AuthoritativeState:
    region = RegionState(id="r", name="R", bounds=(0, 0, 200, 200), kind=kind, hazard_level=2.0)
    return AuthoritativeState(tick=tick, seed=7, regions={"r": region}, terrain={(x, y): "plain" for x in range(0, 200, 10) for y in range(0, 200, 10)})


@pytest.mark.parametrize("kind", ["FOREST", "PLAINS", "MOUNTAIN", "WILDERNESS", "TOWN"])
@pytest.mark.parametrize("tick", [0, 50, 600])
def test_a_region_with_no_monsters_adds_none_at_a_spawn_interval(kind, tick):
    state = _state(kind, tick)
    generator = EntityGenerator(state.seed)
    generator._last_id = state.next_entity_id - 1
    cadence = SystemCadence(world_dynamics=1)
    update = WorldDynamicsSystem.resolve_dynamics(state, StateUpdate(), generator, cadence)
    assert not update.entities_add, f"{kind} at tick {tick}: world dynamics added {[(e.id, e.kind) for e in update.entities_add]} with no source"


def test_the_density_top_up_service_is_gone():
    import importlib

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("src.world.spawn")
    import src.world.spawn_config as config

    assert not hasattr(config, "SPAWN_POOLS") and not hasattr(config, "BASE_MONSTER_DENSITY")
    assert hasattr(config, "DIFFICULTY_TIERS") and hasattr(config, "DIFFICULTY_ZONES")  # what the generator and the region code still read
