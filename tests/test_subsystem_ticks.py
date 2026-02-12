"""Tests for subsystem tick rates (design-02).

Covers:
- Subsystems always run even when no entities are ready (empty tick fix)
- Configurable rate divisors control subsystem frequency
- Core/environment/economy groups fire at expected intervals
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch, call
from src.config import SimulationConfig
from src.core.models import Entity, Stats, Vector2
from src.core.faction import Faction
from src.core.enums import AIState
from src.core.world_state import WorldState
from src.core.grid import Grid
from src.systems.spatial_hash import SpatialHash
from src.engine.world_loop import WorldLoop
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.systems.generator import EntityGenerator


def _make_config(**overrides) -> SimulationConfig:
    defaults = dict(
        max_ticks=100,
        initial_entity_count=0,
        generator_max_entities=0,
        num_camps=0,
        subsystem_rate_core=1,
        subsystem_rate_environment=2,
        subsystem_rate_economy=5,
    )
    defaults.update(overrides)
    return SimulationConfig(**defaults)


def _make_world(config: SimulationConfig) -> WorldState:
    grid = Grid(32, 32)
    spatial = SpatialHash(config.spatial_cell_size)
    return WorldState(seed=42, grid=grid, spatial_index=spatial)


def _make_loop(config=None, world=None) -> WorldLoop:
    from src.ai.brain import AIBrain
    from src.systems.rng import DeterministicRNG
    config = config or _make_config()
    world = world or _make_world(config)
    rng = DeterministicRNG(seed=42)
    brain = AIBrain(config, rng)
    pool = WorkerPool(config, brain)
    resolver = ConflictResolver(config, rng)
    gen = EntityGenerator(config, rng)
    loop = WorldLoop(config, world, pool, resolver, gen, rng=rng)
    return loop


class TestSubsystemsAlwaysRun:
    """Subsystems must tick even when no entities are ready (empty tick bug fix)."""

    def test_effects_tick_on_empty_tick(self):
        """Status effects should decay even when no entities act."""
        loop = _make_loop()
        stats = Stats(hp=50, max_hp=100, atk=10, def_=5, spd=5)
        entity = Entity(id=1, kind="hero", pos=Vector2(5, 5), stats=stats,
                        faction=Faction.HERO_GUILD)
        entity.next_act_at = 999.0  # Won't be ready for a long time
        from src.core.effects import StatusEffect, EffectType
        entity.effects.append(StatusEffect(
            effect_type=EffectType.SKILL_BUFF, remaining_ticks=3, source="test",
        ))
        loop.world.add_entity(entity)

        # Run a tick — entity is NOT ready, but effects should still tick
        loop.tick_once()
        ent = loop.world.entities[1]
        assert len(ent.effects) > 0
        assert ent.effects[0].remaining_ticks == 2

    def test_stamina_regens_on_empty_tick(self):
        """Stamina should regen even when no entities are ready to act."""
        loop = _make_loop()
        stats = Stats(hp=100, max_hp=100, atk=10, def_=5, spd=5, stamina=50, max_stamina=100)
        entity = Entity(id=1, kind="hero", pos=Vector2(5, 5), stats=stats,
                        faction=Faction.HERO_GUILD)
        entity.ai_state = AIState.WANDER
        entity.next_act_at = 999.0
        loop.world.add_entity(entity)

        old_stamina = entity.stats.stamina
        loop.tick_once()
        assert loop.world.entities[1].stats.stamina > old_stamina

    def test_skill_cooldowns_tick_on_empty_tick(self):
        """Skill cooldowns should count down even on empty ticks."""
        loop = _make_loop()
        stats = Stats(hp=100, max_hp=100, atk=10, def_=5, spd=5)
        entity = Entity(id=1, kind="hero", pos=Vector2(5, 5), stats=stats,
                        faction=Faction.HERO_GUILD)
        entity.next_act_at = 999.0
        from src.core.classes import SkillInstance
        skill = SkillInstance(skill_id="power_strike", cooldown_remaining=5)
        entity.skills.append(skill)
        loop.world.add_entity(entity)

        loop.tick_once()
        assert loop.world.entities[1].skills[0].cooldown_remaining == 4


class TestSubsystemRateDivisors:
    """Configurable rate divisors control subsystem frequency."""

    def test_core_runs_every_tick(self):
        config = _make_config(subsystem_rate_core=1)
        loop = _make_loop(config=config)

        with patch.object(WorldLoop, '_phase_cleanup', return_value=None) as mock_cleanup:
            loop._tick_subsystems(0)
            loop._tick_subsystems(1)
            loop._tick_subsystems(2)
            assert mock_cleanup.call_count == 3

    def test_environment_runs_every_2nd_tick(self):
        config = _make_config(subsystem_rate_environment=2)
        loop = _make_loop(config=config)

        with patch.object(WorldLoop, '_process_territory_effects', return_value=None) as mock_terr:
            for t in range(10):
                loop._tick_subsystems(t)
            assert mock_terr.call_count == 5

    def test_economy_runs_every_5th_tick(self):
        config = _make_config(subsystem_rate_economy=5)
        loop = _make_loop(config=config)

        with patch.object(WorldLoop, '_tick_resource_nodes', return_value=None) as mock_res:
            for t in range(20):
                loop._tick_subsystems(t)
            assert mock_res.call_count == 4

    def test_all_subsystems_run_on_tick_0(self):
        """All groups should fire on tick 0 regardless of rate."""
        config = _make_config(
            subsystem_rate_core=3,
            subsystem_rate_environment=7,
            subsystem_rate_economy=13,
        )
        loop = _make_loop(config=config)

        with patch.object(WorldLoop, '_phase_cleanup', return_value=None) as m1, \
             patch.object(WorldLoop, '_process_territory_effects', return_value=None) as m2, \
             patch.object(WorldLoop, '_tick_resource_nodes', return_value=None) as m3:
            loop._tick_subsystems(0)
            assert m1.call_count == 1
            assert m2.call_count == 1
            assert m3.call_count == 1

    def test_rate_1_means_every_tick_for_all(self):
        """Setting all rates to 1 means everything runs every tick."""
        config = _make_config(
            subsystem_rate_core=1,
            subsystem_rate_environment=1,
            subsystem_rate_economy=1,
        )
        loop = _make_loop(config=config)

        with patch.object(WorldLoop, '_phase_cleanup', return_value=None) as m1, \
             patch.object(WorldLoop, '_process_territory_effects', return_value=None) as m2, \
             patch.object(WorldLoop, '_tick_resource_nodes', return_value=None) as m3:
            for t in range(5):
                loop._tick_subsystems(t)
            assert m1.call_count == 5
            assert m2.call_count == 5
            assert m3.call_count == 5


class TestConfigDefaults:
    """Config defaults for subsystem rates are reasonable."""

    def test_default_core_rate_is_1(self):
        cfg = SimulationConfig()
        assert cfg.subsystem_rate_core == 1

    def test_default_environment_rate_is_2(self):
        cfg = SimulationConfig()
        assert cfg.subsystem_rate_environment == 2

    def test_default_economy_rate_is_5(self):
        cfg = SimulationConfig()
        assert cfg.subsystem_rate_economy == 5
